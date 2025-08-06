"""Orchestration service for routing requests to appropriate agents"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from enum import Enum

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from ..config.settings import get_settings
from .base import BaseService

logger = logging.getLogger(__name__)

class AgentType(str, Enum):
    """Available agent types"""
    DOCTOR = "doctor"
    NURSE = "nurse"
    PATIENT = "patient"
    CARETEAM = "careteam"
    BUSINESS = "business"
    PAYMENT = "payment"
    INSIGHT = "insight"
    DEVELOPMENT = "development"
    AUTOMATION = "automation"
    CODE = "code"
    MEDIA = "media"
    EDUCATION = "education"
    CHAT = "chat"
    OPENID = "openid"

class OrchestrationService(BaseService):
    """Service for orchestrating requests across LINC agents"""
    
    def __init__(self, db_session: AsyncSession, redis_client: Redis):
        super().__init__(db_session, redis_client)
        self.settings = get_settings()
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Agent URL mapping
        self.agent_urls = {
            AgentType.DOCTOR: self.settings.doctor_linc_url,
            AgentType.NURSE: self.settings.nurse_linc_url,
            AgentType.PATIENT: self.settings.patient_linc_url,
            AgentType.CARETEAM: self.settings.careteam_linc_url,
            AgentType.BUSINESS: self.settings.biz_linc_url,
            AgentType.PAYMENT: self.settings.pay_linc_url,
            AgentType.INSIGHT: self.settings.insight_linc_url,
            AgentType.DEVELOPMENT: self.settings.dev_linc_url,
            AgentType.AUTOMATION: self.settings.auto_linc_url,
            AgentType.CODE: self.settings.code_linc_url,
            AgentType.MEDIA: self.settings.media_linc_url,
            AgentType.EDUCATION: self.settings.edu_linc_url,
            AgentType.CHAT: self.settings.chat_linc_url,
            AgentType.OPENID: self.settings.oid_linc_url,
        }
    
    async def route_request(
        self, 
        agent_type: AgentType, 
        endpoint: str, 
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Route request to appropriate agent"""
        
        if agent_type not in self.agent_urls:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_url = self.agent_urls[agent_type]
        full_url = f"{agent_url}{endpoint}"
        
        try:
            # Check agent health first
            if not await self.check_agent_health(agent_type):
                raise Exception(f"Agent {agent_type} is not healthy")
            
            self.logger.info(f"Routing {method} request to {full_url}")
            
            # Make the request
            response = await self.http_client.request(
                method=method,
                url=full_url,
                json=data,
                headers=headers or {}
            )
            
            response.raise_for_status()
            
            # Log successful routing
            await self.log_routing_event(agent_type, endpoint, method, "success")
            
            return response.json()
            
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error routing to {agent_type}: {e}")
            await self.log_routing_event(agent_type, endpoint, method, "error", str(e))
            raise
        except Exception as e:
            self.logger.error(f"Error routing to {agent_type}: {e}")
            await self.log_routing_event(agent_type, endpoint, method, "error", str(e))
            raise
    
    async def check_agent_health(self, agent_type: AgentType) -> bool:
        """Check if agent is healthy"""
        try:
            # First check Redis cache for recent health status
            cache_key = f"agent_health:{agent_type}"
            cached_status = await self.redis.get(cache_key)
            
            if cached_status == b"healthy":
                return True
            
            # If not cached or unhealthy, check directly
            agent_url = self.agent_urls[agent_type]
            health_url = f"{agent_url}/health"
            
            response = await self.http_client.get(health_url, timeout=5.0)
            is_healthy = response.status_code == 200
            
            # Cache the result
            await self.redis.setex(
                cache_key, 
                self.settings.agent_registry_ttl,
                "healthy" if is_healthy else "unhealthy"
            )
            
            return is_healthy
            
        except Exception as e:
            self.logger.warning(f"Health check failed for {agent_type}: {e}")
            return False
    
    async def get_agent_registry(self) -> Dict[str, Any]:
        """Get current agent registry with health status"""
        registry = {}
        
        for agent_type in AgentType:
            is_healthy = await self.check_agent_health(agent_type)
            registry[agent_type.value] = {
                "url": self.agent_urls[agent_type],
                "status": "healthy" if is_healthy else "unhealthy",
                "last_checked": "now"  # In production, use actual timestamp
            }
        
        return registry
    
    async def determine_best_agent(self, request_context: Dict[str, Any]) -> AgentType:
        """Determine the best agent to handle a request based on context"""
        
        # Extract context clues
        user_role = request_context.get("user_role", "").lower()
        request_type = request_context.get("request_type", "").lower()
        domain = request_context.get("domain", "").lower()
        
        # Role-based routing
        if user_role in ["doctor", "physician", "clinician"]:
            return AgentType.DOCTOR
        elif user_role in ["nurse", "rn", "lpn"]:
            return AgentType.NURSE
        elif user_role in ["patient", "client"]:
            return AgentType.PATIENT
        
        # Domain-based routing
        if domain in ["healthcare", "medical", "clinical"]:
            if "team" in request_type or "collaboration" in request_type:
                return AgentType.CARETEAM
            return AgentType.DOCTOR
        elif domain in ["business", "operations", "admin"]:
            return AgentType.BUSINESS
        elif domain in ["payment", "billing", "financial"]:
            return AgentType.PAYMENT
        elif domain in ["analytics", "reporting", "insights"]:
            return AgentType.INSIGHT
        elif domain in ["development", "coding", "programming"]:
            return AgentType.DEVELOPMENT
        elif domain in ["media", "imaging", "files"]:
            return AgentType.MEDIA
        elif domain in ["education", "training", "learning"]:
            return AgentType.EDUCATION
        elif domain in ["chat", "conversation", "messaging"]:
            return AgentType.CHAT
        
        # Default to chat agent for general queries
        return AgentType.CHAT
    
    async def log_routing_event(
        self, 
        agent_type: AgentType, 
        endpoint: str, 
        method: str, 
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Log routing event for monitoring and debugging"""
        
        event_data = {
            "agent_type": agent_type.value,
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "timestamp": "now",  # In production, use actual timestamp
        }
        
        if error_message:
            event_data["error"] = error_message
        
        # Store in Redis for short-term monitoring
        event_key = f"routing_events:{agent_type}:{status}"
        await self.redis.lpush(event_key, str(event_data))
        await self.redis.ltrim(event_key, 0, 999)  # Keep last 1000 events
        await self.redis.expire(event_key, 86400)  # Expire after 24 hours
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process orchestration request"""
        
        # Extract routing information
        agent_type_str = request_data.get("agent_type")
        context = request_data.get("context", {})
        
        # Determine target agent
        if agent_type_str:
            try:
                target_agent = AgentType(agent_type_str)
            except ValueError:
                target_agent = await self.determine_best_agent(context)
        else:
            target_agent = await self.determine_best_agent(context)
        
        # Route the request
        endpoint = request_data.get("endpoint", "/")
        method = request_data.get("method", "GET")
        data = request_data.get("data")
        headers = request_data.get("headers")
        
        result = await self.route_request(
            agent_type=target_agent,
            endpoint=endpoint,
            method=method,
            data=data,
            headers=headers
        )
        
        return {
            "routed_to": target_agent.value,
            "result": result
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()