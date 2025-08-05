"""Master LINC Agent - Central orchestration and routing hub"""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .config.logging import setup_logging
from .handlers import health, auth, orchestration
from .utils.exceptions import setup_exception_handlers

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    setup_logging(settings.log_level)
    
    app = FastAPI(
        title="Master LINC Agent",
        description="Central orchestration and routing hub for BrainSAIT LINC Agents",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(orchestration.router, prefix="/orchestrate", tags=["orchestration"])
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    return app

app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )