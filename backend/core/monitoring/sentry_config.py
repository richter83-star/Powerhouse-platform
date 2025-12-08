"""
Sentry configuration for error tracking and monitoring.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_sentry_initialized = False


def init_sentry(dsn: Optional[str] = None, environment: Optional[str] = None, release: Optional[str] = None):
    """
    Initialize Sentry for error tracking.
    
    Args:
        dsn: Sentry DSN (Data Source Name)
        environment: Environment name (e.g., 'production', 'staging', 'development')
        release: Release version
    """
    global _sentry_initialized
    
    if _sentry_initialized:
        return
    
    if not dsn:
        logger.info("Sentry DSN not provided, skipping Sentry initialization")
        return
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        
        sentry_sdk.init(
            dsn=dsn,
            environment=environment or "development",
            release=release,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
            traces_sample_rate=0.1,  # 10% of transactions
            # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions
            profiles_sample_rate=0.1,  # 10% of sampled transactions
            # Enable sending of PII data
            send_default_pii=True,
            # Set before_send to filter sensitive data
            before_send=lambda event, hint: filter_sensitive_data(event, hint),
        )
        
        _sentry_initialized = True
        logger.info("Sentry initialized successfully")
    except ImportError:
        logger.warning("sentry-sdk not installed. Install with: pip install sentry-sdk")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def filter_sensitive_data(event, hint):
    """
    Filter sensitive data from Sentry events.
    
    Args:
        event: Sentry event
        hint: Event hint
        
    Returns:
        Filtered event or None to drop the event
    """
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        sensitive_headers = ['authorization', 'x-api-key', 'cookie', 'x-auth-token']
        for header in sensitive_headers:
            event['request']['headers'].pop(header, None)
    
    # Remove sensitive data from extra context
    if 'extra' in event:
        sensitive_keys = ['password', 'password_hash', 'secret', 'token', 'api_key']
        for key in sensitive_keys:
            event['extra'].pop(key, None)
    
    return event


def capture_exception(exception: Exception, **kwargs):
    """
    Capture an exception in Sentry.
    
    Args:
        exception: Exception to capture
        **kwargs: Additional context
    """
    if not _sentry_initialized:
        return
    
    try:
        import sentry_sdk
        sentry_sdk.capture_exception(exception, **kwargs)
    except Exception as e:
        logger.warning(f"Failed to capture exception in Sentry: {e}")


def capture_message(message: str, level: str = "info", **kwargs):
    """
    Capture a message in Sentry.
    
    Args:
        message: Message to capture
        level: Message level (info, warning, error, fatal)
        **kwargs: Additional context
    """
    if not _sentry_initialized:
        return
    
    try:
        import sentry_sdk
        sentry_sdk.capture_message(message, level=level, **kwargs)
    except Exception as e:
        logger.warning(f"Failed to capture message in Sentry: {e}")

