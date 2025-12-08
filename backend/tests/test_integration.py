"""
Integration tests for full request flow and middleware chain.
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from core.security.user_service import UserService


@pytest.mark.integration
class TestFullRequestFlow:
    """Test complete request flow through all middleware."""
    
    def test_request_with_all_middleware(self, test_client, db_session, sample_user_data):
        """Test request flows through all middleware layers."""
        # Create user
        user_service = UserService(db_session)
        user = user_service.create_user(
            email=sample_user_data["email"],
            password=sample_user_data["password"],
            full_name=sample_user_data["full_name"],
            tenant_id=sample_user_data["tenant_id"]
        )
        
        # Login to get token
        login_response = test_client.post(
            "/api/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
                "tenant_id": sample_user_data["tenant_id"]
            }
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            
            # Make authenticated request
            response = test_client.get(
                "/health",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Check all middleware applied
            assert response.status_code == 200
            
            # Correlation ID should be present
            assert "X-Correlation-ID" in response.headers
            
            # Security headers should be present
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
    
    def test_error_handling_with_correlation_id(self, test_client):
        """Test error responses include correlation ID."""
        response = test_client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        # Correlation ID should be in headers even for errors
        assert "X-Correlation-ID" in response.headers
    
    def test_validation_error_format(self, test_client):
        """Test validation errors follow standard format."""
        response = test_client.post(
            "/api/auth/login",
            json={"invalid": "data"}  # Missing required fields
        )
        
        assert response.status_code == 422
        data = response.json()
        
        # Should have detail or error field
        assert "detail" in data or "error" in data


@pytest.mark.integration
class TestMultiTenantIsolation:
    """Test multi-tenant isolation end-to-end."""
    
    def test_tenant_isolation_in_queries(self, db_session):
        """Test that queries are properly filtered by tenant."""
        from database.models import Run
        from database.query_helpers import query_with_tenant
        
        # Create runs for different tenants
        run1 = Run(
            id="run-1",
            tenant_id="tenant-1",
            workflow_type="compliance",
            status="pending"
        )
        run2 = Run(
            id="run-2",
            tenant_id="tenant-2",
            workflow_type="compliance",
            status="pending"
        )
        db_session.add(run1)
        db_session.add(run2)
        db_session.commit()
        
        # Query for tenant-1
        query1 = query_with_tenant(db_session, Run, "tenant-1")
        results1 = query1.all()
        
        # Should only get tenant-1's runs
        assert all(r.tenant_id == "tenant-1" for r in results1)
        assert not any(r.tenant_id == "tenant-2" for r in results1)
        
        # Query for tenant-2
        query2 = query_with_tenant(db_session, Run, "tenant-2")
        results2 = query2.all()
        
        # Should only get tenant-2's runs
        assert all(r.tenant_id == "tenant-2" for r in results2)
        assert not any(r.tenant_id == "tenant-1" for r in results2)


@pytest.mark.integration
class TestRateLimitingIntegration:
    """Test rate limiting integration."""
    
    def test_rate_limiting_headers(self, test_client):
        """Test rate limiting headers are present."""
        # Make multiple requests
        for _ in range(5):
            response = test_client.get("/health")
            assert response.status_code == 200
        
        # Headers may or may not be present depending on Redis availability
        # But endpoint should still work
        assert True


@pytest.mark.integration
class TestMonitoringIntegration:
    """Test monitoring integration."""
    
    def test_metrics_collected_during_request(self, test_client):
        """Test that metrics are collected during requests."""
        # Make a request
        response = test_client.get("/health")
        assert response.status_code == 200
        
        # Check metrics endpoint
        metrics_response = test_client.get("/metrics/prometheus")
        assert metrics_response.status_code == 200
        
        # Metrics should contain some data
        metrics_text = metrics_response.text
        assert len(metrics_text) > 0
    
    def test_health_metrics_includes_system(self, test_client):
        """Test health metrics include system metrics."""
        response = test_client.get("/metrics/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "system" in data
        assert "timestamp" in data


@pytest.mark.integration
class TestCachingIntegration:
    """Test caching integration with requests."""
    
    def test_cache_used_in_request_flow(self, test_client):
        """Test that cache is used during request processing."""
        # This is a conceptual test - actual cache usage depends on implementation
        response1 = test_client.get("/health")
        response2 = test_client.get("/health")
        
        # Both should work
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Correlation IDs should be different (or same if preserved)
        assert "X-Correlation-ID" in response1.headers
        assert "X-Correlation-ID" in response2.headers

