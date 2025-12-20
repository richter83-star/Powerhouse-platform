"""
Core utilities package.

This package contains utility modules for error handling and other common functionality.
"""

from .error_handler import (
    get_correlation_id,
    create_error_response,
    handle_validation_error,
    handle_authentication_error,
    handle_authorization_error,
    handle_not_found_error,
    handle_rate_limit_error,
    handle_internal_error,
    ErrorCategory
)

__all__ = [
    "get_correlation_id",
    "create_error_response",
    "handle_validation_error",
    "handle_authentication_error",
    "handle_authorization_error",
    "handle_not_found_error",
    "handle_rate_limit_error",
    "handle_internal_error",
    "ErrorCategory",
]

