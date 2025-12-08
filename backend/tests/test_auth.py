"""
Unit and integration tests for authentication endpoints.
"""
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from core.security.user_service import UserService
from database.models import User, Tenant


@pytest.mark.unit
@pytest.mark.auth
class TestUserService:
    """Test UserService functionality."""
    
    def test_create_user(self, db_session: Session, sample_user_data):
        """Test user creation."""
        user_service = UserService(db_session)
        
        user = user_service.create_user(
            email=sample_user_data["email"],
            password=sample_user_data["password"],
            full_name=sample_user_data["full_name"],
            tenant_id=sample_user_data["tenant_id"],
            company_name=sample_user_data.get("company_name")
        )
        
        assert user is not None
        assert user.email == sample_user_data["email"]
        assert user.full_name == sample_user_data["full_name"]
        assert user.is_active == 1
        assert user.is_verified == 0  # Not verified by default
    
    def test_get_user_by_email(self, db_session: Session, sample_user_data):
        """Test retrieving user by email."""
        user_service = UserService(db_session)
        
        # Create user first
        user_service.create_user(
            email=sample_user_data["email"],
            password=sample_user_data["password"],
            full_name=sample_user_data["full_name"],
            tenant_id=sample_user_data["tenant_id"]
        )
        
        # Retrieve user
        user = user_service.get_user_by_email(sample_user_data["email"])
        assert user is not None
        assert user.email == sample_user_data["email"]
    
    def test_verify_password(self, db_session: Session, sample_user_data):
        """Test password verification."""
        user_service = UserService(db_session)
        
        # Create user
        user = user_service.create_user(
            email=sample_user_data["email"],
            password=sample_user_data["password"],
            full_name=sample_user_data["full_name"],
            tenant_id=sample_user_data["tenant_id"]
        )
        
        # Verify correct password
        assert user_service.verify_password(
            sample_user_data["password"],
            user.password_hash
        ) is True
        
        # Verify incorrect password
        assert user_service.verify_password(
            "wrong_password",
            user.password_hash
        ) is False


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    def test_signup_endpoint(self, test_client, sample_user_data):
        """Test user signup endpoint."""
        response = test_client.post(
            "/api/auth/signup",
            json=sample_user_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "user_id" in data or "message" in data
    
    def test_login_endpoint_success(self, test_client, db_session, sample_user_data):
        """Test successful login."""
        # Create user first
        user_service = UserService(db_session)
        user_service.create_user(
            email=sample_user_data["email"],
            password=sample_user_data["password"],
            full_name=sample_user_data["full_name"],
            tenant_id=sample_user_data["tenant_id"]
        )
        
        # Login
        response = test_client.post(
            "/api/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
                "tenant_id": sample_user_data["tenant_id"]
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_endpoint_invalid_credentials(self, test_client):
        """Test login with invalid credentials."""
        response = test_client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
                "tenant_id": "test-tenant"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_endpoint_validation_error(self, test_client):
        """Test login with invalid request data."""
        response = test_client.post(
            "/api/auth/login",
            json={
                "email": "invalid-email",  # Invalid email format
                "password": "short",  # Too short
                "tenant_id": ""
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_refresh_token_endpoint(self, test_client, db_session, sample_user_data):
        """Test token refresh endpoint."""
        # Create user and login
        user_service = UserService(db_session)
        user_service.create_user(
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
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

