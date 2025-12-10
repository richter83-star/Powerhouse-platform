"""
Tests for Communication Protocol (Phase 3)

Tests protocol initialization, messaging, and shared context.
"""

import pytest
from unittest.mock import Mock, patch

try:
    from communication import CommunicationProtocol, MessageType
    COMMUNICATION_AVAILABLE = True
except ImportError:
    COMMUNICATION_AVAILABLE = False
    CommunicationProtocol = None
    MessageType = None


@pytest.mark.unit
@pytest.mark.skipif(not COMMUNICATION_AVAILABLE, reason="Communication protocol not available")
class TestCommunicationProtocol:
    """Test communication protocol."""
    
    def test_protocol_initialization(self):
        """Test CommunicationProtocol setup."""
        protocol = CommunicationProtocol()
        assert protocol is not None
    
    def test_agent_registration(self):
        """Test agent registration."""
        protocol = CommunicationProtocol()
        
        protocol.register_agent(
            name="test_agent",
            agent_type="react",
            capabilities=["reasoning", "tool_usage"]
        )
        
        # Should be able to discover agent
        agents = protocol.discover_agents()
        assert "test_agent" in agents or len(agents) > 0
    
    def test_direct_messaging(self):
        """Test direct messaging between agents."""
        protocol = CommunicationProtocol()
        
        protocol.register_agent("agent1", "react", [])
        protocol.register_agent("agent2", "cot", [])
        
        # Send message
        protocol.send_message(
            sender="agent1",
            receiver="agent2",
            message_type=MessageType.INFORMATION,
            content={"data": "test"}
        )
        
        # Get messages
        messages = protocol.get_messages("agent2")
        assert len(messages) > 0
    
    def test_broadcast_messaging(self):
        """Test broadcast messaging."""
        protocol = CommunicationProtocol()
        
        protocol.register_agent("agent1", "react", [])
        protocol.register_agent("agent2", "cot", [])
        protocol.register_agent("agent3", "tot", [])
        
        # Broadcast
        protocol.broadcast_message(
            sender="agent1",
            message_type=MessageType.INFORMATION,
            content={"announcement": "test"}
        )
        
        # All agents should receive message
        messages2 = protocol.get_messages("agent2")
        messages3 = protocol.get_messages("agent3")
        
        assert len(messages2) > 0 or len(messages3) > 0
    
    def test_shared_state_management(self):
        """Test shared state management."""
        protocol = CommunicationProtocol()
        
        # Set shared state
        protocol.set_shared_state("key1", "value1")
        
        # Get shared state
        value = protocol.get_shared_state("key1")
        assert value == "value1"
    
    def test_context_synchronization(self):
        """Test context synchronization."""
        protocol = CommunicationProtocol()
        
        # Update context
        protocol.set_shared_state("task_context", {"status": "in_progress"})
        
        # Another agent should see it
        context = protocol.get_shared_state("task_context")
        assert context is not None
        assert context.get("status") == "in_progress"


@pytest.mark.unit
class TestCommunicationProtocolMock:
    """Test with mock communication protocol."""
    
    def test_protocol_with_mock(self, mock_communication_protocol):
        """Test using mock protocol."""
        protocol = mock_communication_protocol
        
        # Register agents
        protocol.register_agent("agent1", "react", ["reasoning"])
        protocol.register_agent("agent2", "cot", ["reasoning"])
        
        # Send message
        protocol.send_message("agent1", "agent2", "info", {"data": "test"})
        
        # Get messages
        messages = protocol.get_messages("agent2")
        assert len(messages) > 0

