"""
Shared authentication utilities for LINC agents
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import os

from shared.database import get_db
from shared.database.models import User, UserSession

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "default-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer for token extraction
security = HTTPBearer()

class TokenData:
    """Token data structure"""
    def __init__(self, username: Optional[str] = None):
        self.username = username

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token and return username"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    return token_data.username

def get_current_user(
    token_username: str = Depends(verify_token),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from token"""
    user = db.query(User).filter(User.username == token_username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
    """Authenticate user with username and password"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_user_session(
    user: User,
    agent_name: str,
    ip_address: str,
    user_agent: str,
    db: Session
) -> UserSession:
    """Create a new user session"""
    # Generate session token
    session_data = {
        "sub": user.username,
        "user_id": user.id,
        "agent": agent_name
    }
    session_token = create_access_token(
        session_data,
        expires_delta=timedelta(hours=24)  # Longer session duration
    )
    
    # Create session record
    session = UserSession(
        user_id=user.id,
        session_token=session_token,
        agent_name=agent_name,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session

def get_session_by_token(token: str, db: Session) -> Optional[UserSession]:
    """Get session by token"""
    return db.query(UserSession).filter(
        UserSession.session_token == token,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).first()

def invalidate_session(session_token: str, db: Session) -> bool:
    """Invalidate a user session"""
    session = db.query(UserSession).filter(
        UserSession.session_token == session_token
    ).first()
    
    if session:
        session.is_active = False
        db.commit()
        return True
    
    return False

class RoleChecker:
    """Role-based access control checker"""
    
    def __init__(self, required_roles: list[str]):
        self.required_roles = required_roles
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> bool:
        if current_user.role in self.required_roles:
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

# Common role checkers
require_admin = RoleChecker(["admin"])
require_doctor = RoleChecker(["doctor", "admin"])
require_nurse = RoleChecker(["nurse", "doctor", "admin"])
require_healthcare = RoleChecker(["patient", "nurse", "doctor", "admin"])

def get_user_permissions(user: User) -> list[str]:
    """Get user permissions based on role"""
    role_permissions = {
        "admin": [
            "manage_users", "manage_agents", "view_all_data", 
            "system_config", "audit_logs"
        ],
        "doctor": [
            "patient_records", "prescriptions", "diagnoses", 
            "fhir_access", "clinical_documentation"
        ],
        "nurse": [
            "patient_care", "medication_admin", "shift_reports",
            "care_plans", "vital_signs"
        ],
        "patient": [
            "own_records", "appointments", "health_tracking",
            "education_content", "communication"
        ],
        "business": [
            "analytics", "reports", "billing", "business_intelligence"
        ]
    }
    
    return role_permissions.get(user.role, [])

def check_permission(user: User, permission: str) -> bool:
    """Check if user has specific permission"""
    user_permissions = get_user_permissions(user)
    return permission in user_permissions

def permission_required(permission: str):
    """Decorator for permission-based access control"""
    def decorator(current_user: User = Depends(get_current_active_user)):
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return decorator