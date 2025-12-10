"""
Environment variable validation utility.

Validates that all required environment variables are set and have valid values.
"""

import os
import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when environment variable validation fails."""
    pass


class EnvironmentValidator:
    """Validates environment variables on application startup."""
    
    # Required environment variables that must be set
    REQUIRED_VARS = [
        ("SECRET_KEY", str, "Secret key for JWT encoding (min 32 characters)"),
        ("JWT_SECRET_KEY", str, "JWT secret key (min 32 characters)"),
    ]
    
    # Optional but recommended variables
    RECOMMENDED_VARS = [
        ("DATABASE_URL", str, "Database connection string"),
        ("REDIS_URL", str, "Redis connection URL"),
        ("EMAIL_PROVIDER", str, "Email provider (sendgrid, aws_ses, smtp)"),
    ]
    
    # Variables that should have secure values (not defaults)
    SECURITY_VARS = [
        ("SECRET_KEY", "your-secret-key-change-in-production"),
        ("JWT_SECRET_KEY", "your-jwt-secret-key-change-in-production"),
        ("LICENSE_SECRET_KEY", "your-license-secret-key-change-in-production"),
        ("DB_PASSWORD", "postgres"),
    ]
    
    @classmethod
    def validate_min_length(cls, value: str, min_length: int, var_name: str) -> bool:
        """Validate that a string value meets minimum length requirement."""
        if len(value) < min_length:
            raise ValidationError(
                f"{var_name} must be at least {min_length} characters long. "
                f"Current length: {len(value)}"
            )
        return True
    
    @classmethod
    def validate_secret_key(cls, value: str, var_name: str) -> bool:
        """Validate that a secret key is secure."""
        if len(value) < 32:
            raise ValidationError(
                f"{var_name} must be at least 32 characters long for security. "
                f"Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        
        # Check for common insecure patterns
        insecure_patterns = [
            "change-in-production",
            "your-",
            "default",
            "test",
            "demo",
            "example",
        ]
        
        value_lower = value.lower()
        for pattern in insecure_patterns:
            if pattern in value_lower:
                raise ValidationError(
                    f"{var_name} appears to contain insecure default value. "
                    f"Please use a securely generated random string."
                )
        
        return True
    
    @classmethod
    def validate_url(cls, value: str, var_name: str, schemes: Optional[List[str]] = None) -> bool:
        """Validate that a value is a valid URL."""
        if schemes is None:
            schemes = ["http", "https", "postgresql", "redis"]
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^(' + '|'.join(schemes) + r')://'  # scheme
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        if not url_pattern.match(value):
            raise ValidationError(
                f"{var_name} must be a valid URL. "
                f"Accepted schemes: {', '.join(schemes)}"
            )
        
        return True
    
    @classmethod
    def validate_email_provider(cls, value: str) -> bool:
        """Validate email provider value."""
        valid_providers = ["sendgrid", "aws_ses", "smtp"]
        if value not in valid_providers:
            raise ValidationError(
                f"EMAIL_PROVIDER must be one of: {', '.join(valid_providers)}. "
                f"Got: {value}"
            )
        return True
    
    @classmethod
    def validate_all(cls, fail_on_missing_recommended: bool = False) -> Tuple[bool, List[str]]:
        """
        Validate all environment variables.
        
        Args:
            fail_on_missing_recommended: If True, fail if recommended vars are missing
        
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        errors = []
        warnings = []
        
        # Check required variables
        for var_name, var_type, description in cls.REQUIRED_VARS:
            value = os.getenv(var_name)
            if not value:
                errors.append(
                    f"Required environment variable {var_name} is not set. "
                    f"{description}"
                )
                continue
            
            # Type-specific validation
            try:
                if var_type == str:
                    # For SECRET_KEY and JWT_SECRET_KEY, validate security
                    if "SECRET_KEY" in var_name:
                        cls.validate_secret_key(value, var_name)
                    elif "URL" in var_name:
                        cls.validate_url(value, var_name)
            except ValidationError as e:
                errors.append(str(e))
        
        # Check recommended variables
        for var_name, var_type, description in cls.RECOMMENDED_VARS:
            value = os.getenv(var_name)
            if not value:
                if fail_on_missing_recommended:
                    errors.append(
                        f"Recommended environment variable {var_name} is not set. "
                        f"{description}"
                    )
                else:
                    warnings.append(
                        f"Recommended environment variable {var_name} is not set. "
                        f"{description}"
                    )
        
        # Check for insecure default values
        for var_name, default_value in cls.SECURITY_VARS:
            value = os.getenv(var_name)
            if value and value == default_value:
                errors.append(
                    f"Security risk: {var_name} is set to default value. "
                    f"Please change it to a secure value."
                )
        
        # Validate email provider if set
        email_provider = os.getenv("EMAIL_PROVIDER")
        if email_provider:
            try:
                cls.validate_email_provider(email_provider)
            except ValidationError as e:
                errors.append(str(e))
        
        # Validate database URL if set
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            try:
                cls.validate_url(database_url, "DATABASE_URL", ["postgresql", "postgres"])
            except ValidationError as e:
                errors.append(str(e))
        
        # Validate Redis URL if set
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                cls.validate_url(redis_url, "REDIS_URL", ["redis", "rediss"])
            except ValidationError as e:
                errors.append(str(e))
        
        return len(errors) == 0, errors, warnings
    
    @classmethod
    def get_validation_report(cls) -> str:
        """Generate a human-readable validation report."""
        is_valid, errors, warnings = cls.validate_all()
        
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("Environment Variable Validation Report")
        report_lines.append("=" * 70)
        
        if is_valid and not warnings:
            report_lines.append("✅ All environment variables are valid!")
        else:
            if errors:
                report_lines.append("\n❌ ERRORS (must be fixed):")
                report_lines.append("-" * 70)
                for error in errors:
                    report_lines.append(f"  • {error}")
            
            if warnings:
                report_lines.append("\n⚠️  WARNINGS (recommended to fix):")
                report_lines.append("-" * 70)
                for warning in warnings:
                    report_lines.append(f"  • {warning}")
        
        report_lines.append("\n" + "=" * 70)
        
        return "\n".join(report_lines)


def validate_environment(fail_on_missing_recommended: bool = False) -> None:
    """
    Validate environment variables and raise exception if invalid.
    
    Args:
        fail_on_missing_recommended: If True, fail if recommended vars are missing
    
    Raises:
        ValidationError: If validation fails
    """
    is_valid, errors, warnings = EnvironmentValidator.validate_all(
        fail_on_missing_recommended
    )
    
    # Log warnings
    for warning in warnings:
        logger.warning(f"Environment validation warning: {warning}")
    
    # Raise exception if there are errors
    if not is_valid:
        error_msg = "Environment variable validation failed:\n" + "\n".join(f"  • {e}" for e in errors)
        logger.error(error_msg)
        raise ValidationError(error_msg)

