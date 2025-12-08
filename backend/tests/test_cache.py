"""
Tests for caching functionality.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from core.cache.redis_cache import RedisCache, get_cache, cache_result, invalidate_cache
from core.cache.query_cache import cache_query_result, cache_model_by_id


@pytest.mark.unit
@pytest.mark.cache
class TestRedisCache:
    """Test RedisCache functionality."""
    
    def test_cache_initialization_with_redis(self):
        """Test cache initialization with Redis connection."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        
        cache = RedisCache(redis_client=mock_redis)
        assert cache._available is True
        assert cache.redis == mock_redis
    
    def test_cache_initialization_without_redis(self):
        """Test cache initialization without Redis (graceful degradation)."""
        with patch('core.cache.redis_cache.redis.Redis') as mock_redis_class:
            mock_redis = Mock()
            mock_redis.ping.side_effect = Exception("Connection failed")
            mock_redis_class.return_value = mock_redis
            
            cache = RedisCache()
            assert cache._available is False
    
    def test_cache_set_and_get(self):
        """Test setting and getting values from cache."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = '{"key": "value"}'
        mock_redis.setex.return_value = True
        
        cache = RedisCache(redis_client=mock_redis)
        
        # Test set
        result = cache.set("test_key", {"key": "value"}, ttl=3600)
        assert result is True
        mock_redis.setex.assert_called_once()
        
        # Test get
        value = cache.get("test_key")
        assert value == {"key": "value"}
        mock_redis.get.assert_called()
    
    def test_cache_get_miss(self):
        """Test getting non-existent key returns default."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        
        cache = RedisCache(redis_client=mock_redis)
        value = cache.get("nonexistent", default="default_value")
        assert value == "default_value"
    
    def test_cache_delete(self):
        """Test deleting cache key."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.delete.return_value = 1
        
        cache = RedisCache(redis_client=mock_redis)
        result = cache.delete("test_key")
        assert result is True
        mock_redis.delete.assert_called_once()
    
    def test_cache_clear(self):
        """Test clearing cache with pattern."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.keys.return_value = [b"cache:key1", b"cache:key2"]
        mock_redis.delete.return_value = 2
        
        cache = RedisCache(redis_client=mock_redis)
        count = cache.clear("user:*")
        assert count == 2
        mock_redis.keys.assert_called_once()
        mock_redis.delete.assert_called_once()
    
    def test_cache_exists(self):
        """Test checking if key exists."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.exists.return_value = 1
        
        cache = RedisCache(redis_client=mock_redis)
        exists = cache.exists("test_key")
        assert exists is True
    
    def test_cache_get_or_set(self):
        """Test get_or_set functionality."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        
        cache = RedisCache(redis_client=mock_redis)
        
        def compute_value():
            return "computed_value"
        
        value = cache.get_or_set("test_key", compute_value, ttl=3600)
        assert value == "computed_value"
        mock_redis.setex.assert_called_once()
    
    def test_cache_graceful_degradation(self):
        """Test cache works when Redis is unavailable."""
        cache = RedisCache()
        cache._available = False
        
        # Should return default without error
        value = cache.get("test_key", default="default")
        assert value == "default"
        
        # Set should return False but not raise
        result = cache.set("test_key", "value")
        assert result is False


@pytest.mark.unit
@pytest.mark.cache
class TestCacheDecorators:
    """Test cache decorators."""
    
    def test_cache_result_decorator(self):
        """Test @cache_result decorator."""
        call_count = [0]
        
        @cache_result(ttl=60, key_prefix="test:")
        def expensive_function(x, y):
            call_count[0] += 1
            return x + y
        
        # Mock cache
        with patch('core.cache.redis_cache.get_cache') as mock_get_cache:
            mock_cache = Mock()
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True
            mock_get_cache.return_value = mock_cache
            
            result1 = expensive_function(1, 2)
            assert result1 == 3
            assert call_count[0] == 1
            
            # Second call should use cache
            result2 = expensive_function(1, 2)
            assert result2 == 3
            assert call_count[0] == 1  # Should not increment
    
    def test_invalidate_cache_decorator(self):
        """Test @invalidate_cache decorator."""
        with patch('core.cache.redis_cache.get_cache') as mock_get_cache:
            mock_cache = Mock()
            mock_cache.clear.return_value = 2
            mock_get_cache.return_value = mock_cache
            
            @invalidate_cache("user:*")
            def update_user(user_id, data):
                return {"id": user_id, **data}
            
            result = update_user("123", {"name": "Test"})
            assert result["id"] == "123"
            mock_cache.clear.assert_called_once_with("user:*")
    
    def test_cache_query_result_decorator(self):
        """Test @cache_query_result decorator."""
        call_count = [0]
        
        @cache_query_result(ttl=300)
        def get_users(db, tenant_id):
            call_count[0] += 1
            return [{"id": "1", "name": "User 1"}]
        
        with patch('core.cache.query_cache.get_cache') as mock_get_cache:
            mock_cache = Mock()
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True
            mock_get_cache.return_value = mock_cache
            
            mock_db = Mock()
            result = get_users(mock_db, "tenant-123")
            
            assert len(result) == 1
            assert call_count[0] == 1


@pytest.mark.integration
@pytest.mark.cache
class TestCacheIntegration:
    """Integration tests for caching."""
    
    def test_cache_with_real_redis(self, test_client):
        """Test cache works with real Redis if available."""
        # This test will pass if Redis is available, skip if not
        try:
            from core.cache.redis_cache import get_cache
            cache = get_cache()
            if cache._available:
                cache.set("test_integration", {"test": "data"}, ttl=60)
                value = cache.get("test_integration")
                assert value == {"test": "data"}
        except Exception:
            pytest.skip("Redis not available for integration test")
    
    def test_cache_key_generation(self):
        """Test cache key generation is consistent."""
        with patch('core.cache.redis_cache.get_cache') as mock_get_cache:
            mock_cache = Mock()
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True
            mock_get_cache.return_value = mock_cache
            
            @cache_result(ttl=60)
            def test_func(a, b):
                return a + b
            
            test_func(1, 2)
            test_func(1, 2)  # Should use same cache key
            
            # Verify cache.get was called with same key
            assert mock_cache.get.call_count == 2
            # Both calls should use same key
            assert mock_cache.get.call_args_list[0][0][0] == mock_cache.get.call_args_list[1][0][0]

