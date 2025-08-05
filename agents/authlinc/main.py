"""
AuthLINC - Identity & Security Gateway
Unified authentication and authorization for all LINC agents
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from shared.models.base_agent import BaseLINCAgent
from shared.database import get_db
from shared.database.models import User, UserSession, SystemEvent
from shared.auth import (
    authenticate_user, create_access_token, get_password_hash,
    create_user_session, get_session_by_token, invalidate_session,
    verify_token, get_current_user, get_user_permissions
)

logger = logging.getLogger(__name__)

class UserLogin(BaseModel):
    username: str
    password: str
    agent_name: str = "authlinc"

class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    arabic_name: Optional[str] = None
    role: str = "patient"
    preferred_language: str = "en"
    phone: Optional[str] = None
    saudi_id: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    arabic_name: Optional[str]
    role: str
    preferred_language: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse
    permissions: list[str]

class PasswordReset(BaseModel):
    email: str
    
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class AuthLINC(BaseLINCAgent):
    """Authentication and authorization gateway"""
    
    def __init__(self):
        super().__init__(
            name="authlinc",
            version="1.0.0",
            description="Identity & Security Gateway for unified authentication",
            port=8001,
            dependencies=["masterlinc"]
        )
        
        # Setup custom routes
        self.add_routes(self._setup_routes)
    
    def _setup_routes(self, app: FastAPI):
        """Setup AuthLINC specific routes"""
        
        @app.post("/auth/login", response_model=TokenResponse)
        async def login(
            user_data: UserLogin,
            request: Request,
            db: Session = Depends(get_db)
        ):
            """Authenticate user and create session"""
            try:
                # Authenticate user
                user = authenticate_user(user_data.username, user_data.password, db)
                if not user:
                    # Log failed login attempt
                    event = SystemEvent(
                        event_type="auth.login_failed",
                        agent_name="authlinc",
                        description=f"Failed login attempt for {user_data.username}",
                        event_metadata={
                            "username": user_data.username,
                            "ip_address": request.client.host if request.client else "test",
                            "user_agent": request.headers.get("user-agent")
                        },
                        severity="warning"
                    )
                    db.add(event)
                    db.commit()
                    
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid username or password"
                    )
                
                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Account is disabled"
                    )
                
                # Create access token
                access_token_expires = timedelta(minutes=30)
                access_token = create_access_token(
                    data={"sub": user.username, "user_id": user.id},
                    expires_delta=access_token_expires
                )
                
                # Create session
                session = create_user_session(
                    user=user,
                    agent_name=user_data.agent_name,
                    ip_address=request.client.host if request.client else "test",
                    user_agent=request.headers.get("user-agent", ""),
                    db=db
                )
                
                # Update last login
                user.last_login = datetime.utcnow()
                db.commit()
                
                # Log successful login
                event = SystemEvent(
                    event_type="auth.login_success",
                    agent_name="authlinc",
                    user_id=user.id,
                    description=f"Successful login for {user.username}",
                    event_metadata={
                        "agent_name": user_data.agent_name,
                        "ip_address": request.client.host if request.client else "test"
                    }
                )
                db.add(event)
                db.commit()
                
                # Get user permissions
                permissions = get_user_permissions(user)
                
                return TokenResponse(
                    access_token=access_token,
                    token_type="bearer",
                    expires_in=1800,  # 30 minutes
                    user=UserResponse(
                        id=user.id,
                        username=user.username,
                        email=user.email,
                        full_name=user.full_name,
                        arabic_name=user.arabic_name,
                        role=user.role,
                        preferred_language=user.preferred_language,
                        is_active=user.is_active,
                        is_verified=user.is_verified,
                        created_at=user.created_at,
                        last_login=user.last_login
                    ),
                    permissions=permissions
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Login error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication service error"
                )
        
        @app.post("/auth/register", response_model=UserResponse)
        async def register(
            user_data: UserRegistration,
            request: Request,
            db: Session = Depends(get_db)
        ):
            """Register new user"""
            try:
                # Check if username exists
                existing_user = db.query(User).filter(
                    (User.username == user_data.username) | 
                    (User.email == user_data.email)
                ).first()
                
                if existing_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username or email already registered"
                    )
                
                # Create new user
                hashed_password = get_password_hash(user_data.password)
                new_user = User(
                    username=user_data.username,
                    email=user_data.email,
                    full_name=user_data.full_name,
                    arabic_name=user_data.arabic_name,
                    role=user_data.role,
                    preferred_language=user_data.preferred_language,
                    phone=user_data.phone,
                    saudi_id=user_data.saudi_id,
                    password_hash=hashed_password
                )
                
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                
                # Log registration
                event = SystemEvent(
                    event_type="auth.user_registered",
                    agent_name="authlinc",
                    user_id=new_user.id,
                    description=f"New user registration: {new_user.username}",
                    event_metadata={
                        "role": new_user.role,
                        "ip_address": request.client.host if request.client else "test"
                    }
                )
                db.add(event)
                db.commit()
                
                return UserResponse(
                    id=new_user.id,
                    username=new_user.username,
                    email=new_user.email,
                    full_name=new_user.full_name,
                    arabic_name=new_user.arabic_name,
                    role=new_user.role,
                    preferred_language=new_user.preferred_language,
                    is_active=new_user.is_active,
                    is_verified=new_user.is_verified,
                    created_at=new_user.created_at,
                    last_login=new_user.last_login
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Registration error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Registration service error"
                )
        
        @app.post("/auth/logout")
        async def logout(
            credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
            db: Session = Depends(get_db)
        ):
            """Logout user and invalidate session"""
            try:
                # Invalidate session
                success = invalidate_session(credentials.credentials, db)
                
                if success:
                    return {"message": "Successfully logged out"}
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid session"
                    )
                    
            except Exception as e:
                logger.error(f"Logout error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Logout service error"
                )
        
        @app.get("/auth/me", response_model=UserResponse)
        async def get_current_user_info(
            current_user: User = Depends(get_current_user)
        ):
            """Get current user information"""
            return UserResponse(
                id=current_user.id,
                username=current_user.username,
                email=current_user.email,
                full_name=current_user.full_name,
                arabic_name=current_user.arabic_name,
                role=current_user.role,
                preferred_language=current_user.preferred_language,
                is_active=current_user.is_active,
                is_verified=current_user.is_verified,
                created_at=current_user.created_at,
                last_login=current_user.last_login
            )
        
        @app.get("/auth/permissions")
        async def get_user_permissions_endpoint(
            current_user: User = Depends(get_current_user)
        ):
            """Get current user permissions"""
            permissions = get_user_permissions(current_user)
            return {"permissions": permissions}
        
        @app.post("/auth/verify-token")
        async def verify_token_endpoint(
            credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
            db: Session = Depends(get_db)
        ):
            """Verify token validity"""
            try:
                # Verify token and get user
                username = verify_token(credentials)
                user = db.query(User).filter(User.username == username).first()
                
                if not user or not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or inactive user"
                    )
                
                return {
                    "valid": True,
                    "user_id": user.id,
                    "username": user.username,
                    "role": user.role,
                    "permissions": get_user_permissions(user)
                }
                
            except HTTPException:
                return {"valid": False}
            except Exception as e:
                logger.error(f"Token verification error: {e}")
                return {"valid": False}
        
        @app.post("/auth/change-password")
        async def change_password(
            password_data: PasswordChange,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            """Change user password"""
            try:
                # Verify current password
                if not authenticate_user(current_user.username, password_data.current_password, db):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Current password is incorrect"
                    )
                
                # Update password
                current_user.password_hash = get_password_hash(password_data.new_password)
                db.commit()
                
                # Log password change
                event = SystemEvent(
                    event_type="auth.password_changed",
                    agent_name="authlinc",
                    user_id=current_user.id,
                    description=f"Password changed for {current_user.username}"
                )
                db.add(event)
                db.commit()
                
                return {"message": "Password changed successfully"}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Password change error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Password change service error"
                )
        
        @app.get("/auth/sessions")
        async def get_user_sessions(
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            """Get user's active sessions"""
            sessions = db.query(UserSession).filter(
                UserSession.user_id == current_user.id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).all()
            
            return {
                "sessions": [
                    {
                        "id": session.id,
                        "agent_name": session.agent_name,
                        "ip_address": session.ip_address,
                        "created_at": session.created_at,
                        "expires_at": session.expires_at
                    }
                    for session in sessions
                ]
            }

def create_app():
    """Create and configure the AuthLINC application"""
    return AuthLINC()

if __name__ == "__main__":
    app = create_app()
    app.run()