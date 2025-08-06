"""Configuration settings for Master LINC Agent"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Basic configuration
    agent_name: str = "Master LINC"
    agent_description: str = "Central orchestration and routing hub"
    port: int = Field(default=8000, env="MASTER_LINC_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database configuration
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # Security configuration
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=15, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="ALLOWED_ORIGINS"
    )
    
    # Agent registry configuration
    agent_registry_ttl: int = Field(default=60, env="AGENT_REGISTRY_TTL")  # seconds
    agent_health_check_interval: int = Field(default=30, env="AGENT_HEALTH_CHECK_INTERVAL")  # seconds
    
    # External service URLs
    auth_linc_url: str = Field(default="http://authlinc:8001", env="AUTH_LINC_URL")
    doctor_linc_url: str = Field(default="http://doctorlinc:8010", env="DOCTOR_LINC_URL")
    nurse_linc_url: str = Field(default="http://nurslinc:8011", env="NURSE_LINC_URL")
    patient_linc_url: str = Field(default="http://patientlinc:8012", env="PATIENT_LINC_URL")
    careteam_linc_url: str = Field(default="http://careteamlinc:8013", env="CARETEAM_LINC_URL")
    biz_linc_url: str = Field(default="http://bizlinc:8020", env="BIZ_LINC_URL")
    pay_linc_url: str = Field(default="http://paylinc:8021", env="PAY_LINC_URL")
    insight_linc_url: str = Field(default="http://insightlinc:8022", env="INSIGHT_LINC_URL")
    dev_linc_url: str = Field(default="http://devlinc:8030", env="DEV_LINC_URL")
    auto_linc_url: str = Field(default="http://autolinc:8031", env="AUTO_LINC_URL")
    code_linc_url: str = Field(default="http://codelinc:8032", env="CODE_LINC_URL")
    media_linc_url: str = Field(default="http://medialinc:8040", env="MEDIA_LINC_URL")
    edu_linc_url: str = Field(default="http://edulinc:8041", env="EDU_LINC_URL")
    chat_linc_url: str = Field(default="http://chatlinc:8042", env="CHAT_LINC_URL")
    oid_linc_url: str = Field(default="http://oidlinc:8050", env="OID_LINC_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()