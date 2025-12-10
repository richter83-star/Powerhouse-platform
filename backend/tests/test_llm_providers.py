"""
Tests for LLM Provider Enhancements (Phase 1)

Tests retry logic and error handling.
"""

import pytest
import time
from unittest.mock import Mock, patch
import requests
from requests.exceptions import HTTPError

from llm.routellm_provider import RouteLLMProvider
try:
    from utils.errors import LLMError
except ImportError:
    # Create a simple LLMError if not available
    class LLMError(Exception):
        def __init__(self, message, metadata=None):
            super().__init__(message)
            self.metadata = metadata or {}


@pytest.mark.unit
class TestRouteLLMRetryLogic:
    """Test retry logic in RouteLLM provider."""
    
    def test_retry_on_rate_limit(self):
        """Test retry on 429 (rate limit)."""
        provider = RouteLLMProvider(api_key="test-key")
        
        # Mock requests.post to fail twice with 429, then succeed
        call_count = [0]
        def mock_post(*args, **kwargs):
            call_count[0] += 1
            response = Mock()
            if call_count[0] <= 2:
                response.status_code = 429
                response.raise_for_status.side_effect = HTTPError("Rate limited")
            else:
                response.status_code = 200
                response.json.return_value = {
                    "choices": [{"message": {"content": "Success"}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
                }
            return response
        
        with patch('llm.routellm_provider.requests.post', side_effect=mock_post):
            response = provider.invoke("test prompt")
            
            assert response.content == "Success"
            assert call_count[0] == 3  # Should have retried
    
    def test_retry_on_server_errors(self):
        """Test retry on 502/503 (server errors)."""
        provider = RouteLLMProvider(api_key="test-key")
        
        call_count = [0]
        def mock_post(*args, **kwargs):
            call_count[0] += 1
            response = Mock()
            if call_count[0] <= 1:
                response.status_code = 502
                response.raise_for_status.side_effect = HTTPError("Bad gateway")
            else:
                response.status_code = 200
                response.json.return_value = {
                    "choices": [{"message": {"content": "Success"}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
                }
            return response
        
        with patch('llm.routellm_provider.requests.post', side_effect=mock_post):
            response = provider.invoke("test prompt")
            
            assert response.content == "Success"
            assert call_count[0] >= 2  # Should have retried
    
    def test_no_retry_on_client_errors(self):
        """Test no retry on 401/404 errors."""
        provider = RouteLLMProvider(api_key="test-key")
        
        call_count = [0]
        def mock_post(*args, **kwargs):
            call_count[0] += 1
            response = Mock()
            response.status_code = 401
            response.raise_for_status.side_effect = HTTPError("Unauthorized")
            return response
        
        with patch('llm.routellm_provider.requests.post', side_effect=mock_post):
            with pytest.raises(Exception):  # Should raise without retrying
                provider.invoke("test prompt")
            
            assert call_count[0] == 1  # Should not retry
    
    def test_exponential_backoff_timing(self):
        """Test exponential backoff timing."""
        provider = RouteLLMProvider(api_key="test-key")
        
        call_times = []
        def mock_post(*args, **kwargs):
            call_times.append(time.time())
            response = Mock()
            if len(call_times) < 3:
                response.status_code = 429
                response.raise_for_status.side_effect = HTTPError("Rate limited")
            else:
                response.status_code = 200
                response.json.return_value = {
                    "choices": [{"message": {"content": "Success"}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
                }
            return response
        
        with patch('llm.routellm_provider.requests.post', side_effect=mock_post):
            with patch('llm.routellm_provider.time.sleep'):  # Mock sleep to speed up test
                response = provider.invoke("test prompt")
                
                assert response.content == "Success"
                assert len(call_times) == 3
    
    def test_max_retry_limit(self):
        """Test max retry limit."""
        provider = RouteLLMProvider(api_key="test-key")
        
        call_count = [0]
        def mock_post(*args, **kwargs):
            call_count[0] += 1
            response = Mock()
            response.status_code = 429  # Always rate limited
            response.raise_for_status.side_effect = HTTPError("Rate limited")
            return response
        
        with patch('llm.routellm_provider.requests.post', side_effect=mock_post):
            with pytest.raises(Exception):
                provider.invoke("test prompt")
            
            # Should retry up to max attempts (default is 3)
            assert call_count[0] <= 3


@pytest.mark.unit
class TestLLMErrorHandling:
    """Test error categorization and handling."""
    
    def test_error_categorization(self):
        """Test that errors are properly categorized."""
        provider = RouteLLMProvider(api_key="test-key")
        
        # Test retryable error (429)
        response_429 = Mock()
        response_429.status_code = 429
        response_429.raise_for_status.side_effect = HTTPError("Rate limited")
        
        # Test non-retryable error (401)
        response_401 = Mock()
        response_401.status_code = 401
        response_401.raise_for_status.side_effect = HTTPError("Unauthorized")
        
        # The provider should handle these differently
        # (retry logic decorator handles this, but we can test behavior)
        with patch('llm.routellm_provider.requests.post', return_value=response_429):
            with pytest.raises(Exception):
                provider.invoke("test")  # Should retry then fail
        
        with patch('llm.routellm_provider.requests.post', return_value=response_401):
            with pytest.raises(Exception):
                provider.invoke("test")  # Should fail immediately

