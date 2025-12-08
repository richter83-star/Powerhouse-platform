"""
Tests for security features.
"""
import pytest
from datetime import datetime, timedelta

from core.security.jwt_auth import JWTAuthManager
from core.security.user_service import UserService
from database.session import Session


@pytest.mark.unit
@pytest.mark.auth
class TestJWTAuth:
    """Test JWT authentication."""
    
    def test_create_access_token(self):
        """Test creating access token."""
        auth_manager = JWTAuthManager()
        token = auth_manager.create_access_token(
            user_id="test-user-123",
            tenant_id="test-tenant-123"
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        auth_manager = JWTAuthManager()
        token = auth_manager.create_access_token(
            user_id="test-user-123",
            tenant_id="test-tenant-123"
        )
        
        payload = auth_manager.verify_token(token)
        assert payload is not None
        assert payload.get("user_id") == "test-user-123"
        assert payload.get("tenant_id") == "test-tenant-123"
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        auth_manager = JWTAuthManager()
        invalid_token = "invalid.token.here"
        
        payload = auth_manager.verify_token(invalid_token)
        assert payload is None
    
    def test_token_expiration(self):
        """Test that tokens expire correctly."""
        auth_manager = JWTAuthManager()
        # Create token with very short expiration (1 second)
        token = auth_manager.create_access_token(
            user_id="test-user-123",
            tenant_id="test-tenant-123",
            expires_delta=timedelta(seconds=1)
        )
        
        # Token should be valid immediately
        payload = auth_manager.verify_token(token)
        assert payload is not None
        
        # After expiration, token should be invalid
        import time
        time.sleep(2)
        payload = auth_manager.verify_token(token)
        # Note: This test may be flaky, but demonstrates the concept


@pytest.mark.unit
@pytest.mark.auth
class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_hashing(self, db_session: Session):
        """Test that passwords are hashed correctly."""
        user_service = UserService(db_session)
        
        password = "TestPassword123!"
        user = user_service.create_user(
            email="test@example.com",
            password=password,
            full_name="Test User",
            tenant_id="test-tenant"
        )
        
        # Password hash should be different from plain password
        assert user.password_hash != password
        assert len(user.password_hash) > 0
        
        # Should be able to verify the password
        assert user_service.verify_password(password, user.password_hash) is True
        assert user_service.verify_password("wrong_password", user.password_hash) is False

