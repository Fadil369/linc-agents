"""
Message broker for inter-agent communication
"""

import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

class MessageBroker:
    """Redis-based message broker for agent communication"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub = None
        self.subscribers: Dict[str, Callable] = {}
        self.is_connected = False
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            self.is_connected = True
            logger.info("Connected to Redis message broker")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
            if self.redis_client:
                await self.redis_client.close()
            self.is_connected = False
            logger.info("Disconnected from Redis message broker")
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")
    
    async def publish(self, channel: str, message: Dict[str, Any]):
        """Publish message to a channel"""
        if not self.is_connected:
            logger.warning("Not connected to Redis, attempting to reconnect...")
            await self.connect()
        
        try:
            message_with_timestamp = {
                **message,
                "timestamp": datetime.now().isoformat(),
                "broker_id": id(self)
            }
            
            await self.redis_client.publish(
                channel,
                json.dumps(message_with_timestamp)
            )
            logger.debug(f"Published message to {channel}")
            
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
    
    async def subscribe(self, channel: str, handler: Callable):
        """Subscribe to a channel with a message handler"""
        if not self.is_connected:
            await self.connect()
        
        try:
            await self.pubsub.subscribe(channel)
            self.subscribers[channel] = handler
            logger.info(f"Subscribed to channel: {channel}")
            
            # Start listening for messages
            asyncio.create_task(self._listen_for_messages())
            
        except Exception as e:
            logger.error(f"Error subscribing to {channel}: {e}")
    
    async def unsubscribe(self, channel: str):
        """Unsubscribe from a channel"""
        try:
            await self.pubsub.unsubscribe(channel)
            if channel in self.subscribers:
                del self.subscribers[channel]
            logger.info(f"Unsubscribed from channel: {channel}")
            
        except Exception as e:
            logger.error(f"Error unsubscribing from {channel}: {e}")
    
    async def _listen_for_messages(self):
        """Listen for incoming messages"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode()
                    data = json.loads(message["data"].decode())
                    
                    # Call the appropriate handler
                    if channel in self.subscribers:
                        try:
                            await self.subscribers[channel](data)
                        except Exception as e:
                            logger.error(f"Error handling message in {channel}: {e}")
                            
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")
    
    async def set_cache(self, key: str, value: Any, expire_seconds: int = 3600):
        """Set cached value"""
        if not self.is_connected:
            await self.connect()
        
        try:
            await self.redis_client.setex(
                key,
                expire_seconds,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Error setting cache {key}: {e}")
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if not self.is_connected:
            await self.connect()
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache {key}: {e}")
            return None
    
    async def delete_cache(self, key: str):
        """Delete cached value"""
        if not self.is_connected:
            await self.connect()
        
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting cache {key}: {e}")

# Agent communication channels
AGENT_CHANNELS = {
    "system": "linc:system",
    "healthcare": "linc:healthcare", 
    "business": "linc:business",
    "development": "linc:development",
    "content": "linc:content",
    "orchestration": "linc:orchestration"
}

class AgentMessenger:
    """High-level messaging interface for agents"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.broker = MessageBroker()
    
    async def connect(self):
        """Connect to message broker"""
        await self.broker.connect()
        
        # Subscribe to agent-specific channel
        agent_channel = f"linc:agent:{self.agent_name}"
        await self.broker.subscribe(agent_channel, self._handle_direct_message)
        
        # Subscribe to relevant type channels based on agent type
        await self._subscribe_to_type_channels()
    
    async def _subscribe_to_type_channels(self):
        """Subscribe to channels based on agent type"""
        # All agents subscribe to system channel
        await self.broker.subscribe(
            AGENT_CHANNELS["system"],
            self._handle_system_message
        )
        
        # Subscribe to orchestration for coordination
        await self.broker.subscribe(
            AGENT_CHANNELS["orchestration"],
            self._handle_orchestration_message
        )
    
    async def send_to_agent(self, target_agent: str, message_type: str, payload: Dict[str, Any]):
        """Send message directly to another agent"""
        message = {
            "from_agent": self.agent_name,
            "to_agent": target_agent,
            "message_type": message_type,
            "payload": payload
        }
        
        await self.broker.publish(f"linc:agent:{target_agent}", message)
    
    async def broadcast_to_type(self, agent_type: str, message_type: str, payload: Dict[str, Any]):
        """Broadcast message to all agents of a certain type"""
        if agent_type in AGENT_CHANNELS:
            message = {
                "from_agent": self.agent_name,
                "message_type": message_type,
                "payload": payload,
                "broadcast": True
            }
            
            await self.broker.publish(AGENT_CHANNELS[agent_type], message)
    
    async def send_system_alert(self, alert_level: str, message: str, metadata: Dict[str, Any] = None):
        """Send system-wide alert"""
        alert = {
            "from_agent": self.agent_name,
            "alert_level": alert_level,  # info, warning, error, critical
            "message": message,
            "metadata": metadata or {}
        }
        
        await self.broker.publish(AGENT_CHANNELS["system"], alert)
    
    async def _handle_direct_message(self, message: Dict[str, Any]):
        """Handle direct message to this agent"""
        logger.info(f"Received direct message: {message['message_type']} from {message['from_agent']}")
        # Override in agent implementation
    
    async def _handle_system_message(self, message: Dict[str, Any]):
        """Handle system-wide message"""
        logger.info(f"Received system message: {message}")
        # Override in agent implementation
    
    async def _handle_orchestration_message(self, message: Dict[str, Any]):
        """Handle orchestration message"""
        logger.info(f"Received orchestration message: {message}")
        # Override in agent implementation
    
    async def disconnect(self):
        """Disconnect from message broker"""
        await self.broker.disconnect()