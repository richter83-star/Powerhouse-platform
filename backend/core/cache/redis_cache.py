"""
Redis-based caching system for performance optimization.
"""
import json
import hashlib
import logging
from typing import Optional, Callable, Any, TypeVar, Union
from functools import wraps
from datetime import timedelta
import redis
from redis.connection import ConnectionPool

from config.settings import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RedisCache:
    """
    Redis-based cache with TTL support.
    
    Features:
    - Automatic serialization/deserialization
    - TTL (time-to-live) support
    - Key prefixing for namespacing
    - Connection pooling
    - Graceful degradation if Redis unavailable
    """
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        key_prefix: str = "cache:",
        default_ttl: int = 3600,  # 1 hour default
        decode_responses: bool = True
    ):
        """
        Initialize Redis cache.
        
        Args:
            redis_client: Redis client instance (creates new if None)
            key_prefix: Prefix for all cache keys
            default_ttl: Default TTL in seconds
            decode_responses: Whether to decode responses as strings
        """
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.decode_responses = decode_responses
        
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
                decode_responses=decode_responses,
                max_connections=50
            )
            self.redis = redis.Redis(connection_pool=pool)
        
        # Test connection
        try:
            self.redis.ping()
            self._available = True
            logger.info("Redis cache connected successfully")
        except redis.ConnectionError as e:
            logger.warning(f"Redis cache unavailable: {e}. Caching disabled.")
            self._available = False
    
    def _get_key(self, key: str) -> str:
        """Get full cache key with prefix."""
        return f"{self.key_prefix}{key}"
    
    def _serialize(self, value: Any) -> str:
        """Serialize value to JSON string."""
        return json.dumps(value, default=str)
    
    def _deserialize(self, value: str) -> Any:
        """Deserialize JSON string to value."""
        return json.loads(value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        if not self._available:
            return default
        
        try:
            full_key = self._get_key(key)
            value = self.redis.get(full_key)
            if value is None:
                return default
            return self._deserialize(value)
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return default
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._available:
            return False
        
        try:
            full_key = self._get_key(key)
            serialized = self._serialize(value)
            ttl = ttl or self.default_ttl
            return self.redis.setex(full_key, ttl, serialized)
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        if not self._available:
            return False
        
        try:
            full_key = self._get_key(key)
            return bool(self.redis.delete(full_key))
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*"). If None, clears all keys with prefix.
            
        Returns:
            Number of keys deleted
        """
        if not self._available:
            return 0
        
        try:
            if pattern:
                search_pattern = f"{self.key_prefix}{pattern}"
            else:
                search_pattern = f"{self.key_prefix}*"
            
            keys = self.redis.keys(search_pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache clear error for pattern {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._available:
            return False
        
        try:
            full_key = self._get_key(key)
            return bool(self.redis.exists(full_key))
        except Exception as e:
            logger.warning(f"Cache exists error for key {key}: {e}")
            return False
    
    def get_or_set(
        self,
        key: str,
        callable: Callable[[], T],
        ttl: Optional[int] = None
    ) -> T:
        """
        Get value from cache, or compute and cache it.
        
        Args:
            key: Cache key
            callable: Function to call if cache miss
            ttl: Time-to-live in seconds
            
        Returns:
            Cached or computed value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        value = callable()
        self.set(key, value, ttl)
        return value


# Global cache instance
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


def cache_result(
    ttl: int = 3600,
    key_prefix: str = "",
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache key
        key_func: Function to generate cache key from args/kwargs
    
    Example:
        @cache_result(ttl=300, key_prefix="user:")
        def get_user(user_id: str):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name + args hash
                key_parts = [func.__name__]
                if args:
                    key_parts.append(str(hash(args)))
                if kwargs:
                    key_parts.append(str(hash(frozenset(kwargs.items()))))
                cache_key = ":".join(key_parts)
            
            if key_prefix:
                cache_key = f"{key_prefix}{cache_key}"
            
            # Try to get from cache
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Decorator to invalidate cache after function execution.
    
    Args:
        pattern: Cache key pattern to invalidate
    
    Example:
        @invalidate_cache("user:*")
        def update_user(user_id: str, data: dict):
            # Update user in database
            # Cache will be invalidated after this function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate cache
            cache = get_cache()
            cache.clear(pattern)
            
            return result
        
        return wrapper
    return decorator

