"""
Async utilities for performance optimization.
"""
import asyncio
import logging
from typing import List, Callable, TypeVar, Awaitable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def run_in_thread(func: Callable, *args, **kwargs) -> Any:
    """
    Run a synchronous function in a thread pool.
    
    Args:
        func: Synchronous function to run
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Function result
    
    Example:
        result = await run_in_thread(db.query, User).all()
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))


async def batch_async(
    tasks: List[Awaitable[T]],
    batch_size: int = 10,
    max_concurrent: int = 5
) -> List[T]:
    """
    Execute async tasks in batches with concurrency control.
    
    Args:
        tasks: List of awaitable tasks
        batch_size: Number of tasks per batch
        max_concurrent: Maximum concurrent tasks per batch
    
    Returns:
        List of results in order
    
    Example:
        tasks = [fetch_user(user_id) for user_id in user_ids]
        results = await batch_async(tasks, batch_size=20, max_concurrent=5)
    """
    results = []
    
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]
        
        # Process batch with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(task):
            async with semaphore:
                return await task
        
        batch_results = await asyncio.gather(
            *[process_with_semaphore(task) for task in batch],
            return_exceptions=True
        )
        
        # Handle exceptions
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Task failed: {result}")
                results.append(None)
            else:
                results.append(result)
    
    return results


def async_cache_result(ttl: int = 3600):
    """
    Decorator to cache async function results.
    
    Args:
        ttl: Cache TTL in seconds
    
    Example:
        @async_cache_result(ttl=300)
        async def get_user_data(user_id: str):
            return await fetch_from_api(user_id)
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_times = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = str((args, tuple(sorted(kwargs.items()))))
            
            # Check cache
            if cache_key in cache:
                cache_time = cache_times.get(cache_key, 0)
                import time
                if time.time() - cache_time < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache[cache_key]
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            import time
            cache[cache_key] = result
            cache_times[cache_key] = time.time()
            
            logger.debug(f"Cache miss for {func.__name__}")
            return result
        
        return wrapper
    return decorator


async def parallel_map(
    items: List[T],
    func: Callable[[T], Awaitable[Any]],
    max_concurrent: int = 10
) -> List[Any]:
    """
    Apply async function to items in parallel with concurrency control.
    
    Args:
        items: List of items to process
        func: Async function to apply
        max_concurrent: Maximum concurrent operations
    
    Returns:
        List of results
    
    Example:
        user_ids = ["1", "2", "3"]
        users = await parallel_map(user_ids, fetch_user, max_concurrent=5)
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_item(item):
        async with semaphore:
            return await func(item)
    
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks, return_exceptions=True)

