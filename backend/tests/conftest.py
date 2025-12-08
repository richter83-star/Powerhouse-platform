"""
Pytest configuration and shared fixtures.
"""
import pytest
import asyncio
import time
from typing import Generator, AsyncGenerator
from unittest.mock import Mock
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


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = 0
    mock_redis.keys.return_value = []
    return mock_redis


@pytest.fixture
def cache_instance(mock_redis):
    """Cache instance for testing."""
    from core.cache.redis_cache import RedisCache
    return RedisCache(redis_client=mock_redis)


@pytest.fixture
def metrics_collector():
    """Metrics collector fixture."""
    from core.monitoring.metrics import REGISTRY
    # Clear metrics before test
    for collector in list(REGISTRY._collector_to_names.keys()):
        REGISTRY.unregister(collector)
    yield
    # Cleanup after test
    for collector in list(REGISTRY._collector_to_names.keys()):
        REGISTRY.unregister(collector)


@pytest.fixture
def performance_timer():
    """Performance timer utility."""
    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.end_time - self.start_time
        
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return PerformanceTimer()

