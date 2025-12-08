
"""
Rate Limiting and Circuit Breaker
Provides request rate limiting and circuit breaker patterns for resilient operations.
"""

import time
import logging
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
from functools import wraps
import threading

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    max_requests: int  # Maximum requests
    time_window: int  # Time window in seconds
    burst_size: int = 0  # Burst capacity (0 = no burst)


class RateLimiter:
    """
    Token bucket rate limiter with burst support.
    Thread-safe and efficient for high-throughput scenarios.
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.max_requests
        self.last_refill = time.time()
        self._lock = threading.Lock()
        
        # Calculate refill rate (tokens per second)
        self.refill_rate = config.max_requests / config.time_window
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Calculate tokens to add
        tokens_to_add = elapsed * self.refill_rate
        
        # Cap at max_requests (or burst_size if configured)
        max_tokens = self.config.max_requests + self.config.burst_size
        self.tokens = min(self.tokens + tokens_to_add, max_tokens)
        
        self.last_refill = now
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False otherwise
        """
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def wait_for_token(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Wait for tokens to become available.
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait (None = wait indefinitely)
            
        Returns:
            True if tokens acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.try_acquire(tokens):
                return True
            
            if timeout and (time.time() - start_time) >= timeout:
                return False
            
            # Sleep for a short time before retrying
            time.sleep(0.01)
    
    def get_available_tokens(self) -> float:
        """Get current available tokens"""
        with self._lock:
            self._refill()
            return self.tokens


class RateLimitStore:
    """
    Store for managing multiple rate limiters.
    Supports per-user, per-endpoint, and global rate limiting.
    """
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self._lock = threading.Lock()
    
    def get_or_create_limiter(self, key: str, config: RateLimitConfig) -> RateLimiter:
        """Get or create a rate limiter for a key"""
        with self._lock:
            if key not in self.limiters:
                self.limiters[key] = RateLimiter(config)
            return self.limiters[key]
    
    def check_rate_limit(self, key: str, config: RateLimitConfig, tokens: int = 1) -> bool:
        """Check if request is within rate limit"""
        limiter = self.get_or_create_limiter(key, config)
        return limiter.try_acquire(tokens)


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes before closing from half-open
    timeout: int = 60  # Timeout in seconds before trying half-open
    half_open_max_calls: int = 3  # Max calls in half-open state


class CircuitState:
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    Prevents cascading failures by stopping requests to failing services.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        with self._lock:
            # Check if circuit should transition to half-open
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and \
                   (time.time() - self.last_failure_time) >= self.config.timeout:
                    logger.info(f"Circuit breaker {self.name}: Transitioning to HALF_OPEN")
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                else:
                    raise Exception(f"Circuit breaker {self.name} is OPEN")
            
            # Check if too many calls in half-open state
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise Exception(f"Circuit breaker {self.name} is HALF_OPEN (max calls reached)")
                self.half_open_calls += 1
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                
                if self.success_count >= self.config.success_threshold:
                    logger.info(f"Circuit breaker {self.name}: Transitioning to CLOSED")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.half_open_calls = 0
            
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success in closed state
                self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                logger.warning(f"Circuit breaker {self.name}: Failure in HALF_OPEN, transitioning to OPEN")
                self.state = CircuitState.OPEN
                self.success_count = 0
                self.half_open_calls = 0
            
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    logger.warning(f"Circuit breaker {self.name}: Transitioning to OPEN")
                    self.state = CircuitState.OPEN
                    self.success_count = 0
    
    def get_state(self) -> Dict:
        """Get current circuit breaker state"""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "success_threshold": self.config.success_threshold,
                    "timeout": self.config.timeout
                }
            }
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.half_open_calls = 0
            logger.info(f"Circuit breaker {self.name}: Manually reset to CLOSED")


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
    
    def get_or_create(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        with self._lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, config)
            return self.breakers[name]
    
    def get_all_states(self) -> Dict[str, Dict]:
        """Get states of all circuit breakers"""
        with self._lock:
            return {name: breaker.get_state() for name, breaker in self.breakers.items()}


# Global instances
rate_limit_store = RateLimitStore()
circuit_breaker_registry = CircuitBreakerRegistry()


def rate_limit(config: RateLimitConfig, key_func: Optional[Callable] = None):
    """
    Decorator for rate limiting.
    
    Args:
        config: Rate limit configuration
        key_func: Function to extract rate limit key from args (default: use function name)
    
    Usage:
        @rate_limit(RateLimitConfig(max_requests=10, time_window=60))
        def api_endpoint(user_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Determine rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = func.__name__
            
            # Check rate limit
            if not rate_limit_store.check_rate_limit(key, config):
                raise Exception(f"Rate limit exceeded for {key}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def circuit_breaker(config: CircuitBreakerConfig, name: Optional[str] = None):
    """
    Decorator for circuit breaker protection.
    
    Args:
        config: Circuit breaker configuration
        name: Circuit breaker name (default: function name)
    
    Usage:
        @circuit_breaker(CircuitBreakerConfig(failure_threshold=5))
        def external_api_call():
            ...
    """
    def decorator(func: Callable) -> Callable:
        breaker_name = name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            breaker = circuit_breaker_registry.get_or_create(breaker_name, config)
            return breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator
