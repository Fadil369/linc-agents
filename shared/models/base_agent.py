"""
Base agent class for LINC architecture
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Any
import asyncio
import httpx
import logging
import os
from datetime import datetime, timedelta
import uuid

from shared.database import get_db, DatabaseManager
from shared.database.models import Agent, InterAgentMessage, SystemEvent
from shared.auth import verify_token, get_current_user
from shared.messaging import MessageBroker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthResponse(BaseModel):
    status: str
    agent: str
    version: str
    uptime: float
    dependencies: List[str]
    timestamp: datetime

class AgentMessage(BaseModel):
    to_agent: str
    message_type: str
    payload: Dict[str, Any]
    priority: str = "normal"
    correlation_id: Optional[str] = None

class BaseLINCAgent:
    """Base class for all LINC agents"""
    
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        port: int = 8000,
        dependencies: List[str] = None
    ):
        self.name = name
        self.version = version
        self.description = description
        self.port = port
        self.dependencies = dependencies or []
        self.start_time = datetime.now()
        self.app = FastAPI(
            title=f"BrainSAIT {name.upper()}",
            description=description,
            version=version
        )
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure properly in production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize message broker
        self.message_broker = MessageBroker()
        
        # Setup base routes
        self._setup_base_routes()
        
        # Initialize database on startup
        self.app.add_event_handler("startup", self._startup_event)
        self.app.add_event_handler("shutdown", self._shutdown_event)
    
    def _setup_base_routes(self):
        """Setup standard routes for all agents"""
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint"""
            uptime = (datetime.now() - self.start_time).total_seconds()
            return HealthResponse(
                status="healthy",
                agent=self.name,
                version=self.version,
                uptime=uptime,
                dependencies=self.dependencies,
                timestamp=datetime.now()
            )
        
        @self.app.get("/")
        async def root():
            """Root endpoint"""
            return {
                "agent": self.name,
                "version": self.version,
                "description": self.description,
                "status": "online",
                "timestamp": datetime.now()
            }
        
        @self.app.post("/messages/send")
        async def send_message(
            message: AgentMessage,
            background_tasks: BackgroundTasks,
            db: Session = Depends(get_db)
        ):
            """Send message to another agent"""
            try:
                # Create inter-agent message record
                inter_msg = InterAgentMessage(
                    from_agent=self.name,
                    to_agent=message.to_agent,
                    message_type=message.message_type,
                    payload=message.payload,
                    priority=message.priority,
                    correlation_id=message.correlation_id or str(uuid.uuid4())
                )
                db.add(inter_msg)
                db.commit()
                
                # Send message asynchronously
                background_tasks.add_task(
                    self._send_agent_message,
                    message.to_agent,
                    message.message_type,
                    message.payload,
                    message.correlation_id
                )
                
                return {"status": "sent", "correlation_id": inter_msg.correlation_id}
                
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/messages/receive")
        async def receive_message(
            from_agent: str,
            message_type: str,
            payload: Dict[str, Any],
            correlation_id: Optional[str] = None,
            db: Session = Depends(get_db)
        ):
            """Receive message from another agent"""
            try:
                # Log the received message
                event = SystemEvent(
                    event_type=f"message.received",
                    agent_name=self.name,
                    description=f"Received {message_type} from {from_agent}",
                    metadata={
                        "from_agent": from_agent,
                        "message_type": message_type,
                        "correlation_id": correlation_id
                    }
                )
                db.add(event)
                db.commit()
                
                # Process message
                response = await self._handle_agent_message(
                    from_agent, message_type, payload, correlation_id
                )
                
                return {"status": "received", "response": response}
                
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _startup_event(self):
        """Agent startup event"""
        try:
            # Initialize database
            DatabaseManager.init_database()
            
            # Register/update agent in database
            await self._register_agent()
            
            # Connect to message broker
            await self.message_broker.connect()
            
            # Start heartbeat
            asyncio.create_task(self._heartbeat_loop())
            
            logger.info(f"{self.name} agent started successfully")
            
        except Exception as e:
            logger.error(f"Startup error: {e}")
            raise
    
    async def _shutdown_event(self):
        """Agent shutdown event"""
        try:
            # Update agent status to offline
            await self._update_agent_status("offline")
            
            # Disconnect from message broker
            await self.message_broker.disconnect()
            
            logger.info(f"{self.name} agent shutdown complete")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
    
    async def _register_agent(self):
        """Register agent in the database"""
        try:
            from shared.database import get_db_session
            from shared.database.models import Agent
            
            with get_db_session() as db:
                agent = db.query(Agent).filter(Agent.name == self.name).first()
                if agent:
                    # Update existing agent
                    agent.status = "online"
                    agent.version = self.version
                    agent.description = self.description
                    agent.port = self.port
                    agent.last_heartbeat = datetime.now()
                    agent.health_check_url = f"http://localhost:{self.port}/health"
                else:
                    # Create new agent
                    agent = Agent(
                        name=self.name,
                        type="custom",  # Override in subclasses
                        status="online",
                        version=self.version,
                        port=self.port,
                        description=self.description,
                        health_check_url=f"http://localhost:{self.port}/health"
                    )
                    db.add(agent)
                
                db.commit()
                
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
    
    async def _update_agent_status(self, status: str):
        """Update agent status in database"""
        try:
            from shared.database import get_db_session
            from shared.database.models import Agent
            
            with get_db_session() as db:
                agent = db.query(Agent).filter(Agent.name == self.name).first()
                if agent:
                    agent.status = status
                    agent.last_heartbeat = datetime.now()
                    db.commit()
                    
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat to maintain agent status"""
        while True:
            try:
                await self._update_agent_status("online")
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(30)
    
    async def _send_agent_message(
        self,
        to_agent: str,
        message_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Send message to another agent via HTTP"""
        try:
            # Get target agent info from database
            from shared.database import get_db_session
            from shared.database.models import Agent
            
            with get_db_session() as db:
                target_agent = db.query(Agent).filter(Agent.name == to_agent).first()
                if not target_agent:
                    raise Exception(f"Agent {to_agent} not found")
                
                if target_agent.status != "online":
                    raise Exception(f"Agent {to_agent} is not online")
                
                # Send HTTP request to target agent
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"http://localhost:{target_agent.port}/messages/receive",
                        json={
                            "from_agent": self.name,
                            "message_type": message_type,
                            "payload": payload,
                            "correlation_id": correlation_id
                        },
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Message sent successfully to {to_agent}")
                        return response.json()
                    else:
                        raise Exception(f"HTTP {response.status_code}: {response.text}")
                        
        except Exception as e:
            logger.error(f"Error sending message to {to_agent}: {e}")
            # Update message status to failed
            from shared.database import get_db_session
            from shared.database.models import InterAgentMessage
            
            with get_db_session() as db:
                if correlation_id:
                    msg = db.query(InterAgentMessage).filter(
                        InterAgentMessage.correlation_id == correlation_id
                    ).first()
                    if msg:
                        msg.status = "failed"
                        db.commit()
    
    async def _handle_agent_message(
        self,
        from_agent: str,
        message_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle incoming message from another agent - override in subclasses"""
        logger.info(f"Received {message_type} from {from_agent}")
        
        # Default response
        return {
            "status": "acknowledged",
            "agent": self.name,
            "timestamp": datetime.now().isoformat()
        }
    
    def add_routes(self, routes_func):
        """Add custom routes to the agent"""
        routes_func(self.app)
    
    def run(self, host: str = "0.0.0.0", reload: bool = False):
        """Run the agent"""
        import uvicorn
        uvicorn.run(
            self.app,
            host=host,
            port=self.port,
            reload=reload,
            log_level="info"
        )