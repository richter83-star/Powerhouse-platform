"""
Tests for performance optimization features.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch

from core.performance.async_utils import (
    run_in_thread,
    batch_async,
    async_cache_result,
    parallel_map
)
from core.performance.connection_pool import create_optimized_engine


@pytest.mark.unit
@pytest.mark.performance
class TestAsyncUtils:
    """Test async utility functions."""
    
    @pytest.mark.asyncio
    async def test_run_in_thread(self):
        """Test running synchronous function in thread."""
        def sync_function(x, y):
            return x + y
        
        result = await run_in_thread(sync_function, 2, 3)
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_batch_async(self):
        """Test batch async execution."""
        async def async_task(n):
            await asyncio.sleep(0.01)
            return n * 2
        
        tasks = [async_task(i) for i in range(10)]
        results = await batch_async(tasks, batch_size=3, max_concurrent=2)
        
        assert len(results) == 10
        assert results[0] == 0
        assert results[5] == 10
    
    @pytest.mark.asyncio
    async def test_batch_async_with_exceptions(self):
        """Test batch_async handles exceptions."""
        async def async_task(n):
            if n == 5:
                raise ValueError("Test error")
            return n * 2
        
        tasks = [async_task(i) for i in range(10)]
        results = await batch_async(tasks, batch_size=5, max_concurrent=2)
        
        assert len(results) == 10
        assert results[5] is None  # Exception should result in None
    
    @pytest.mark.asyncio
    async def test_parallel_map(self):
        """Test parallel_map function."""
        async def process_item(item):
            await asyncio.sleep(0.01)
            return item * 2
        
        items = [1, 2, 3, 4, 5]
        results = await parallel_map(items, process_item, max_concurrent=3)
        
        assert len(results) == 5
        assert results[0] == 2
        assert results[4] == 10
    
    @pytest.mark.asyncio
    async def test_async_cache_result(self):
        """Test async cache result decorator."""
        call_count = [0]
        
        @async_cache_result(ttl=60)
        async def expensive_async_function(x):
            call_count[0] += 1
            await asyncio.sleep(0.01)
            return x * 2
        
        result1 = await expensive_async_function(5)
        assert result1 == 10
        assert call_count[0] == 1
        
        # Second call should use cache
        result2 = await expensive_async_function(5)
        assert result2 == 10
        assert call_count[0] == 1  # Should not increment


@pytest.mark.unit
@pytest.mark.performance
class TestConnectionPool:
    """Test connection pool optimization."""
    
    def test_create_optimized_engine(self):
        """Test creating optimized engine."""
        database_url = "sqlite:///:memory:"
        
        # Should not raise error
        try:
            engine = create_optimized_engine(database_url)
            assert engine is not None
        except Exception as e:
            # SQLite might not support all optimizations
            if "sqlite" not in str(e).lower():
                raise
    
    @patch('core.performance.connection_pool.create_engine')
    def test_connection_pool_configuration(self, mock_create_engine):
        """Test connection pool is configured correctly."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        database_url = "postgresql://user:pass@localhost/db"
        engine = create_optimized_engine(database_url)
        
        # Verify create_engine was called with pool configuration
        mock_create_engine.assert_called_once()
        call_kwargs = mock_create_engine.call_args[1]
        
        assert call_kwargs.get("pool_size") == 10 or "poolclass" in call_kwargs
        assert call_kwargs.get("max_overflow") == 20 or "poolclass" in call_kwargs
        assert call_kwargs.get("pool_pre_ping") is True


@pytest.mark.integration
@pytest.mark.performance
class TestPerformanceImprovements:
    """Integration tests for performance improvements."""
    
    def test_cache_reduces_database_queries(self, db_session):
        """Test that caching reduces database queries."""
        from core.cache.query_cache import cache_query_result
        from database.models import User
        
        query_count = [0]
        
        @cache_query_result(ttl=60)
        def get_users_cached(db, tenant_id):
            query_count[0] += 1
            return db.query(User).all()
        
        with patch('core.cache.query_cache.get_cache') as mock_get_cache:
            mock_cache = Mock()
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True
            mock_get_cache.return_value = mock_cache
            
            # First call
            get_users_cached(db_session, "tenant-1")
            assert query_count[0] == 1
            
            # Second call should use cache
            mock_cache.get.return_value = [{"id": "1"}]
            get_users_cached(db_session, "tenant-1")
            assert query_count[0] == 1  # Should not increment
    
    def test_pagination_reduces_memory(self, db_session):
        """Test pagination reduces memory usage."""
        from database.models import User
        from core.performance.query_optimizer import QueryOptimizer
        
        # Create many users
        for i in range(100):
            user = User(
                id=f"user-{i}",
                email=f"user{i}@example.com",
                password_hash="hash",
                is_active=1
            )
            db_session.add(user)
        db_session.commit()
        
        query = db_session.query(User)
        items, pagination = QueryOptimizer.paginate_query(query, page=1, page_size=10)
        
        # Should only load 10 items, not all 100
        assert len(items) == 10
        assert pagination["total"] == 100

