"""
Enhanced OpenAPI/Swagger Documentation Configuration
"""
import json
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from config.settings import settings


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Generate enhanced custom OpenAPI schema with examples"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description="""
# Powerhouse Multi-Agent Platform API

Enterprise-grade B2B multi-agent platform API that delivers repeatable ROI on defined workflows.

## Core Features

- **Multi-Agent Orchestration**: Coordinate complex agent workflows with 19+ specialized agents
- **Compliance Intelligence**: Multi-agent compliance analysis and risk assessment
- **Real-time Learning**: Continuous model improvement via feedback pipeline
- **Multi-Tenancy**: Secure tenant isolation and data separation
- **Performance Monitoring**: Comprehensive metrics and analytics
- **Security & Compliance**: RBAC, JWT auth, audit logging, encryption

## Authentication

Two authentication methods are supported:

### 1. JWT Bearer Token (Recommended)
```
Authorization: Bearer <your_access_token>
```

Obtain tokens via `/api/auth/login` endpoint.

### 2. API Key (Legacy)
```
X-API-Key: <your_api_key>
```

## Rate Limiting

API endpoints are rate-limited per user/IP:
- **Standard**: 60 requests/minute
- **Burst**: 120 requests/minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in window
- `X-RateLimit-Reset`: Time when limit resets

## Request Tracking

All requests include a correlation ID for tracking:
- **Request Header**: `X-Correlation-ID` (optional, auto-generated if not provided)
- **Response Header**: `X-Correlation-ID` (always included)

## Error Handling

All errors follow a consistent format:
```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "correlation_id": "abc123-def456",
  "error_code": "ERROR_CODE",
  "details": {},
  "timestamp": "2025-01-01T12:00:00Z"
}
```

## API Versioning

The API uses URL-based versioning:
- Current version: `/api/v1`
- Future versions: `/api/v2`, `/api/v3`, etc.

## Support

