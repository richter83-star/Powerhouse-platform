
"""
OpenAPI/Swagger Documentation Configuration
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    """Generate custom OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Powerhouse B2B Platform API",
        version="1.0.0",
        description="""
# Powerhouse B2B Multi-Agent Platform API

Enterprise-grade API for managing intelligent multi-agent systems with advanced features:

## Core Features
- **Multi-Agent Orchestration**: Coordinate complex agent workflows
- **Real-time Learning**: Continuous model improvement and adaptation
- **Performance Monitoring**: Comprehensive metrics and analytics
- **Security & Compliance**: RBAC, JWT auth, audit logging, encryption

## Integration Ecosystem
- **Webhooks**: Event-driven integrations with signature verification
- **API Connectors**: Unified interface for third-party APIs with rate limiting
- **Plugin System**: Dynamic plugin loading and management
- **Data Porter**: Bulk import/export in multiple formats (JSON, CSV, JSONL)

## Authentication
All protected endpoints require JWT bearer token authentication:
```
Authorization: Bearer <your_token>
```

Obtain tokens via `/auth/login` endpoint.

## Rate Limiting
API endpoints are rate-limited per user/IP. Default limits:
- **Standard**: 100 requests/minute
- **Burst**: 200 requests/minute

## Support
- Documentation: https://docs.powerhouse.ai
- Support: support@powerhouse.ai
        """,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login endpoint"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add tags
    openapi_schema["tags"] = [
        {
            "name": "authentication",
            "description": "User authentication and session management"
        },
        {
            "name": "agents",
            "description": "Multi-agent system management"
        },
        {
            "name": "workflows",
            "description": "Workflow orchestration and execution"
        },
        {
            "name": "monitoring",
            "description": "Performance metrics and observability"
        },
        {
            "name": "integrations",
            "description": "Webhooks, connectors, plugins, and data operations"
        },
        {
            "name": "security",
            "description": "RBAC, permissions, and audit logs"
        },
        {
            "name": "hardening",
            "description": "State management, telemetry, and rate limiting"
        }
    ]
    
    # Add example responses
    openapi_schema["components"]["examples"] = {
        "LoginSuccess": {
            "value": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        },
        "ValidationError": {
            "value": {
                "detail": [
                    {
                        "loc": ["body", "email"],
                        "msg": "field required",
                        "type": "value_error.missing"
                    }
                ]
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_api_docs(app: FastAPI):
    """Setup API documentation"""
    app.openapi = lambda: custom_openapi(app)
    
    # Configure Swagger UI
    app.swagger_ui_parameters = {
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "displayRequestDuration": True,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "syntaxHighlight.theme": "monokai"
    }
