"""
Database query result caching.
"""
import hashlib
import logging
from typing import Optional, TypeVar, Type, Callable
from functools import wraps
from sqlalchemy.orm import Session, Query

from core.cache.redis_cache import get_cache, cache_result
from database.query_helpers import query_with_tenant

logger = logging.getLogger(__name__)

T = TypeVar('T')


def cache_query_result(
    ttl: int = 300,  # 5 minutes default
    key_prefix: Optional[str] = None
):
    """
    Decorator to cache database query results.
    
    Args:
        ttl: Cache TTL in seconds
        key_prefix: Optional prefix for cache keys
    
    Example:
        @cache_query_result(ttl=600)
        def get_user_workflows(db: Session, user_id: str, tenant_id: str):
            return query_with_tenant(db, Run, tenant_id, user_id=user_id).all()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract db session and tenant_id from args/kwargs
            db = None
            tenant_id = None
            
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break
            
            if not db:
                db = kwargs.get('db') or kwargs.get('db_session')
            
            tenant_id = kwargs.get('tenant_id')
            if not tenant_id:
                # Try to get from db session state or request
                pass
            
            # Generate cache key from function name and parameters
            cache_key_parts = [func.__name__]
            
            # Add tenant_id to key if available
            if tenant_id:
                cache_key_parts.append(f"tenant:{tenant_id}")
            
            # Add other relevant kwargs to key
            for key, value in sorted(kwargs.items()):
                if key not in ['db', 'db_session'] and value is not None:
                    cache_key_parts.append(f"{key}:{str(value)}")
            
            cache_key = ":".join(cache_key_parts)
            
            if key_prefix:
                cache_key = f"{key_prefix}{cache_key}"
            
            # Hash long keys
            if len(cache_key) > 200:
                cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            cache = get_cache()
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for query: {func.__name__}")
                return cached_result
            
            # Execute query
            logger.debug(f"Cache miss for query: {func.__name__}")
            result = func(*args, **kwargs)
            
            # Cache result (only if it's serializable)
            try:
                # For SQLAlchemy objects, we need to convert to dicts
                if hasattr(result, '__iter__') and not isinstance(result, (str, bytes)):
                    result_list = list(result)
                    if result_list and hasattr(result_list[0], '__dict__'):
                        # Convert SQLAlchemy objects to dicts
                        serializable_result = [
                            {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
                            for obj in result_list
                        ]
                        cache.set(cache_key, serializable_result, ttl)
                    else:
                        cache.set(cache_key, result, ttl)
                else:
                    cache.set(cache_key, result, ttl)
            except Exception as e:
                logger.warning(f"Failed to cache query result: {e}")
            
            return result
        
        return wrapper
    return decorator


def cache_model_by_id(
    model_class: Type[T],
    ttl: int = 600  # 10 minutes default
):
    """
    Cache model instances by ID.
    
    Args:
        model_class: SQLAlchemy model class
        ttl: Cache TTL in seconds
    
    Returns:
        Decorated function that caches model lookups
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract ID from args/kwargs
            record_id = kwargs.get('id') or kwargs.get('record_id') or kwargs.get(f'{model_class.__name__.lower()}_id')
            tenant_id = kwargs.get('tenant_id')
            
            if not record_id:
                # If no ID, just execute function
                return func(*args, **kwargs)
            
            cache_key = f"model:{model_class.__name__}:{record_id}"
            if tenant_id:
                cache_key = f"{cache_key}:tenant:{tenant_id}"
            
            cache = get_cache()
            
            # Try cache
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {model_class.__name__}:{record_id}")
                # Reconstruct model instance from dict
                # Note: This is simplified - in production, use proper serialization
                return cached
            
            # Execute query
            logger.debug(f"Cache miss for {model_class.__name__}:{record_id}")
            result = func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                try:
                    if hasattr(result, '__dict__'):
                        serialized = {
                            k: v for k, v in result.__dict__.items()
                            if not k.startswith('_')
                        }
                        cache.set(cache_key, serialized, ttl)
                except Exception as e:
                    logger.warning(f"Failed to cache model: {e}")
            
            return result
        
        return wrapper
    return decorator

