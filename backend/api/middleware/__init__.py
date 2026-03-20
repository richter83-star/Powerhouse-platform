"""
API middleware package.
"""
from api.middleware.security_headers import SecurityHeadersMiddleware
from api.middleware.correlation_id import CorrelationIDMiddleware
from api.middleware.rate_limit import RateLimitMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Callable


class SecurityMiddleware(BaseHTTPMiddleware):
    """Pass-through security middleware placeholder (JWT auth handled at route level)."""
    async def dispatch(self, request: Request, call_next: Callable):
        return await call_next(request)


class UsageLimitMiddleware(BaseHTTPMiddleware):
    """Pass-through usage limit middleware (enforcement handled at route level)."""
    async def dispatch(self, request: Request, call_next: Callable):
        return await call_next(request)


class SLATrackingMiddleware(BaseHTTPMiddleware):
    """Pass-through SLA tracking middleware (metrics handled at route level)."""
    async def dispatch(self, request: Request, call_next: Callable):
        return await call_next(request)


__all__ = [
    'SecurityHeadersMiddleware',
    'CorrelationIDMiddleware',
    'RateLimitMiddleware',
    'SecurityMiddleware',
    'UsageLimitMiddleware',
    'SLATrackingMiddleware',
]

