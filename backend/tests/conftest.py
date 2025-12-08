"""
Pytest configuration and shared fixtures.
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from api.main import app
from database.models import Base
from database.session import get_db
from config.settings import settings


# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a test database session.
    Uses in-memory SQLite for fast tests.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client for FastAPI.
    Overrides database dependency with test session.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "company_name": "Test Company",
        "tenant_id": "test-tenant-123"
    }


@pytest.fixture
def sample_tenant_data():
    """Sample tenant data for testing."""
    return {
        "id": "test-tenant-123",
        "name": "Test Tenant",
        "subscription_tier": "pro"
    }


@pytest.fixture
def sample_workflow_data():
    """Sample workflow request data for testing."""
    return {
        "query": "Analyze our data retention policy for GDPR compliance",
        "jurisdiction": "EU",
        "risk_threshold": 0.8,
        "policy_documents": ["https://example.com/policy.pdf"]
    }


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzA0MTAwMDAwfQ.test"


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings to defaults before each test."""
    original_debug = settings.debug
    original_log_level = settings.log_level
    yield
    settings.debug = original_debug
    settings.log_level = original_log_level

