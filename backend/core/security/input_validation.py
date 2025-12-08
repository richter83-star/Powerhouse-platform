"""
Input validation and sanitization utilities.
"""
import re
import html
import logging
from typing import Any, Optional, List
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)


class InputSanitizer:
    """
    Input sanitization utilities to prevent injection attacks.
    """
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"('|(\\')|(;)|(\|)|(\*))",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]<>]",
        r"\b(cat|ls|pwd|whoami|id|uname|ps|kill|rm|mv|cp)\b",
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, allow_html: bool = False) -> str:
        """
        Sanitize string input.
        
        Args:
            value: Input string
            allow_html: If True, allow HTML (but still escape dangerous tags)
        
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return str(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # HTML escape if not allowing HTML
        if not allow_html:
            value = html.escape(value)
        
        # Remove dangerous patterns
        for pattern in cls.XSS_PATTERNS:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
        
        return value.strip()
    
    @classmethod
    def validate_no_sql_injection(cls, value: str) -> bool:
        """
        Check if string contains SQL injection patterns.
        
        Args:
            value: String to check
        
        Returns:
            True if safe, False if suspicious
        """
        if not isinstance(value, str):
            return True
        
        value_upper = value.upper()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {value[:50]}")
                return False
        
        return True
    
    @classmethod
    def validate_no_xss(cls, value: str) -> bool:
        """
        Check if string contains XSS patterns.
        
        Args:
            value: String to check
        
        Returns:
            True if safe, False if suspicious
        """
        if not isinstance(value, str):
            return True
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                logger.warning(f"Potential XSS detected: {value[:50]}")
                return False
        
        return True
    
    @classmethod
    def validate_no_command_injection(cls, value: str) -> bool:
        """
        Check if string contains command injection patterns.
        
        Args:
            value: String to check
        
        Returns:
            True if safe, False if suspicious
        """
        if not isinstance(value, str):
            return True
        
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential command injection detected: {value[:50]}")
                return False
        
        return True
    
    @classmethod
    def sanitize_dict(cls, data: dict, allow_html: bool = False) -> dict:
        """
        Recursively sanitize dictionary values.
        
        Args:
            data: Dictionary to sanitize
            allow_html: If True, allow HTML in strings
        
        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_string(value, allow_html)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value, allow_html)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize_string(item, allow_html) if isinstance(item, str)
                    else cls.sanitize_dict(item, allow_html) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str, allowed_schemes: List[str] = None) -> bool:
    """
    Validate URL format and scheme.
    
    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes (default: ['http', 'https'])
    
    Returns:
        True if valid, False otherwise
    """
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, url):
        return False
    
    scheme = url.split('://')[0]
    return scheme in allowed_schemes


class SecureString(BaseModel):
    """
    Pydantic model for secure string validation.
    """
    value: str
    
    @validator('value')
    def validate_secure(cls, v):
        """Validate string is secure."""
        if not InputSanitizer.validate_no_sql_injection(v):
            raise ValueError("Potential SQL injection detected")
        if not InputSanitizer.validate_no_xss(v):
            raise ValueError("Potential XSS detected")
        if not InputSanitizer.validate_no_command_injection(v):
            raise ValueError("Potential command injection detected")
        return InputSanitizer.sanitize_string(v)

