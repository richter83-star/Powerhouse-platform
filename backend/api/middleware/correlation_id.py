"""
Correlation ID middleware for request tracking.
"""
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

logger = logging.getLogger(__name__)

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation ID to all requests.
    
    Generates a unique correlation ID for each request and adds it to:
    - Request state (for use in handlers)
    - Response headers
    - Log records
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add to request state
        request.state.correlation_id = correlation_id
        
        # Add to logging context
        import logging
        for handler in logging.root.handlers:
            # Set correlation ID in current context
            old_filter = getattr(handler, 'filters', [])
            for filter_obj in old_filter:
                if hasattr(filter_obj, 'correlation_id'):
                    filter_obj.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        
        return response


def get_correlation_id(request: Request) -> str:
    """Get correlation ID from request."""
    return getattr(request.state, 'correlation_id', None)

