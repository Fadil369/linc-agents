"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import os
from typing import Generator

from .models import Base

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./brainsait_agents.db")

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true"
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true"
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

class DatabaseManager:
    """Database operations manager"""
    
    @staticmethod
    def init_database():
        """Initialize database with tables and initial data"""
        create_tables()
        DatabaseManager.seed_initial_data()
    
    @staticmethod
    def seed_initial_data():
        """Seed database with initial agents and system data"""
        from .models import Agent
        
        with get_db_session() as db:
            # Check if agents already exist
            if db.query(Agent).first():
                return
            
            # Core infrastructure agents
            core_agents = [
                {
                    "name": "masterlinc",
                    "type": "core",
                    "subdomain": "master.brainsait.io",
                    "port": 8000,
                    "description": "Central orchestration hub for all LINC agents",
                    "capabilities": ["orchestration", "routing", "monitoring", "load_balancing"],
                    "dependencies": []
                },
                {
                    "name": "authlinc",
                    "type": "core", 
                    "subdomain": "auth.brainsait.io",
                    "port": 8001,
                    "description": "Authentication and authorization gateway",
                    "capabilities": ["authentication", "authorization", "session_management", "rbac"],
                    "dependencies": ["masterlinc"]
                },
                {
                    "name": "oidlinc",
                    "type": "core",
                    "subdomain": "oid.brainsait.io", 
                    "port": 8050,
                    "description": "Digital identity manager using PEN OID system",
                    "capabilities": ["digital_identity", "healthcare_ids", "national_records"],
                    "dependencies": ["authlinc"]
                }
            ]
            
            # Healthcare agents
            healthcare_agents = [
                {
                    "name": "doctorlinc",
                    "type": "healthcare",
                    "subdomain": "doctor.brainsait.io",
                    "port": 8010,
                    "description": "Physician assistant for clinical decision support",
                    "capabilities": ["clinical_documentation", "fhir_integration", "arabic_transcription", "soap_notes"],
                    "dependencies": ["authlinc", "oidlinc"]
                },
                {
                    "name": "nurslinc", 
                    "type": "healthcare",
                    "subdomain": "nurse.brainsait.io",
                    "port": 8011,
                    "description": "Nursing workflow automation and support",
                    "capabilities": ["shift_reports", "care_checklists", "medication_scheduling"],
                    "dependencies": ["doctorlinc", "authlinc"]
                },
                {
                    "name": "patientlinc",
                    "type": "healthcare", 
                    "subdomain": "patient.brainsait.io",
                    "port": 8012,
                    "description": "Patient experience navigator and health education",
                    "capabilities": ["patient_education", "appointment_scheduling", "health_tracking"],
                    "dependencies": ["authlinc", "oidlinc"]
                },
                {
                    "name": "careteamlinc",
                    "type": "healthcare",
                    "subdomain": "careteam.brainsait.io", 
                    "port": 8013,
                    "description": "Multi-provider care coordination",
                    "capabilities": ["care_coordination", "provider_communication", "telehealth"],
                    "dependencies": ["doctorlinc", "nurslinc", "patientlinc"]
                }
            ]
            
            # Business agents
            business_agents = [
                {
                    "name": "bizlinc",
                    "type": "business",
                    "subdomain": "biz.brainsait.io",
                    "port": 8020, 
                    "description": "Healthcare business intelligence and SME support",
                    "capabilities": ["business_intelligence", "saudi_compliance", "rfp_generation"],
                    "dependencies": ["authlinc"]
                },
                {
                    "name": "paylinc",
                    "type": "business",
                    "subdomain": "pay.brainsait.io",
                    "port": 8021,
                    "description": "Payment processing and financial management", 
                    "capabilities": ["payment_processing", "billing", "financial_reporting"],
                    "dependencies": ["authlinc", "bizlinc"]
                },
                {
                    "name": "insightlinc",
                    "type": "business",
                    "subdomain": "insight.brainsait.io",
                    "port": 8022,
                    "description": "Business analytics and intelligence dashboards",
                    "capabilities": ["analytics", "reporting", "dashboards", "kpi_tracking"],
                    "dependencies": ["bizlinc", "paylinc"]
                }
            ]
            
            # Development and automation agents
            dev_agents = [
                {
                    "name": "devlinc",
                    "type": "development",
                    "subdomain": "dev.brainsait.io",
                    "port": 8030,
                    "description": "DevOps automation and infrastructure management",
                    "capabilities": ["devops", "deployment", "monitoring", "infrastructure"],
                    "dependencies": ["masterlinc"]
                },
                {
                    "name": "autolinc", 
                    "type": "automation",
                    "subdomain": "auto.brainsait.io",
                    "port": 8031,
                    "description": "Workflow orchestration and cross-platform automation",
                    "capabilities": ["workflow_automation", "integration", "n8n_management"],
                    "dependencies": ["devlinc"]
                },
                {
                    "name": "codelinc",
                    "type": "development", 
                    "subdomain": "code.brainsait.io",
                    "port": 8032,
                    "description": "Code generation and development assistance",
                    "capabilities": ["code_generation", "documentation", "api_integration"],
                    "dependencies": ["devlinc"]
                }
            ]
            
            # Content and communication agents
            content_agents = [
                {
                    "name": "medialinc",
                    "type": "content",
                    "subdomain": "media.brainsait.io", 
                    "port": 8040,
                    "description": "Multimedia content transformation and localization",
                    "capabilities": ["video_processing", "arabic_dubbing", "content_localization"],
                    "dependencies": ["authlinc"]
                },
                {
                    "name": "edulinc",
                    "type": "content",
                    "subdomain": "edu.brainsait.io",
                    "port": 8041, 
                    "description": "Educational content management and course creation",
                    "capabilities": ["lms_integration", "course_authoring", "assessment_creation"],
                    "dependencies": ["medialinc"]
                },
                {
                    "name": "chatlinc",
                    "type": "communication",
                    "subdomain": "chat.brainsait.io",
                    "port": 8042,
                    "description": "Multilingual communication hub",
                    "capabilities": ["multilingual_chat", "intent_recognition", "customer_service"],
                    "dependencies": ["authlinc"]
                }
            ]
            
            # Add all agents
            all_agents = core_agents + healthcare_agents + business_agents + dev_agents + content_agents
            
            for agent_data in all_agents:
                agent = Agent(**agent_data)
                db.add(agent)
            
            db.commit()