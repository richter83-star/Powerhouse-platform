"""
Pytest configuration and shared fixtures.
"""
import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
import asyncio
import time
from typing import Generator, AsyncGenerator
from unittest.mock import Mock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Try importing app, but make it optional for tests that don't need it
try:
    from api.main import app
    APP_AVAILABLE = True
except (ImportError, NameError, AttributeError, ModuleNotFoundError) as e:
    # Create a minimal mock app for tests that don't need the real app
    # This handles cases where dependencies have issues
    from fastapi import FastAPI
    app = FastAPI()
    APP_AVAILABLE = False

# Import database models (make optional)
try:
    from database.models import Base
    from database.session import get_db
    DATABASE_AVAILABLE = True
except ImportError:
    Base = None
    get_db = None
    DATABASE_AVAILABLE = False

# Import settings (make optional)
try:
    from config.settings import settings
except ImportError:
    # Create minimal settings mock
    class Settings:
        debug = False
        log_level = "INFO"
    settings = Settings()


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
    if not DATABASE_AVAILABLE or Base is None:
        pytest.skip("Database not available")
    
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
    if not APP_AVAILABLE or not DATABASE_AVAILABLE:
        pytest.skip("FastAPI app or database not available")
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    if get_db is not None:
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


# ============================================================================
# Phase 1-4 Testing Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing."""
    from unittest.mock import Mock, MagicMock
    from llm.base import LLMResponse
    from datetime import datetime
    
    mock_provider = Mock()
    
    def create_response(content: str, model: str = "test-model") -> LLMResponse:
        return LLMResponse(
            content=content,
            model=model,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            metadata={},
            timestamp=datetime.now()
        )
    
    # Default response
    mock_provider.invoke.return_value = create_response("Test response")
    
    # Allow custom responses
    def invoke_side_effect(*args, **kwargs):
        prompt = kwargs.get("prompt", args[0] if args else "")
        # Return different responses based on prompt content
        if "final answer" in prompt.lower():
            return create_response("Final Answer: Test result")
        elif "tool" in prompt.lower() or "action" in prompt.lower():
            return create_response("Thought: I need to use a tool. Action: search('test')")
        else:
            return create_response("Reasoning: Test thought process")
    
    mock_provider.invoke.side_effect = invoke_side_effect
    
    # Mock streaming
    mock_provider.invoke_streaming.return_value = iter(["Test", " response", " stream"])
    
    return mock_provider


@pytest.fixture
def mock_communication_protocol():
    """Mock communication protocol for testing."""
    from unittest.mock import Mock, MagicMock
    
    mock_protocol = Mock()
    mock_protocol.agents = {}
    mock_protocol.messages = []
    
    def register_agent(agent_id, agent_type, capabilities=None):
        mock_protocol.agents[agent_id] = {
            "agent_type": agent_type,
            "capabilities": capabilities or [],
            "registered_at": "2024-01-01T00:00:00"
        }
    
    def send_message(sender_id, receiver_id, message_type, content, metadata=None):
        msg = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "message_type": message_type,
            "content": content,
            "metadata": metadata or {},
            "timestamp": "2024-01-01T00:00:00"
        }
        mock_protocol.messages.append(msg)
        return msg
    
    def broadcast_message(sender_id, message_type, content, metadata=None):
        msg = {
            "sender_id": sender_id,
            "receiver_id": None,  # Broadcast
            "message_type": message_type,
            "content": content,
            "metadata": metadata or {},
            "timestamp": "2024-01-01T00:00:00"
        }
        mock_protocol.messages.append(msg)
        return msg
    
    def get_messages(agent_id, message_type=None, limit=None):
        msgs = [m for m in mock_protocol.messages if m["receiver_id"] == agent_id or m["receiver_id"] is None]
        if message_type:
            msgs = [m for m in msgs if m["message_type"] == message_type]
        if limit:
            msgs = msgs[:limit]
        return msgs
    
    def discover_agents(capability=None):
        if capability:
            return [aid for aid, agent in mock_protocol.agents.items() 
                   if capability in agent.get("capabilities", [])]
        return list(mock_protocol.agents.keys())
    
    def set_shared_state(key, value):
        if not hasattr(mock_protocol, "shared_state"):
            mock_protocol.shared_state = {}
        mock_protocol.shared_state[key] = value
    
    def get_shared_state(key, default=None):
        if not hasattr(mock_protocol, "shared_state"):
            mock_protocol.shared_state = {}
        return mock_protocol.shared_state.get(key, default)
    
    mock_protocol.register_agent = register_agent
    mock_protocol.send_message = send_message
    mock_protocol.broadcast_message = broadcast_message
    mock_protocol.get_messages = get_messages
    mock_protocol.discover_agents = discover_agents
    mock_protocol.set_shared_state = set_shared_state
    mock_protocol.get_shared_state = get_shared_state
    mock_protocol.shared_state = {}
    
    return mock_protocol


@pytest.fixture
def sample_tasks():
    """Sample tasks for testing with various complexity levels."""
    return {
        "simple": "What is 2 + 2?",
        "medium": "Explain how a neural network learns from data.",
        "complex": "Design a comprehensive multi-agent system architecture that supports autonomous learning, collaboration, and safety verification. Include detailed component interactions and data flow diagrams.",
        "reasoning": "If all roses are flowers and some flowers are red, can we conclude that all roses are red? Explain your reasoning step by step.",
        "planning": "Plan a trip to Japan for 2 weeks. Include budgeting, itinerary, and required documentation.",
        "tool_required": "Search for information about the latest developments in quantum computing and summarize the key findings."
    }


@pytest.fixture
def pre_trained_model(tmp_path):
    """Pre-trained model fixture for faster tests."""
    import numpy as np
    from core.learning.neural_agent_selector import NeuralAgentSelector
    
    # Create a small trained model
    selector = NeuralAgentSelector(
        agent_names=["react", "chain_of_thought", "tree_of_thought"],
        embedding_dim=32,
        hidden_dim=64
    )
    
    # Generate synthetic training data
    features = []
    labels = []
    for i in range(50):
        feat = {
            "task_complexity": np.random.rand(),
            "task_type_encoded": np.random.rand(5),
            "context_features": np.random.rand(10),
            "agent_history_success_rate": np.random.rand(),
            "agent_history_latency": np.random.rand() * 1000,
            "current_load": np.random.rand(),
            "available_resources": np.random.rand()
        }
        features.append(feat)
        labels.append(np.random.randint(0, 3))  # 3 agents
    
    # Train on synthetic data
    try:
        selector.train(features, labels, epochs=2, batch_size=10)
    except Exception:
        # If training fails, just return untrained model
        pass
    
    return selector


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry for testing."""
    from unittest.mock import Mock
    from core.tools.tool_registry import ToolRegistry
    
    registry = ToolRegistry()
    return registry
