"""
FastAPI application for Powerhouse Multi-Agent Platform.

This is the main entry point for the REST API that exposes the multi-agent
platform capabilities via HTTP endpoints.
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from config.settings import settings
from api.models import HealthCheckResponse, ErrorResponse
from api.routes import workflows, agents, auth
from api import learning_routes, config_routes, budget_routes
from api import marketplace_routes, agent_builder_routes, app_builder_routes

# Import additional route modules
try:
    from api.routes import performance_routes
    HAS_PERFORMANCE_ROUTES = True
except ImportError:
    HAS_PERFORMANCE_ROUTES = False

try:
    from api.routes import forecasting_routes
    HAS_FORECASTING_ROUTES = True
except ImportError:
    HAS_FORECASTING_ROUTES = False

try:
    from api.routes import autonomous_agent_routes
    HAS_AUTONOMOUS_ROUTES = True
except ImportError:
    HAS_AUTONOMOUS_ROUTES = False

try:
    from api.routes import file_management
    HAS_FILE_MANAGEMENT = True
except ImportError:
    HAS_FILE_MANAGEMENT = False

try:
    from api.routes import exponential_learning_routes
    HAS_EXPONENTIAL_LEARNING = True
except ImportError:
    HAS_EXPONENTIAL_LEARNING = False

try:
    from api import observability_routes
    HAS_OBSERVABILITY_ROUTES = True
except ImportError:
    HAS_OBSERVABILITY_ROUTES = False

from database.session import get_engine
from database.models import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Lifespan Events
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Powerhouse Multi-Agent Platform API")
    logger.info(f"Version: {settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize audit logger
    try:
        from core.security import audit_logger
        await audit_logger.start()
        logger.info("Audit logger started")
    except Exception as e:
        logger.warning(f"Could not start audit logger: {e}")
    
    # Create database tables
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
    
    # Initialize online learning (if Kafka is enabled)
    from config.kafka_config import kafka_config
    model_updater = None
    if kafka_config.ENABLE_KAFKA:
        try:
            from core.online_learning import get_model_updater
            model_updater = get_model_updater(
                kafka_servers=kafka_config.KAFKA_BOOTSTRAP_SERVERS,
                force_new=True
            )
            if model_updater:
                model_updater.start()
                logger.info("Online learning model updater started")
        except Exception as e:
            logger.warning(f"Failed to start model updater: {e}")
    else:
        logger.info("Kafka disabled, online learning not started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Powerhouse Multi-Agent Platform API")
    
    # Stop audit logger
    try:
        from core.security import audit_logger
        await audit_logger.stop()
        logger.info("Audit logger stopped")
    except Exception as e:
        logger.warning(f"Error stopping audit logger: {e}")
    
    # Stop model updater
    if model_updater:
        try:
            model_updater.stop()
            logger.info("Model updater stopped")
        except Exception as e:
            logger.error(f"Error stopping model updater: {e}")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    **Powerhouse Multi-Agent Platform API**
    
    A B2B multi-agent platform that delivers repeatable ROI on defined workflows.
    
    ## Features
    
    * **Compliance Intelligence**: Multi-agent compliance analysis and risk assessment
    * **19 Specialized Agents**: ReAct, Debate, Evaluator, Governor, and 15 more
    * **Multi-Tenancy**: Secure tenant isolation and data separation
    * **JWT & API Key Auth**: Flexible authentication for different use cases
    * **Real-time Status**: Track workflow progress in real-time
    * **Comprehensive Reports**: Detailed compliance reports with risk assessments
    * **Online Learning**: Continuous model improvement via real-time feedback pipeline
    
    ## Authentication
    
    Two authentication methods are supported:
    
    1. **JWT Token** (OAuth2): Use `/api/v1/auth/token` to get a token
       - Demo credentials: username=any, password=demo123
    2. **API Key**: Include `X-API-Key` header with your API key
       - Demo API key: demo-api-key-12345
    
    ## Quick Start
    
    1. Get an access token or use API key
    2. Start a compliance workflow: `POST /api/v1/workflows/compliance`
    3. Check status: `GET /api/v1/workflows/{workflow_id}/status`
    4. Get results: `GET /api/v1/workflows/{workflow_id}/results`
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# ============================================================================
# Middleware
# ============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware (JWT validation, audit logging)
try:
    from api.middleware import SecurityMiddleware, RateLimitMiddleware
    # Note: SecurityMiddleware is commented out by default to not break existing functionality
    # Uncomment when ready to enforce JWT authentication on all endpoints
    # app.add_middleware(SecurityMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=120)
    logger.info("Security middleware loaded (JWT auth disabled by default)")
except ImportError as e:
    logger.warning(f"Could not load security middleware: {e}")


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            message="Invalid request data",
            details={"errors": exc.errors()},
            timestamp=datetime.utcnow()
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details={"error": str(exc)} if settings.debug else None,
            timestamp=datetime.utcnow()
        ).model_dump()
    )


# ============================================================================
# Routes
# ============================================================================

# Health check endpoint
@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["health"],
    summary="Health Check",
    description="Check if the API is running and database is connected"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns the current status of the API and its dependencies.
    """
    # Check database connection
    db_connected = True
    try:
        from database.session import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_connected = False
    
    return HealthCheckResponse(
        status="healthy" if db_connected else "degraded",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        database_connected=db_connected
    )


