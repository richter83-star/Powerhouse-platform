"""
Rate limiting configuration for security.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SecurityRateLimitConfig:
    """
    Security-focused rate limiting configuration.
    
    Different limits for different endpoint types to prevent abuse.
    """
    # Authentication endpoints - very strict
    auth_max_requests: int = 5  # 5 attempts per window
    auth_time_window: int = 300  # 5 minutes
    
    # Password reset - very strict
    password_reset_max_requests: int = 3  # 3 attempts per window
    password_reset_time_window: int = 3600  # 1 hour
    
    # API endpoints - standard
    api_max_requests: int = 60  # 60 requests per window
    api_time_window: int = 60  # 1 minute
    
    # Workflow endpoints - moderate
    workflow_max_requests: int = 10  # 10 workflows per window
    workflow_time_window: int = 300  # 5 minutes
    
    # File upload - strict
    upload_max_requests: int = 20  # 20 uploads per window
    upload_time_window: int = 3600  # 1 hour
    
    # IP-based limits (for unauthenticated requests)
    ip_max_requests: int = 100  # 100 requests per window
    ip_time_window: int = 60  # 1 minute


# Global security rate limit configuration
security_rate_limits = SecurityRateLimitConfig()

