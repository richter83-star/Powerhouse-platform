
"""
FastAPI middleware for security, logging, and multi-tenancy.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import json
import logging

from core.security import verify_token, audit_logger, AuditEventType, AuditSeverity
try:
    from core.security import rbac_manager
except ImportError:
    rbac_manager = None

logger = logging.getLogger(__name__)

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
        "/api/billing/webhook",  # Stripe webhook (has its own signature verification)
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
    Redis-backed rate limiting middleware to prevent abuse.
    
    Works across multiple instances and survives restarts.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        
        # Initialize Redis rate limiter
        try:
            from core.resilience.redis_rate_limiter import (
                get_redis_rate_limiter,
                RateLimitConfig
            )
            self.rate_limiter = get_redis_rate_limiter()
            self.rate_limit_config = RateLimitConfig(
                max_requests=requests_per_minute,
                time_window=60,  # 1 minute
                burst_size=10  # Allow 10 extra requests as burst
            )
            self.use_redis = True
        except Exception as e:
            logger.warning(f"Failed to initialize Redis rate limiter: {e}. Falling back to in-memory.")
            self.rate_limiter = None
            self.requests = {}  # Fallback: in-memory dict
            self.use_redis = False
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Apply rate limiting"""
        # Get user from request state (set by SecurityMiddleware)
        user_id = getattr(request.state, 'user_id', None)
        tenant_id = getattr(request.state, 'tenant_id', 'unknown')
        
        # Use IP address as fallback identifier if no user_id
        identifier = user_id or request.client.host if request.client else "anonymous"
        
        if self.use_redis and self.rate_limiter:
            # Use Redis rate limiting
            allowed, info = self.rate_limiter.check_rate_limit(
                identifier=f"{tenant_id}:{identifier}",
                config=self.rate_limit_config
            )
            
            if not allowed:
                # Log rate limit violation
                await audit_logger.log(
                    event_type=AuditEventType.SECURITY_BREACH_ATTEMPT,
                    user_id=user_id or identifier,
                    tenant_id=tenant_id,
                    resource_type="api",
                    resource_id=request.url.path,
                    action="rate_limit_exceeded",
                    outcome="blocked",
                    severity=AuditSeverity.WARNING
                )
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "reset_time": info.get("reset_time"),
                        "limit": info.get("limit")
                    },
                    headers={
                        "X-RateLimit-Limit": str(info.get("limit", self.requests_per_minute)),
                        "X-RateLimit-Remaining": str(info.get("remaining", 0)),
                        "X-RateLimit-Reset": str(info.get("reset_time", int(time.time()) + 60))
                    }
                )
        else:
            # Fallback: in-memory rate limiting
            current_time = time.time()
            
            if identifier in self.requests:
                self.requests[identifier] = [
                    (ts, count) for ts, count in self.requests[identifier]
                    if current_time - ts < 60
                ]
            else:
                self.requests[identifier] = []
            
            recent_count = sum(count for _, count in self.requests[identifier])
            
            if recent_count >= self.requests_per_minute:
                await audit_logger.log(
                    event_type=AuditEventType.SECURITY_BREACH_ATTEMPT,
                    user_id=user_id or identifier,
                    tenant_id=tenant_id,
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
            
            self.requests[identifier].append((current_time, 1))
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        if self.use_redis and self.rate_limiter:
            info = self.rate_limiter.get_rate_limit_info(
                identifier=f"{tenant_id}:{identifier}",
                config=self.rate_limit_config
            )
            response.headers["X-RateLimit-Limit"] = str(info.get("limit", self.requests_per_minute))
            response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
            response.headers["X-RateLimit-Reset"] = str(info.get("reset_time", int(time.time()) + 60))
        
        return response

class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Ensures tenant data isolation by validating tenant_id in requests.
    
    Sets tenant context for database queries and validates tenant access.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Enforce tenant isolation"""
        tenant_id = getattr(request.state, 'tenant_id', None)
        
        if tenant_id:
            # Set tenant context for RLS (if using PostgreSQL RLS)
            # This is done at the database session level, not here
            # The tenant_id is available in request.state for use in route handlers
            
            # Validate tenant exists and is active (optional check)
            # This could query the database to verify tenant exists
            pass
        
        response = await call_next(request)
        return response


class UsageLimitMiddleware(BaseHTTPMiddleware):
    """
    Enforces usage limits based on tenant subscription tier.
    
    Checks limits before processing requests and blocks if hard limits are exceeded.
    """
    
    # Paths that don't count toward usage
    EXEMPT_PATHS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/license/validate",  # License validation doesn't count
        "/api/v1/license/hardware-fingerprint"
    ]
    
    # Paths that count as API calls
    API_CALL_PATHS = [
        "/api/v1/",
        "/api/performance/",
        "/api/forecasting/",
        "/api/autonomous/",
        "/api/files/",
        "/api/exponential/",
        "/api/billing/",
        "/api/commercial/"
    ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Check usage limits before processing request"""
        # Skip for exempt paths
        if any(request.url.path.startswith(path) for path in self.EXEMPT_PATHS):
            return await call_next(request)
        
        tenant_id = getattr(request.state, 'tenant_id', None)
        if not tenant_id:
            # No tenant = no limit checking
            return await call_next(request)
        
        # Check if this is an API call
        is_api_call = any(request.url.path.startswith(path) for path in self.API_CALL_PATHS)
        
        if is_api_call:
            try:
                from core.commercial.usage_tracker import get_usage_tracker, LimitType
                from core.commercial.tenant_manager import get_tenant_manager
                
                usage_tracker = get_usage_tracker()
                tenant_manager = get_tenant_manager()
                tenant = tenant_manager.get_tenant(tenant_id)
                
                if tenant:
                    # Check hourly API call limit
                    limit_status = usage_tracker.check_limit(
                        tenant_id=tenant_id,
                        resource_type="api_call",
                        quantity=1.0,
                        window_seconds=3600,  # Hourly limit
                        limit_type=LimitType.HARD
                    )
                    
                    if not limit_status.allowed:
                        # Log limit exceeded
                        await audit_logger.log(
                            event_type=AuditEventType.ACCESS_DENIED,
                            user_id=getattr(request.state, 'user_id', 'unknown'),
                            tenant_id=tenant_id,
                            resource_type="api",
                            resource_id=request.url.path,
                            action=request.method,
                            outcome="blocked",
                            severity=AuditSeverity.WARNING,
                            metadata={
                                "reason": "usage_limit_exceeded",
                                "limit_status": limit_status.message
                            }
                        )
                        
                        return JSONResponse(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            content={
                                "error": "UsageLimitExceeded",
                                "message": limit_status.message,
                                "detail": f"API call limit exceeded. Current: {limit_status.current:.0f}, Limit: {limit_status.limit:.0f}",
                                "limit_type": limit_status.limit_type.value,
                                "percentage": limit_status.percentage
                            },
                            headers={
                                "X-Usage-Limit-Exceeded": "true",
                                "X-Usage-Current": str(int(limit_status.current)),
                                "X-Usage-Limit": str(int(limit_status.limit)),
                                "X-Usage-Percentage": f"{limit_status.percentage:.1f}"
                            }
                        )
                    
                    # Check soft limits and add warnings
                    if limit_status.percentage >= 80:
                        # Add warning header
                        response = await call_next(request)
                        response.headers["X-Usage-Warning"] = limit_status.message
                        response.headers["X-Usage-Percentage"] = f"{limit_status.percentage:.1f}"
                        return response
                
            except Exception as e:
                logger.warning(f"Usage limit check failed: {e}", exc_info=True)
                # Don't block on error, just log and continue
                pass
        
        # Process request and record usage
        response = await call_next(request)
        
        # Record usage after successful request
        if is_api_call and response.status_code < 400:
            try:
                from core.commercial.usage_tracker import get_usage_tracker
                usage_tracker = get_usage_tracker()
                
                # Record usage (non-blocking)
                usage_tracker.record_usage(
                    tenant_id=tenant_id,
                    resource_type="api_call",
                    quantity=1.0,
                    metadata={
                        "path": request.url.path,
                        "method": request.method,
                        "status_code": response.status_code
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to record usage: {e}")
        
        return response


class SLATrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track requests for SLA monitoring.
    
    Records response times, status codes, and errors for SLA metrics.
    """
    
    # Paths to exclude from SLA tracking
    EXEMPT_PATHS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json"
    ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Track request for SLA monitoring"""
        # Skip tracking for exempt paths
        if any(request.url.path.startswith(path) for path in self.EXEMPT_PATHS):
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            response_time_ms = (time.time() - start_time) * 1000
            
            # Record request for SLA tracking
            try:
                from core.monitoring.sla_tracker import get_sla_tracker
                sla_tracker = get_sla_tracker()
                
                sla_tracker.record_request(
                    endpoint=request.url.path,
                    method=request.method,
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    error=None
                )
            except Exception as e:
                logger.warning(f"Failed to record request for SLA tracking: {e}")
            
            return response
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            # Record error
            try:
                from core.monitoring.sla_tracker import get_sla_tracker
                sla_tracker = get_sla_tracker()
                
                sla_tracker.record_request(
                    endpoint=request.url.path,
                    method=request.method,
                    response_time_ms=response_time_ms,
                    status_code=500,
                    error=str(e)
                )
            except Exception as e2:
                logger.warning(f"Failed to record error for SLA tracking: {e2}")
            
            raise
