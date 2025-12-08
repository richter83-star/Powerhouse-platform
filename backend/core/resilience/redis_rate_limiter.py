"""
Redis-backed rate limiter for distributed rate limiting.
"""
import time
import logging
from typing import Optional
from dataclasses import dataclass
import redis
from redis.connection import ConnectionPool

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    max_requests: int  # Maximum requests
    time_window: int  # Time window in seconds
    burst_size: int = 0  # Burst capacity (0 = no burst)


class RedisRateLimiter:
    """
    Redis-backed rate limiter using sliding window log algorithm.
    
    Thread-safe and works across multiple instances.
    """
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        key_prefix: str = "rate_limit:"
    ):
        """
        Initialize Redis rate limiter.
        
        Args:
            redis_client: Redis client instance (creates new if None)
            key_prefix: Prefix for Redis keys
        """
        self.key_prefix = key_prefix
        
        if redis_client:
            self.redis = redis_client
        else:
            # Create Redis connection from settings
            redis_host = getattr(settings, 'redis_host', 'localhost')
            redis_port = getattr(settings, 'redis_port', 6379)
            redis_db = getattr(settings, 'redis_db', 0)
            redis_password = getattr(settings, 'redis_password', None)
            
            pool = ConnectionPool(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=False,  # We need bytes for some operations
                max_connections=50
            )
            self.redis = redis.Redis(connection_pool=pool)
        
        # Test connection
        try:
            self.redis.ping()
            logger.info("Redis rate limiter connected successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _get_key(self, identifier: str) -> bytes:
        """Get Redis key for identifier"""
        return f"{self.key_prefix}{identifier}".encode('utf-8')
    
    def check_rate_limit(
        self,
        identifier: str,
        config: RateLimitConfig,
        tokens: int = 1
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit using sliding window log.
        
        Args:
            identifier: Unique identifier (user_id, ip_address, etc.)
            config: Rate limit configuration
            tokens: Number of tokens to consume
            
        Returns:
            Tuple of (allowed: bool, info: dict)
            info contains: allowed, remaining, reset_time, limit
        """
        key = self._get_key(identifier)
        now = time.time()
        window_start = now - config.time_window
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Remove old entries (outside time window)
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiration
            pipe.expire(key, config.time_window + 1)
            
            # Execute pipeline
            results = pipe.execute()
            current_count = results[1]  # Result from zcard
            
            # Check if within limit
            limit = config.max_requests + config.burst_size
            allowed = current_count < limit
            
            if allowed:
                # Calculate remaining
                remaining = max(0, limit - current_count - tokens)
            else:
                remaining = 0
            
            # Calculate reset time (oldest entry + window)
            if current_count > 0:
                oldest = self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_time = oldest[0][1] + config.time_window
                else:
                    reset_time = now + config.time_window
            else:
                reset_time = now + config.time_window
            
            return allowed, {
                "allowed": allowed,
                "remaining": remaining,
                "reset_time": int(reset_time),
                "limit": limit,
                "current": current_count
            }
        
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Fail open - allow request if Redis is down
            return True, {
                "allowed": True,
                "remaining": config.max_requests,
                "reset_time": int(now + config.time_window),
                "limit": config.max_requests,
                "current": 0,
                "error": "redis_unavailable"
            }
    
    def get_rate_limit_info(
        self,
        identifier: str,
        config: RateLimitConfig
    ) -> dict:
        """
        Get current rate limit status without consuming tokens.
        
        Args:
            identifier: Unique identifier
            config: Rate limit configuration
            
        Returns:
            Dict with rate limit information
        """
        key = self._get_key(identifier)
        now = time.time()
        window_start = now - config.time_window
        
        try:
            # Remove old entries
            self.redis.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_count = self.redis.zcard(key)
            
            limit = config.max_requests + config.burst_size
            remaining = max(0, limit - current_count)
            
            # Get reset time
            if current_count > 0:
                oldest = self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_time = oldest[0][1] + config.time_window
                else:
                    reset_time = now + config.time_window
            else:
                reset_time = now + config.time_window
            
            return {
                "remaining": remaining,
                "reset_time": int(reset_time),
                "limit": limit,
                "current": current_count
            }
        
        except redis.RedisError as e:
            logger.error(f"Redis error getting rate limit info: {e}")
            return {
                "remaining": config.max_requests,
                "reset_time": int(now + config.time_window),
                "limit": config.max_requests,
                "current": 0,
                "error": "redis_unavailable"
            }
    
    def reset_rate_limit(self, identifier: str) -> bool:
        """
        Reset rate limit for identifier.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            True if reset successful
        """
        key = self._get_key(identifier)
        try:
            return bool(self.redis.delete(key))
        except redis.RedisError as e:
            logger.error(f"Redis error resetting rate limit: {e}")
            return False


# Global Redis rate limiter instance
_redis_rate_limiter: Optional[RedisRateLimiter] = None


def get_redis_rate_limiter() -> RedisRateLimiter:
    """Get or create global Redis rate limiter instance"""
    global _redis_rate_limiter
    
    if _redis_rate_limiter is None:
        _redis_rate_limiter = RedisRateLimiter()
    
    return _redis_rate_limiter