# Root endpoint
@app.get(
    "/",
    tags=["root"],
    summary="API Root",
    description="Get API information and links to documentation"
)
async def root():
    """
    API root endpoint.
    
    Returns basic information about the API and links to documentation.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "health": "/health",
            "auth": f"{settings.api_v1_prefix}/auth",
            "workflows": f"{settings.api_v1_prefix}/workflows",
            "agents": f"{settings.api_v1_prefix}/agents",
            "learning": "/api/learning"
        }
    }


# Include routers
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(workflows.router, prefix=settings.api_v1_prefix)
app.include_router(agents.router, prefix=settings.api_v1_prefix)
app.include_router(learning_routes.router)  # Learning routes have their own prefix
app.include_router(config_routes.router)  # Configuration routes have their own prefix
app.include_router(budget_routes.router, prefix=settings.api_v1_prefix)  # Budget and rate limiting routes
app.include_router(marketplace_routes.router, prefix=settings.api_v1_prefix, tags=["marketplace"])  # Marketplace routes
app.include_router(agent_builder_routes.router, prefix=settings.api_v1_prefix, tags=["agent-builder"])  # Agent Builder routes
app.include_router(app_builder_routes.router, prefix=settings.api_v1_prefix, tags=["app-builder"])  # App Builder routes

# Include new security authentication routes
try:
    from api.auth_routes import router as security_auth_router
    app.include_router(security_auth_router, tags=["security"])
    logger.info("Security authentication routes loaded")
except ImportError as e:
    logger.warning(f"Could not load security auth routes: {e}")

# Include optional routers if available
if HAS_PERFORMANCE_ROUTES:
    app.include_router(performance_routes.router, prefix="/api/performance", tags=["performance"])

if HAS_FORECASTING_ROUTES:
    app.include_router(forecasting_routes.router, prefix="/api/forecasting", tags=["forecasting"])

if HAS_AUTONOMOUS_ROUTES:
    app.include_router(autonomous_agent_routes.router, prefix="/api/autonomous", tags=["autonomous"])

if HAS_FILE_MANAGEMENT:
    app.include_router(file_management.router, prefix="/api/files", tags=["files"])

if HAS_EXPONENTIAL_LEARNING:
    app.include_router(exponential_learning_routes.router, prefix="/api/exponential", tags=["exponential"])

if HAS_OBSERVABILITY_ROUTES:
    app.include_router(observability_routes.router, tags=["observability"])
    logger.info("Observability routes loaded (telemetry, checkpoints, circuit breakers)")

# Include integration ecosystem routes
try:
    from api.integration_routes import router as integration_router
    app.include_router(integration_router, tags=["integrations"])
    logger.info("Integration ecosystem routes loaded (webhooks, connectors, plugins, data porter)")
except ImportError as e:
    logger.warning(f"Could not load integration routes: {e}")

# Include AI quality routes
try:
    from api.ai_quality_routes import router as ai_quality_router
    app.include_router(ai_quality_router, tags=["ai-quality"])
    logger.info("AI quality routes loaded (model versioning, metrics, training data, explainability)")
except ImportError as e:
    logger.warning(f"Could not load AI quality routes: {e}")

# Setup API documentation
try:
    from api.docs_config import setup_api_docs
    setup_api_docs(app)
    logger.info("Enhanced API documentation configured")
except ImportError as e:
    logger.warning(f"Could not configure enhanced docs: {e}")

# Include commercial routes (multi-tenancy, billing, usage tracking)
try:
    from api.commercial_routes import router as commercial_router
    app.include_router(commercial_router, tags=["commercial"])
    logger.info("Commercial routes loaded (multi-tenancy, billing, usage)")
except ImportError as e:
    logger.warning(f"Could not load commercial routes: {e}")

# Include deployment routes (health checks, backups)
try:
    from api.deployment_routes import router as deployment_router
    app.include_router(deployment_router, tags=["deployment"])
    logger.info("Deployment routes loaded (health checks, backups)")
except ImportError as e:
    logger.warning(f"Could not load deployment routes: {e}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
