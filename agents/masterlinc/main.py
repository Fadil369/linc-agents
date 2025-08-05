"""
MasterLINC - Central Orchestration Hub
Coordinates all LINC agents, manages workflows, and provides unified routing
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import asyncio
import httpx
import logging
from datetime import datetime, timedelta

from shared.models.base_agent import BaseLINCAgent
from shared.database import get_db
from shared.database.models import Agent, Conversation, User, InterAgentMessage
from shared.auth import get_current_user, permission_required
from shared.messaging import AgentMessenger, AGENT_CHANNELS

logger = logging.getLogger(__name__)

class WorkflowRequest(BaseModel):
    user_intent: str
    context: Dict[str, Any] = {}
    preferred_language: str = "en"
    priority: str = "normal"

class AgentRoute(BaseModel):
    agent_name: str
    confidence: float
    reasoning: str

class WorkflowResponse(BaseModel):
    workflow_id: str
    primary_agent: str
    supporting_agents: List[str]
    estimated_duration: int  # minutes
    steps: List[Dict[str, Any]]

class MasterLINC(BaseLINCAgent):
    """Central orchestration hub for all LINC agents"""
    
    def __init__(self):
        super().__init__(
            name="masterlinc",
            version="1.0.0",
            description="Central orchestration hub governing all LINC agents",
            port=8000,
            dependencies=[]
        )
        
        self.messenger = AgentMessenger("masterlinc")
        self.agent_registry: Dict[str, Dict] = {}
        self.active_workflows: Dict[str, Dict] = {}
        
        # Setup custom routes
        self.add_routes(self._setup_routes)
    
    def _setup_routes(self, app: FastAPI):
        """Setup MasterLINC specific routes"""
        
        @app.get("/agents", response_model=List[Dict])
        async def list_agents(db: Session = Depends(get_db)):
            """List all registered agents and their status"""
            agents = db.query(Agent).all()
            return [
                {
                    "name": agent.name,
                    "type": agent.type,
                    "status": agent.status,
                    "version": agent.version,
                    "subdomain": agent.subdomain,
                    "port": agent.port,
                    "capabilities": agent.capabilities,
                    "last_heartbeat": agent.last_heartbeat
                }
                for agent in agents
            ]
        
        @app.post("/workflow/route", response_model=WorkflowResponse)
        async def route_workflow(
            request: WorkflowRequest,
            background_tasks: BackgroundTasks,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user)
        ):
            """Route user request to appropriate agent workflow"""
            try:
                # Analyze user intent and route to appropriate agents
                routing_result = await self._analyze_and_route(request, current_user, db)
                
                # Create workflow in background
                background_tasks.add_task(
                    self._execute_workflow,
                    routing_result["workflow_id"],
                    routing_result,
                    current_user.id,
                    db
                )
                
                return WorkflowResponse(**routing_result)
                
            except Exception as e:
                logger.error(f"Error routing workflow: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/workflow/{workflow_id}")
        async def get_workflow_status(
            workflow_id: str,
            current_user: User = Depends(get_current_user)
        ):
            """Get workflow execution status"""
            if workflow_id in self.active_workflows:
                return self.active_workflows[workflow_id]
            else:
                raise HTTPException(status_code=404, detail="Workflow not found")
        
        @app.post("/agents/{agent_name}/health-check")
        async def health_check_agent(
            agent_name: str,
            db: Session = Depends(get_db)
        ):
            """Perform health check on specific agent"""
            agent = db.query(Agent).filter(Agent.name == agent_name).first()
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            health_status = await self._check_agent_health(agent)
            return health_status
        
        @app.get("/system/metrics")
        async def get_system_metrics(
            current_user: User = Depends(permission_required("system_config"))
        ):
            """Get system-wide metrics and statistics"""
            metrics = await self._collect_system_metrics()
            return metrics
        
        @app.post("/system/broadcast")
        async def broadcast_message(
            message_type: str,
            payload: Dict[str, Any],
            target_type: str = "system",
            current_user: User = Depends(permission_required("manage_agents"))
        ):
            """Broadcast message to all agents of specified type"""
            await self.messenger.broadcast_to_type(target_type, message_type, payload)
            return {"status": "broadcast_sent", "target_type": target_type}
    
    async def _analyze_and_route(
        self, 
        request: WorkflowRequest, 
        user: User, 
        db: Session
    ) -> Dict[str, Any]:
        """Analyze user intent and determine routing"""
        
        # Simple intent analysis (can be enhanced with AI/ML)
        intent_keywords = {
            "doctorlinc": [
                "doctor", "physician", "medical", "diagnosis", "prescription", 
                "symptom", "treatment", "clinic", "consultation", "health"
            ],
            "nurslinc": [
                "nurse", "nursing", "care", "medication", "vital signs",
                "shift", "report", "patient care", "checklist"
            ],
            "patientlinc": [
                "patient", "appointment", "schedule", "education", "health tracking",
                "lab results", "medication reminder", "symptoms"
            ],
            "bizlinc": [
                "business", "entrepreneur", "startup", "proposal", "rfp",
                "market analysis", "etimad", "saudi business"
            ],
            "paylinc": [
                "payment", "billing", "invoice", "financial", "subscription",
                "stripe", "paypal", "transaction"
            ],
            "chatlinc": [
                "chat", "talk", "conversation", "help", "support",
                "question", "information"
            ]
        }
        
        user_intent_lower = request.user_intent.lower()
        agent_scores = {}
        
        # Score agents based on keyword matching
        for agent_name, keywords in intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in user_intent_lower)
            if score > 0:
                agent_scores[agent_name] = score / len(keywords)
        
        # Default to chatlinc if no clear match
        if not agent_scores:
            agent_scores["chatlinc"] = 0.8
        
        # Get the highest scoring agent
        primary_agent = max(agent_scores.keys(), key=lambda x: agent_scores[x])
        
        # Determine supporting agents based on primary agent
        supporting_agents = self._get_supporting_agents(primary_agent, request.context)
        
        # Generate workflow ID
        import uuid
        workflow_id = str(uuid.uuid4())
        
        # Create workflow steps
        steps = [
            {
                "step": 1,
                "agent": primary_agent,
                "action": "process_request",
                "status": "pending"
            }
        ]
        
        # Add supporting agent steps if needed
        for i, agent in enumerate(supporting_agents):
            steps.append({
                "step": i + 2,
                "agent": agent,
                "action": "support_processing",
                "status": "waiting"
            })
        
        return {
            "workflow_id": workflow_id,
            "primary_agent": primary_agent,
            "supporting_agents": supporting_agents,
            "estimated_duration": 5,  # Default 5 minutes
            "steps": steps
        }
    
    def _get_supporting_agents(self, primary_agent: str, context: Dict) -> List[str]:
        """Determine supporting agents based on primary agent and context"""
        support_map = {
            "doctorlinc": ["nurslinc", "patientlinc"],
            "nurslinc": ["doctorlinc"],
            "patientlinc": ["doctorlinc", "nurslinc"],
            "bizlinc": ["paylinc", "insightlinc"],
            "paylinc": ["bizlinc"],
            "chatlinc": []  # Can route to any agent based on conversation
        }
        
        return support_map.get(primary_agent, [])
    
    async def _execute_workflow(
        self,
        workflow_id: str,
        workflow_data: Dict,
        user_id: int,
        db: Session
    ):
        """Execute workflow by coordinating agents"""
        try:
            # Store workflow
            self.active_workflows[workflow_id] = {
                **workflow_data,
                "status": "executing",
                "user_id": user_id,
                "started_at": datetime.now()
            }
            
            # Send initial request to primary agent
            primary_agent = workflow_data["primary_agent"]
            
            message_payload = {
                "workflow_id": workflow_id,
                "user_id": user_id,
                "request_type": "workflow_start",
                "context": workflow_data.get("context", {})
            }
            
            await self.messenger.send_to_agent(
                primary_agent,
                "workflow_request",
                message_payload
            )
            
            logger.info(f"Workflow {workflow_id} started with agent {primary_agent}")
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = "error"
                self.active_workflows[workflow_id]["error"] = str(e)
    
    async def _check_agent_health(self, agent: Agent) -> Dict[str, Any]:
        """Check health of a specific agent"""
        try:
            if agent.health_check_url:
                async with httpx.AsyncClient() as client:
                    response = await client.get(agent.health_check_url, timeout=10.0)
                    
                    if response.status_code == 200:
                        health_data = response.json()
                        return {
                            "agent": agent.name,
                            "status": "healthy",
                            "response_time": response.elapsed.total_seconds(),
                            "details": health_data
                        }
                    else:
                        return {
                            "agent": agent.name,
                            "status": "unhealthy",
                            "error": f"HTTP {response.status_code}"
                        }
            else:
                return {
                    "agent": agent.name,
                    "status": "unknown",
                    "error": "No health check URL configured"
                }
                
        except Exception as e:
            return {
                "agent": agent.name,
                "status": "error",
                "error": str(e)
            }
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-wide metrics"""
        from shared.database import get_db_session
        from shared.database.models import SystemEvent
        
        with get_db_session() as db:
            # Agent status summary
            agents = db.query(Agent).all()
            agent_status = {}
            for agent in agents:
                status = agent.status
                agent_status[status] = agent_status.get(status, 0) + 1
            
            # Recent system events
            recent_events = db.query(SystemEvent).filter(
                SystemEvent.created_at > datetime.now() - timedelta(hours=24)
            ).count()
            
            # Active conversations
            active_conversations = db.query(Conversation).filter(
                Conversation.status == "active"
            ).count()
            
            return {
                "timestamp": datetime.now(),
                "agents": {
                    "total": len(agents),
                    "status_breakdown": agent_status
                },
                "activity": {
                    "recent_events_24h": recent_events,
                    "active_conversations": active_conversations,
                    "active_workflows": len(self.active_workflows)
                },
                "system": {
                    "uptime": (datetime.now() - self.start_time).total_seconds(),
                    "version": self.version
                }
            }
    
    async def _handle_agent_message(
        self,
        from_agent: str,
        message_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle incoming messages from other agents"""
        
        if message_type == "workflow_complete":
            workflow_id = payload.get("workflow_id")
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = "completed"
                self.active_workflows[workflow_id]["completed_at"] = datetime.now()
                logger.info(f"Workflow {workflow_id} completed by {from_agent}")
        
        elif message_type == "workflow_error":
            workflow_id = payload.get("workflow_id")
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = "error"
                self.active_workflows[workflow_id]["error"] = payload.get("error")
                logger.error(f"Workflow {workflow_id} failed: {payload.get('error')}")
        
        elif message_type == "agent_registration":
            # Handle dynamic agent registration
            await self._handle_agent_registration(from_agent, payload)
        
        return {"status": "acknowledged"}
    
    async def _handle_agent_registration(self, agent_name: str, agent_data: Dict):
        """Handle registration of new agents"""
        try:
            from shared.database import get_db_session
            
            with get_db_session() as db:
                agent = db.query(Agent).filter(Agent.name == agent_name).first()
                if agent:
                    # Update existing agent
                    for key, value in agent_data.items():
                        if hasattr(agent, key):
                            setattr(agent, key, value)
                else:
                    # Create new agent
                    agent = Agent(name=agent_name, **agent_data)
                    db.add(agent)
                
                db.commit()
                logger.info(f"Agent {agent_name} registered/updated")
                
        except Exception as e:
            logger.error(f"Error registering agent {agent_name}: {e}")

def create_app():
    """Create and configure the MasterLINC application"""
    return MasterLINC()

if __name__ == "__main__":
    app = create_app()
    app.run()