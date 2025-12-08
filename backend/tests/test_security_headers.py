"""
Tests for security headers middleware.
"""
import pytest
from fastapi.testclient import TestClient

from api.middleware.security_headers import SecurityHeadersMiddleware


@pytest.mark.unit
@pytest.mark.security
class TestSecurityHeaders:
    """Test security headers middleware."""
    
    def test_security_headers_present(self, test_client):
        """Test that all security headers are present in response."""
        response = test_client.get("/health")
        
        # Check required security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers
        assert "X-Permitted-Cross-Domain-Policies" in response.headers
    
    def test_csp_header_present(self, test_client):
        """Test that Content-Security-Policy header is present."""
        response = test_client.get("/health")
        
        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
    
    def test_hsts_header_https_only(self, test_client):
        """Test HSTS header only on HTTPS requests."""
        # For HTTP (localhost), HSTS should not be present
        response = test_client.get("/health")
        
        # HSTS should not be present for HTTP
        assert "Strict-Transport-Security" not in response.headers or \
               response.url.startswith("https://")
    
    def test_server_header_removed(self, test_client):
        """Test that Server header is removed."""
        response = test_client.get("/health")
        
        # Server header should not be present (security through obscurity)
        assert "Server" not in response.headers
    
    def test_security_headers_values(self, test_client):
        """Test that security headers have correct values."""
        response = test_client.get("/health")
        
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"
    
    def test_csp_configuration(self, test_client):
        """Test CSP header configuration."""
        response = test_client.get("/health")
        csp = response.headers["Content-Security-Policy"]
        
        # Check CSP contains essential directives
        assert "default-src 'self'" in csp
        assert "script-src" in csp
        assert "style-src" in csp
        assert "img-src" in csp
    
    def test_permissions_policy(self, test_client):
        """Test Permissions-Policy header."""
        response = test_client.get("/health")
        permissions = response.headers["Permissions-Policy"]
        
        # Check that dangerous features are disabled
        assert "geolocation=()" in permissions
        assert "microphone=()" in permissions
        assert "camera=()" in permissions


@pytest.mark.integration
@pytest.mark.security
class TestSecurityHeadersIntegration:
    """Integration tests for security headers."""
    
    def test_security_headers_all_endpoints(self, test_client):
        """Test security headers on multiple endpoints."""
        endpoints = ["/", "/health", "/docs", "/openapi.json"]
        
        for endpoint in endpoints:
            response = test_client.get(endpoint)
            
            # All endpoints should have security headers
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
    
    def test_security_headers_post_request(self, test_client):
        """Test security headers on POST requests."""
        response = test_client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "test", "tenant_id": "test"}
        )
        
        # POST responses should also have security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers

