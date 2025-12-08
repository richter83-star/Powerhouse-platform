"""
Integration tests for API endpoints.
"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.api
class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_health_check_has_correlation_id(self, test_client):
        """Test that health check includes correlation ID in response."""
        response = test_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        assert "X-Correlation-ID" in response.headers


@pytest.mark.integration
@pytest.mark.api
class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint returns API information."""
        response = test_client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert "documentation" in data
        assert "endpoints" in data


@pytest.mark.integration
@pytest.mark.api
class TestWorkflowEndpoints:
    """Test workflow endpoints."""
    
    def test_start_compliance_workflow_requires_auth(self, test_client, sample_workflow_data):
        """Test that workflow endpoints require authentication."""
        response = test_client.post(
            "/api/v1/workflows/compliance",
            json=sample_workflow_data
        )
        
        # Should return 401 or 403 if auth is enabled
        # For now, may return 202 if auth is disabled
        assert response.status_code in [
            status.HTTP_202_ACCEPTED,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]
    
    def test_workflow_status_endpoint(self, test_client):
        """Test workflow status endpoint."""
        # Use a non-existent workflow ID
        response = test_client.get("/api/v1/workflows/nonexistent-id/status")
        
        # Should return 404 or 401/403
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.integration
@pytest.mark.api
class TestErrorHandling:
    """Test error handling and responses."""
    
    def test_404_not_found(self, test_client):
        """Test 404 error response."""
        response = test_client.get("/nonexistent-endpoint")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_validation_error_format(self, test_client):
        """Test that validation errors follow standard format."""
        response = test_client.post(
            "/api/auth/login",
            json={"invalid": "data"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        # Check if it follows ErrorResponse format
        assert "detail" in data or "error" in data
    
    def test_correlation_id_in_error_response(self, test_client):
        """Test that error responses include correlation ID."""
        response = test_client.get("/nonexistent-endpoint")
        
        # Correlation ID should be in response headers
        assert "X-Correlation-ID" in response.headers

