"""
Retry Handler with Exponential Backoff

Provides automatic retry with exponential backoff for failed operations.
"""

import logging
import asyncio
import random
from typing import Callable, Any, Optional, TypeVar, List
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Retry configuration"""
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple = (Exception,)
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to delays
            retryable_exceptions: Tuple of exception types to retry
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions


def retry_with_backoff(
    func: Optional[Callable] = None,
    config: Optional[RetryConfig] = None
):
    """
    Decorator for retry with exponential backoff.
    
    Usage:
        @retry_with_backoff(config=RetryConfig(max_attempts=5))
        def my_function():
            ...
    """
    retry_config = config or RetryConfig()
    
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, retry_config.max_attempts + 1):
                try:
                    return f(*args, **kwargs)
                except retry_config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == retry_config.max_attempts:
                        logger.error(
                            f"Function {f.__name__} failed after {retry_config.max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        retry_config.initial_delay * (retry_config.exponential_base ** (attempt - 1)),
                        retry_config.max_delay
                    )
                    
                    # Add jitter
                    if retry_config.jitter:
                        jitter_amount = delay * 0.1 * random.random()
                        delay = delay + jitter_amount
                    
                    logger.warning(
                        f"Function {f.__name__} failed (attempt {attempt}/{retry_config.max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
        
        @wraps(f)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, retry_config.max_attempts + 1):
                try:
                    return await f(*args, **kwargs)
                except retry_config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == retry_config.max_attempts:
                        logger.error(
                            f"Function {f.__name__} failed after {retry_config.max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay
                    delay = min(
                        retry_config.initial_delay * (retry_config.exponential_base ** (attempt - 1)),
                        retry_config.max_delay
                    )
                    
                    if retry_config.jitter:
                        jitter_amount = delay * 0.1 * random.random()
                        delay = delay + jitter_amount
                    
                    logger.warning(
                        f"Function {f.__name__} failed (attempt {attempt}/{retry_config.max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    await asyncio.sleep(delay)
            
            if last_exception:
                raise last_exception
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(f):
            return async_wrapper
        else:
            return sync_wrapper
    
    # Support both @retry_with_backoff and @retry_with_backoff(config=...)
    if func is None:
        return decorator
    else:
        return decorator(func)


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,)
):
    """
    Simplified retry decorator.
    
    Usage:
        @retry(max_attempts=5, initial_delay=2.0)
        def my_function():
            ...
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions
    )
    return retry_with_backoff(config=config)


async def retry_async(
    func: Callable,
    *args,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Retry async function with exponential backoff.
    
    Usage:
        result = await retry_async(my_async_function, arg1, arg2, max_attempts=5)
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions
    )
    
    last_exception = None
    
    for attempt in range(1, config.max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt == config.max_attempts:
                logger.error(
                    f"Function {func.__name__} failed after {config.max_attempts} attempts: {e}"
                )
                raise
            
            delay = min(
                config.initial_delay * (config.exponential_base ** (attempt - 1)),
                config.max_delay
            )
            
            if config.jitter:
                jitter_amount = delay * 0.1 * random.random()
                delay = delay + jitter_amount
            
            logger.warning(
                f"Function {func.__name__} failed (attempt {attempt}/{config.max_attempts}): {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            
            await asyncio.sleep(delay)
    
    if last_exception:
        raise last_exception