- **Documentation**: https://docs.powerhouse.ai
- **Support Email**: support@powerhouse.ai
- **Status Page**: https://status.powerhouse.ai
        """,
        routes=app.routes,
        servers=[
            {
                "url": "http://localhost:8001",
                "description": "Local development server"
            },
            {
                "url": "https://api.powerhouse.ai",
                "description": "Production server"
            }
        ]
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /api/auth/login endpoint. Token expires in 30 minutes."
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication (legacy method)"
        }
    }
    
    # Add comprehensive tags with descriptions
    openapi_schema["tags"] = [
        {
            "name": "health",
            "description": "Health check and system status endpoints",
            "externalDocs": {
                "description": "Health Check Documentation",
                "url": "https://docs.powerhouse.ai/health"
            }
        },
        {
            "name": "authentication",
            "description": "User authentication, registration, and session management",
            "externalDocs": {
                "description": "Authentication Guide",
                "url": "https://docs.powerhouse.ai/auth"
            }
        },
        {
            "name": "workflows",
            "description": "Workflow orchestration and execution. Start, monitor, and retrieve workflow results.",
            "externalDocs": {
                "description": "Workflow Documentation",
                "url": "https://docs.powerhouse.ai/workflows"
            }
        },
        {
            "name": "agents",
            "description": "Multi-agent system management. List, configure, and manage agents.",
            "externalDocs": {
                "description": "Agent Documentation",
                "url": "https://docs.powerhouse.ai/agents"
            }
        },
        {
            "name": "monitoring",
            "description": "Performance metrics, observability, and system monitoring",
            "externalDocs": {
                "description": "Monitoring Guide",
                "url": "https://docs.powerhouse.ai/monitoring"
            }
        },
        {
            "name": "integrations",
            "description": "Webhooks, API connectors, plugins, and data import/export operations",
            "externalDocs": {
                "description": "Integration Guide",
                "url": "https://docs.powerhouse.ai/integrations"
            }
        },
        {
            "name": "security",
            "description": "RBAC, permissions, audit logs, and security management",
            "externalDocs": {
                "description": "Security Documentation",
                "url": "https://docs.powerhouse.ai/security"
            }
        },
        {
            "name": "commercial",
            "description": "Multi-tenancy, billing, usage tracking, and subscription management"
        }
    ]
    
    # Add comprehensive examples
    openapi_schema["components"]["examples"] = {
        "LoginRequest": {
            "summary": "User Login",
            "description": "Example login request",
            "value": {
                "email": "user@example.com",
                "password": "SecurePassword123!",
                "tenant_id": "tenant-abc-123"
            }
        },
        "LoginResponse": {
            "summary": "Login Success",
            "description": "Successful login response with tokens",
            "value": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiZXhwIjoxNzA0MTAwMDAwfQ.example",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh.example",
                "token_type": "bearer",
                "expires_in": 1800
            }
        },
        "ComplianceWorkflowRequest": {
            "summary": "Start Compliance Workflow",
            "description": "Example request to start a compliance analysis workflow",
            "value": {
                "query": "Analyze our data retention policy for GDPR compliance",
                "jurisdiction": "EU",
                "risk_threshold": 0.8,
                "policy_documents": [
                    "https://example.com/policy.pdf"
                ]
            }
        },
        "WorkflowStatusResponse": {
            "summary": "Workflow Status",
            "description": "Example workflow status response",
            "value": {
                "workflow_id": "wf_abc123",
                "status": "running",
                "workflow_type": "compliance",
                "created_at": "2025-01-01T12:00:00Z",
                "updated_at": "2025-01-01T12:05:00Z",
                "progress_percentage": 65.5,
                "current_agent": "debate_agent"
            }
        },
        "ErrorResponse": {
            "summary": "Error Response",
            "description": "Standard error response format",
            "value": {
                "error": "ValidationError",
                "message": "Invalid request data",
                "correlation_id": "abc123-def456",
                "error_code": "VALIDATION_ERROR",
                "details": {
                    "errors": [
                        {
                            "loc": ["body", "query"],
                            "msg": "field required",
                            "type": "value_error.missing"
                        }
                    ]
                },
                "timestamp": "2025-01-01T12:00:00Z"
            }
        },
        "HealthCheckResponse": {
            "summary": "Health Check",
            "description": "System health status",
            "value": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-01-01T12:00:00Z",
                "database_connected": True,
                "redis_connected": True,
                "services": {
                    "database": {"status": "healthy"},
                    "redis": {"status": "healthy"}
                },
                "uptime_seconds": 86400.5
            }
        }
    }
    
    # Add response headers documentation
    openapi_schema["components"]["headers"] = {
        "X-Correlation-ID": {
            "description": "Correlation ID for request tracking",
            "schema": {
                "type": "string",
                "example": "abc123-def456-ghi789"
            }
        },
        "X-RateLimit-Limit": {
            "description": "Maximum requests allowed per time window",
            "schema": {
                "type": "integer",
                "example": 60
            }
        },
        "X-RateLimit-Remaining": {
            "description": "Number of requests remaining in current window",
            "schema": {
                "type": "integer",
                "example": 45
            }
        },
        "X-RateLimit-Reset": {
            "description": "Unix timestamp when rate limit resets",
            "schema": {
                "type": "integer",
                "example": 1704100000
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_api_docs(app: FastAPI):
    """Setup enhanced API documentation"""
    app.openapi = lambda: custom_openapi(app)
    
    # Configure Swagger UI with enhanced settings
    app.swagger_ui_parameters = {
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
        "displayRequestDuration": True,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "syntaxHighlight.theme": "monokai",
        "tryItOutEnabled": True,
        "requestSnippetsEnabled": True,
        "requestSnippets": {
            "generators": {
                "curl_bash": {
                    "title": "cURL (bash)"
                },
                "curl_powershell": {
                    "title": "cURL (PowerShell)"
                },
                "python": {
                    "title": "Python"
                },
                "javascript": {
                    "title": "JavaScript"
                }
            }
        }
    }
    
    # Configure ReDoc
    app.redoc_ui_parameters = {
        "theme": {
            "colors": {
                "primary": {
                    "main": "#32329f"
                }
            }
        },
        "scrollYOffset": 0,
        "hideDownloadButton": False,
        "expandResponses": "200,201",
        "pathInMiddlePanel": True,
        "hideHostname": False,
        "requiredPropsFirst": True
    }


def generate_postman_collection(app: FastAPI) -> Dict[str, Any]:
    """
    Generate Postman collection from OpenAPI schema.
    
    Returns:
        Postman collection v2.1 format
    """
    openapi_schema = custom_openapi(app)
    
    collection = {
        "info": {
            "name": f"{settings.app_name} API",
            "description": openapi_schema.get("info", {}).get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "version": settings.app_version
        },
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{access_token}}",
                    "type": "string"
                }
            ]
        },
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8001",
                "type": "string"
            },
            {
                "key": "access_token",
                "value": "",
                "type": "string"
            }
        ],
        "item": []
    }
    
    # Group routes by tags
    routes_by_tag = {}
    for route in app.routes:
        if hasattr(route, "tags") and route.tags:
            for tag in route.tags:
                if tag not in routes_by_tag:
                    routes_by_tag[tag] = []
                routes_by_tag[tag].append(route)
    
    # Convert routes to Postman items
    for tag, routes in routes_by_tag.items():
        folder = {
            "name": tag.title(),
            "item": []
        }
        
        for route in routes:
            if hasattr(route, "methods") and hasattr(route, "path"):
                method = list(route.methods)[0] if route.methods else "GET"
                path = route.path
                
                item = {
                    "name": getattr(route, "summary", path) or path,
                    "request": {
                        "method": method,
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "url": {
                            "raw": "{{base_url}}" + path,
                            "host": ["{{base_url}}"],
                            "path": path.strip("/").split("/")
                        }
                    },
                    "response": []
                }
                
                # Add description if available
                if hasattr(route, "description"):
                    item["request"]["description"] = route.description
                
                folder["item"].append(item)
        
        if folder["item"]:
            collection["item"].append(folder)
    
    return collection


# Note: Postman collection endpoint is added in main.py
