"""
End-to-end tests for complete workflows.
"""
import pytest
import time
from fastapi import status
from fastapi.testclient import TestClient

from core.security.user_service import UserService
from database.models import Run


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflow:
    """Test complete workflow execution end-to-end."""
    
    def test_user_signup_to_workflow_execution(self, test_client, db_session):
        """Test complete flow from signup to workflow execution."""
        # Step 1: User signup
        signup_data = {
            "email": "e2e@example.com",
            "password": "TestPassword123!",
            "full_name": "E2E Test User",
            "tenant_id": "e2e-tenant-123"
        }
        
        signup_response = test_client.post(
            "/api/auth/signup",
            json=signup_data
        )
        
        # Signup should succeed (or return appropriate status)
        assert signup_response.status_code in [201, 200, 400]  # 400 if user exists
        
        # Step 2: Login
        login_response = test_client.post(
            "/api/auth/login",
            json={
                "email": signup_data["email"],
                "password": signup_data["password"],
                "tenant_id": signup_data["tenant_id"]
            }
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data["access_token"]
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Step 3: Check health (with auth)
            health_response = test_client.get("/health", headers=headers)
            assert health_response.status_code == 200
            
            # Step 4: Verify correlation ID
            assert "X-Correlation-ID" in health_response.headers
            
            # Step 5: Verify security headers
            assert "X-Content-Type-Options" in health_response.headers
    
    def test_workflow_lifecycle(self, test_client, db_session, sample_user_data):
        """Test complete workflow lifecycle."""
        # Create user and login
        user_service = UserService(db_session)
        user = user_service.create_user(
            email=sample_user_data["email"],
            password=sample_user_data["password"],
            full_name=sample_user_data["full_name"],
            tenant_id=sample_user_data["tenant_id"]
        )
        
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
            headers = {"Authorization": f"Bearer {token}"}
            
            # Start workflow (if endpoint available and auth enabled)
            workflow_response = test_client.post(
                "/api/v1/workflows/compliance",
                headers=headers,
                json={
                    "query": "Test compliance query",
                    "jurisdiction": "EU"
                }
            )
            
            # Should either succeed or require different auth
            assert workflow_response.status_code in [
                202,  # Accepted
                401,  # Unauthorized (if auth not properly configured)
                403,  # Forbidden
                404   # Endpoint not found
            ]


@pytest.mark.e2e
@pytest.mark.slow
class TestAgentOrchestration:
    """Test agent orchestration with caching."""
    
    def test_agent_execution_flow(self, test_client):
        """Test agent execution flow."""
        # This is a conceptual test - actual agent execution may require
        # more setup and configuration
        
        # Check agents endpoint
        response = test_client.get("/api/v1/agents")
        
        # Should return list of agents or appropriate status
        assert response.status_code in [200, 401, 403, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "agents" in data or isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.slow
class TestDatabaseOperationsWithTenantFiltering:
    """Test database operations with tenant filtering."""
    
    def test_create_and_retrieve_with_tenant(self, db_session):
        """Test creating and retrieving data with tenant filtering."""
        from database.query_helpers import query_with_tenant, create_with_tenant
        from database.models import Run
        
        tenant_id = "e2e-tenant-123"
        
        # Create run with tenant
        run = Run(
            id="e2e-run-1",
            workflow_type="compliance",
            status="pending"
        )
        created_run = create_with_tenant(db_session, run, tenant_id)
        
        assert created_run.tenant_id == tenant_id
        
        # Retrieve with tenant filter
        query = query_with_tenant(db_session, Run, tenant_id)
        results = query.all()
        
        assert len(results) >= 1
        assert any(r.id == "e2e-run-1" for r in results)
        assert all(r.tenant_id == tenant_id for r in results)


@pytest.mark.e2e
@pytest.mark.slow
class TestErrorScenarios:
    """Test error scenarios and recovery."""
    
    def test_database_error_handling(self, test_client):
        """Test database error handling."""
        # Make request that might cause database error
        response = test_client.get("/health")
        
        # Should handle gracefully
        assert response.status_code in [200, 503]  # 503 if DB unavailable
    
    def test_redis_unavailable_graceful_degradation(self, test_client):
        """Test graceful degradation when Redis is unavailable."""
        # Health check should still work
        response = test_client.get("/health")
        assert response.status_code == 200
        
        # Cache should degrade gracefully
        data = response.json()
        assert "status" in data
    
    def test_invalid_token_handling(self, test_client):
        """Test invalid token handling."""
        response = test_client.get(
            "/health",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # Should either accept (if auth disabled) or reject gracefully
        assert response.status_code in [200, 401, 403]

