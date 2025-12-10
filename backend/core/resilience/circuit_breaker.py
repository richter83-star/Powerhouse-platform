"""
Circuit Breaker Pattern Implementation

Prevents cascading failures by stopping requests to failing services.
"""

import logging
import time
from typing import Callable, Any, Optional, Dict
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Open circuit after N failures
    success_threshold: int = 2  # Close circuit after N successes (half-open)
    timeout_seconds: int = 60  # Time before trying half-open
    expected_exception: type = Exception  # Exception type to catch


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[datetime] = None
    state: CircuitState = CircuitState.CLOSED
    total_requests: int = 0
    rejected_requests: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation.
    
    Features:
    - Automatic state transitions
    - Configurable thresholds
    - Statistics tracking
    - Graceful degradation
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker (e.g., "database", "external_api")
            config: Configuration (uses defaults if None)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.stats.last_failure_time:
                time_since_failure = (datetime.utcnow() - self.stats.last_failure_time).total_seconds()
                if time_since_failure >= self.config.timeout_seconds:
                    # Transition to half-open
                    self.state = CircuitState.HALF_OPEN
                    self.stats.successes = 0
                    logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
                else:
                    # Still open, reject request
                    self.stats.rejected_requests += 1
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker {self.name} is OPEN. "
                        f"Retry after {self.config.timeout_seconds - int(time_since_failure)} seconds"
                    )
        
        # Execute function
        self.stats.total_requests += 1
        try:
            result = func(*args, **kwargs)
            
            # Success
            self._record_success()
            return result
            
        except self.config.expected_exception as e:
            # Failure
            self._record_failure()
            raise e
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self.stats.last_failure_time:
                time_since_failure = (datetime.utcnow() - self.stats.last_failure_time).total_seconds()
                if time_since_failure >= self.config.timeout_seconds:
                    self.state = CircuitState.HALF_OPEN
                    self.stats.successes = 0
                    logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
                else:
                    self.stats.rejected_requests += 1
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker {self.name} is OPEN. "
                        f"Retry after {self.config.timeout_seconds - int(time_since_failure)} seconds"
                    )
        
        # Execute function
        self.stats.total_requests += 1
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
            
        except self.config.expected_exception as e:
            self._record_failure()
            raise e
    
    def _record_success(self):
        """Record successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.stats.successes += 1
            if self.stats.successes >= self.config.success_threshold:
                # Close circuit
                self.state = CircuitState.CLOSED
                self.stats.failures = 0
                logger.info(f"Circuit breaker {self.name} CLOSED (recovered)")
        else:
            # Reset failure count on success
            self.stats.failures = 0
    
    def _record_failure(self):
        """Record failed call."""
        self.stats.failures += 1
        self.stats.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitState.HALF_OPEN:
            # Back to open
            self.state = CircuitState.OPEN
            self.stats.successes = 0
            logger.warning(f"Circuit breaker {self.name} OPEN (half-open test failed)")
        
        elif self.state == CircuitState.CLOSED:
            if self.stats.failures >= self.config.failure_threshold:
                # Open circuit
                self.state = CircuitState.OPEN
                logger.error(
                    f"Circuit breaker {self.name} OPEN "
                    f"(failure threshold {self.config.failure_threshold} reached)"
                )
    
    def reset(self):
        """Manually reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.stats.failures = 0
        self.stats.successes = 0
        self.stats.last_failure_time = None
        logger.info(f"Circuit breaker {self.name} manually reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.stats.failures,
            "successes": self.stats.successes,
            "total_requests": self.stats.total_requests,
            "rejected_requests": self.stats.rejected_requests,
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds
            }
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# Global circuit breakers registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """
    Get or create a circuit breaker.
    
    Args:
        name: Circuit breaker name
        config: Configuration (uses defaults if None)
        
    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    
    return _circuit_breakers[name]


def reset_all_circuit_breakers():
    """Reset all circuit breakers."""
    for cb in _circuit_breakers.values():
        cb.reset()

