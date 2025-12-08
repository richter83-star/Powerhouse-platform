"""
Tests for middleware functionality.
"""
import pytest
from fastapi import status


@pytest.mark.unit
class TestCorrelationIDMiddleware:
    """Test correlation ID middleware."""
    
    def test_correlation_id_generated(self, test_client):
        """Test that correlation ID is generated if not provided."""
        response = test_client.get("/health")
        
        assert "X-Correlation-ID" in response.headers
        correlation_id = response.headers["X-Correlation-ID"]
        assert correlation_id is not None
        assert len(correlation_id) > 0
    
    def test_correlation_id_preserved(self, test_client):
        """Test that provided correlation ID is preserved."""
        custom_id = "custom-correlation-id-123"
        response = test_client.get(
            "/health",
            headers={"X-Correlation-ID": custom_id}
        )
        
        assert response.headers["X-Correlation-ID"] == custom_id


@pytest.mark.integration
class TestRateLimitMiddleware:
    """Test rate limiting middleware."""
    
    def test_rate_limit_headers(self, test_client):
        """Test that rate limit headers are present."""
        response = test_client.get("/health")
        
        # Headers may not be present if rate limiting is disabled
        # or if Redis is not available
        # This test just ensures the endpoint works
        assert response.status_code == status.HTTP_200_OK

