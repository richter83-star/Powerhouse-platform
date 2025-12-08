"""
Tests for database models.
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import User, Tenant, UserTenant, Run


@pytest.mark.unit
@pytest.mark.database
class TestUserModel:
    """Test User model."""
    
    def test_create_user(self, db_session: Session):
        """Test creating a user."""
        user = User(
            id="test-user-123",
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
            is_active=1,
            is_verified=0
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved_user = db_session.query(User).filter(User.id == "test-user-123").first()
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.full_name == "Test User"
    
    def test_user_relationships(self, db_session: Session):
        """Test user relationships."""
        user = User(
            id="test-user-123",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Check that relationships are accessible
        assert hasattr(user, "refresh_tokens")
        assert hasattr(user, "login_attempts")
        assert hasattr(user, "user_tenants")


@pytest.mark.unit
@pytest.mark.database
class TestTenantModel:
    """Test Tenant model."""
    
    def test_create_tenant(self, db_session: Session):
        """Test creating a tenant."""
        tenant = Tenant(
            id="test-tenant-123",
            name="Test Tenant",
            subscription_tier="pro"
        )
        db_session.add(tenant)
        db_session.commit()
        
        retrieved_tenant = db_session.query(Tenant).filter(Tenant.id == "test-tenant-123").first()
        assert retrieved_tenant is not None
        assert retrieved_tenant.name == "Test Tenant"


@pytest.mark.unit
@pytest.mark.database
class TestUserTenantModel:
    """Test UserTenant model."""
    
    def test_create_user_tenant_association(self, db_session: Session):
        """Test creating user-tenant association."""
        user = User(
            id="test-user-123",
            email="test@example.com",
            password_hash="hashed_password"
        )
        tenant = Tenant(
            id="test-tenant-123",
            name="Test Tenant"
        )
        db_session.add(user)
        db_session.add(tenant)
        db_session.commit()
        
        user_tenant = UserTenant(
            user_id=user.id,
            tenant_id=tenant.id,
            role="admin"
        )
        db_session.add(user_tenant)
        db_session.commit()
        
        retrieved = db_session.query(UserTenant).filter(
            UserTenant.user_id == user.id,
            UserTenant.tenant_id == tenant.id
        ).first()
        
        assert retrieved is not None
        assert retrieved.role == "admin"


@pytest.mark.unit
@pytest.mark.database
class TestRunModel:
    """Test Run model with tenant isolation."""
    
    def test_create_run_with_tenant(self, db_session: Session):
        """Test creating a run with tenant ID."""
        run = Run(
            id="test-run-123",
            tenant_id="test-tenant-123",
            workflow_type="compliance",
            status="pending"
        )
        db_session.add(run)
        db_session.commit()
        
        retrieved_run = db_session.query(Run).filter(Run.id == "test-run-123").first()
        assert retrieved_run is not None
        assert retrieved_run.tenant_id == "test-tenant-123"
        assert retrieved_run.workflow_type == "compliance"

