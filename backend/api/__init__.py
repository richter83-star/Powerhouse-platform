
"""
API module initialization.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.logging import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application
    """
    app = FastAPI(
        title="Powerhouse B2B Multi-Agent Platform",
        description="Enterprise-grade multi-agent system with real-time monitoring",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers (optional - will be added by specific startup scripts)
    # Individual startup scripts register their own routes
    
    logger.info("FastAPI application initialized")
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Powerhouse B2B Platform",
            "version": "1.0.0",
            "status": "operational"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return app


__all__ = ["create_app"]
