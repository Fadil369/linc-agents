"""
BrainSAIT LINC Shared Database Models
Core models for the unified agent architecture
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

Base = declarative_base()

class Agent(Base):
    """Core agent registry and status tracking"""
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "masterlinc", "doctorlinc"
    type = Column(String(30), nullable=False)  # e.g., "core", "healthcare", "business"
    status = Column(String(20), default="offline")  # online, offline, error, maintenance
    version = Column(String(20), default="1.0.0")
    subdomain = Column(String(100), unique=True)  # e.g., "doctor.brainsait.io"
    port = Column(Integer, unique=True)
    description = Column(Text)
    capabilities = Column(JSON)  # List of features/APIs this agent provides
    dependencies = Column(JSON)  # List of other agents this depends on
    health_check_url = Column(String(200))
    last_heartbeat = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="agent")

class User(Base):
    """User accounts across all agents"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    arabic_name = Column(String(100))  # Arabic name support
    role = Column(String(30), default="patient")  # patient, doctor, nurse, admin, etc.
    preferred_language = Column(String(10), default="en")  # en, ar
    saudi_id = Column(String(20), unique=True)  # National ID
    healthcare_id = Column(String(50))  # Healthcare system ID
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    password_hash = Column(String(128))
    avatar_url = Column(String(200))
    user_metadata = Column(JSON)  # Flexible user data
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    messages = relationship("Message", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")

class UserSession(Base):
    """User authentication sessions"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    agent_name = Column(String(50), ForeignKey("agents.name"))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class Conversation(Base):
    """Conversation sessions between users and agents"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_agent = Column(String(50), ForeignKey("agents.name"), nullable=False)
    type = Column(String(30), default="chat")  # chat, consultation, workflow, etc.
    language = Column(String(10), default="en")
    status = Column(String(20), default="active")  # active, completed, transferred, error
    priority = Column(String(10), default="normal")  # low, normal, high, urgent
    context = Column(JSON)  # Conversation context and state
    summary = Column(Text)  # AI-generated conversation summary
    tags = Column(JSON)  # Categorization tags
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime)
    last_activity = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    """Messages within conversations"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    agent_name = Column(String(50), ForeignKey("agents.name"))
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="text")  # text, audio, image, file
    language = Column(String(10), default="en")
    direction = Column(String(10), nullable=False)  # inbound, outbound
    processed = Column(Boolean, default=False)
    message_metadata = Column(JSON)  # Message metadata (attachments, etc.)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")
    agent = relationship("Agent", back_populates="messages")

class InterAgentMessage(Base):
    """Messages between agents for coordination"""
    __tablename__ = "inter_agent_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    from_agent = Column(String(50), ForeignKey("agents.name"), nullable=False)
    to_agent = Column(String(50), ForeignKey("agents.name"), nullable=False)
    message_type = Column(String(30), nullable=False)  # handoff, request, response, notification
    payload = Column(JSON, nullable=False)
    priority = Column(String(10), default="normal")
    status = Column(String(20), default="pending")  # pending, delivered, failed
    correlation_id = Column(String(100))  # For tracking request/response chains
    created_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime)

class SystemEvent(Base):
    """System-wide events and audit log"""
    __tablename__ = "system_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)  # agent.startup, user.login, etc.
    agent_name = Column(String(50), ForeignKey("agents.name"))
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(Text)
    event_metadata = Column(JSON)
    severity = Column(String(10), default="info")  # debug, info, warning, error, critical
    created_at = Column(DateTime, default=func.now())

class HealthcareRecord(Base):
    """Healthcare-specific data (FHIR-compatible)"""
    __tablename__ = "healthcare_records"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    record_type = Column(String(50), nullable=False)  # consultation, prescription, lab_result, etc.
    fhir_resource_type = Column(String(50))  # Patient, Observation, DiagnosticReport, etc.
    fhir_resource_id = Column(String(100))
    data = Column(JSON, nullable=False)  # FHIR resource data
    source_agent = Column(String(50), ForeignKey("agents.name"))
    provider_id = Column(String(100))  # Healthcare provider identifier
    facility_id = Column(String(100))  # Healthcare facility identifier
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())