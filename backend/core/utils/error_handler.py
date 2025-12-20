"""
Standardized error handling utilities.

Provides consistent error responses with correlation IDs and error categorization.
"""

import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from http import HTTPStatus

from api.models import ErrorResponse

logger = logging.getLogger(__name__)


class ErrorCategory:
    """Error categories for better error handling."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    RATE_LIMIT = "rate_limit"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    INTERNAL = "internal"


def get_correlation_id(request: Request) -> str:
    """
    Get or create correlation ID for a request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Correlation ID string
    """
    # Check if correlation ID already exists in request state
    if hasattr(request.state, 'correlation_id') and request.state.correlation_id:
        return request.state.correlation_id
    
    # Check if provided in headers
    correlation_id = request.headers.get('X-Correlation-ID') or request.headers.get('X-Request-ID')
    
    if not correlation_id:
        # Generate new correlation ID
        correlation_id = str(uuid.uuid4())
    
    # Store in request state
    request.state.correlation_id = correlation_id
    
    return correlation_id


def create_error_response(
    error_type: str,
    message: str,
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
    details: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    error_code: Optional[str] = None,
    category: Optional[str] = None
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        error_type: Error type (e.g., "ValidationError", "AuthenticationError")
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        correlation_id: Correlation ID for request tracking
        error_code: Machine-readable error code
        category: Error category (for filtering/monitoring)
        
    Returns:
        JSONResponse with standardized error format
    """
    error_code = error_code or error_type.upper().replace("ERROR", "").replace(" ", "_")
    
    error_response = ErrorResponse(
        error=error_type,
        message=message,
        details=details or {},
        correlation_id=correlation_id,
        error_code=error_code,
        timestamp=datetime.utcnow()
    )
    
    # Add category to details if provided
    if category:
        error_response.details["category"] = category
    
    # Use mode='json' to ensure datetime is properly serialized
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(mode='json')
    )


def handle_validation_error(
    errors: list,
    correlation_id: Optional[str] = None
) -> JSONResponse:
    """Create standardized validation error response."""
    return create_error_response(
        error_type="ValidationError",
        message="Invalid request data",
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        details={"errors": errors},
        correlation_id=correlation_id,
        error_code="VALIDATION_ERROR",
        category=ErrorCategory.VALIDATION
    )


def handle_authentication_error(
    message: str = "Authentication required",
    correlation_id: Optional[str] = None
) -> JSONResponse:
    """Create standardized authentication error response."""
    return create_error_response(
        error_type="AuthenticationError",
        message=message,
        status_code=HTTPStatus.UNAUTHORIZED,
        correlation_id=correlation_id,
        error_code="AUTH_REQUIRED",
        category=ErrorCategory.AUTHENTICATION
    )


def handle_authorization_error(
    message: str = "Insufficient permissions",
    correlation_id: Optional[str] = None
) -> JSONResponse:
    """Create standardized authorization error response."""
    return create_error_response(
        error_type="AuthorizationError",
        message=message,
        status_code=HTTPStatus.FORBIDDEN,
        correlation_id=correlation_id,
        error_code="FORBIDDEN",
        category=ErrorCategory.AUTHORIZATION
    )


def handle_not_found_error(
    resource_type: str,
    resource_id: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> JSONResponse:
    """Create standardized not found error response."""
    message = f"{resource_type} not found"
    if resource_id:
        message = f"{resource_type} with ID '{resource_id}' not found"
    
    return create_error_response(
        error_type="NotFoundError",
        message=message,
        status_code=HTTPStatus.NOT_FOUND,
        details={"resource_type": resource_type, "resource_id": resource_id},
        correlation_id=correlation_id,
        error_code="NOT_FOUND",
        category=ErrorCategory.NOT_FOUND
    )


def handle_rate_limit_error(
    retry_after: Optional[int] = None,
    correlation_id: Optional[str] = None
) -> JSONResponse:
    """Create standardized rate limit error response."""
    message = "Rate limit exceeded. Please try again later."
    details = {}
    if retry_after:
        details["retry_after_seconds"] = retry_after
        message = f"Rate limit exceeded. Please try again after {retry_after} seconds."
    
    response = create_error_response(
        error_type="RateLimitError",
        message=message,
        status_code=HTTPStatus.TOO_MANY_REQUESTS,
        details=details,
        correlation_id=correlation_id,
        error_code="RATE_LIMIT_EXCEEDED",
        category=ErrorCategory.RATE_LIMIT
    )
    
    # Add Retry-After header if provided
    if retry_after:
        response.headers["Retry-After"] = str(retry_after)
    
    return response


def handle_internal_error(
    error: Exception,
    correlation_id: Optional[str] = None,
    error_id: Optional[str] = None,
    debug: bool = False
) -> JSONResponse:
    """Create standardized internal server error response."""
    error_id = error_id or str(uuid.uuid4())
    
    details = {"error_id": error_id}
    if debug:
        details.update({
            "error": str(error),
            "type": type(error).__name__
        })
    
    return create_error_response(
        error_type="InternalServerError",
        message="An unexpected error occurred",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        details=details,
        correlation_id=correlation_id,
        error_code="INTERNAL_ERROR",
        category=ErrorCategory.INTERNAL
    )

