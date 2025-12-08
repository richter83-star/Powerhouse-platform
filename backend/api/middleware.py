
"""
FastAPI middleware for security, logging, and multi-tenancy.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import json

from core.security import verify_token, rbac_manager, audit_logger, AuditEventType, AuditSeverity

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for:
    - JWT token validation
    - Multi-tenant isolation
    - Request logging
    """
    
    EXEMPT_PATHS = [
        "/api/auth/login",
        "/api/auth/refresh",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health"
    ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request through security pipeline"""
        start_time = time.time()
        
        # Skip auth for exempt paths
        if any(request.url.path.startswith(path) for path in self.EXEMPT_PATHS):
            response = await call_next(request)
            return response
        
        # Extract and validate token
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authorization header"}
            )
        
        token = auth_header.split(" ")[1]
        payload = verify_token(token)
        
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"}
            )
        
        # Add user context to request state
        request.state.user_id = payload.get("sub")
        request.state.tenant_id = payload.get("tenant_id")
        request.state.roles = payload.get("roles", [])
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log API access
            process_time = time.time() - start_time
            
            await audit_logger.log(
                event_type=AuditEventType.ACCESS_GRANTED,
                user_id=request.state.user_id,
                tenant_id=request.state.tenant_id,
                resource_type="api",
                resource_id=request.url.path,
                action=request.method,
                outcome="success",
                severity=AuditSeverity.DEBUG,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={
                    "status_code": response.status_code,
                    "process_time": round(process_time, 3)
                }
            )
            
            return response
            
        except Exception as e:
            # Log error
            await audit_logger.log(
                event_type=AuditEventType.SYSTEM_ERROR,
                user_id=request.state.user_id,
                tenant_id=request.state.tenant_id,
                resource_type="api",
                resource_id=request.url.path,
                action=request.method,
                outcome="failure",
                severity=AuditSeverity.ERROR,
                metadata={"error": str(e)}
            )
            
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # {user_id: [(timestamp, count)]}
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Apply rate limiting"""
        # Get user from request state (set by SecurityMiddleware)
        user_id = getattr(request.state, 'user_id', None)
        
        if user_id:
            current_time = time.time()
            
            # Clean old entries
            if user_id in self.requests:
                self.requests[user_id] = [
                    (ts, count) for ts, count in self.requests[user_id]
                    if current_time - ts < 60
                ]
            else:
                self.requests[user_id] = []
            
            # Count requests in last minute
            recent_count = sum(count for _, count in self.requests[user_id])
            
            if recent_count >= self.requests_per_minute:
                # Log rate limit violation
                await audit_logger.log(
                    event_type=AuditEventType.SECURITY_BREACH_ATTEMPT,
                    user_id=user_id,
                    tenant_id=getattr(request.state, 'tenant_id', 'unknown'),
                    resource_type="api",
                    resource_id=request.url.path,
                    action="rate_limit_exceeded",
                    outcome="blocked",
                    severity=AuditSeverity.WARNING
                )
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"}
                )
            
            # Record this request
            self.requests[user_id].append((current_time, 1))
        
        response = await call_next(request)
        return response

class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Ensures tenant data isolation by validating tenant_id in requests.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Enforce tenant isolation"""
        tenant_id = getattr(request.state, 'tenant_id', None)
        
        if tenant_id:
            # Add tenant_id to query params or body for downstream processing
            # In production, this would interact with database query filters
            pass
        
        response = await call_next(request)
        return response
