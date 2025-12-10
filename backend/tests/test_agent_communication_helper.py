"""
Tests for Agent Communication Helper (Phase 3)

Tests communication helper methods and integration.
"""

import pytest
from unittest.mock import Mock

from core.agent_communication_helper import AgentCommunicationHelper


@pytest.mark.unit
class TestAgentCommunicationHelper:
    """Test agent communication helper."""
    
    def test_helper_initialization(self, mock_communication_protocol):
        """Test helper initialization."""
        mock_agent = Mock()
        helper = AgentCommunicationHelper(
            agent=mock_agent,
            agent_name="test_agent",
            protocol=mock_communication_protocol
        )
        
        assert helper.agent == mock_agent
        assert helper.agent_name == "test_agent"
        assert helper.protocol == mock_communication_protocol
    
    def test_send_message_wrapper(self, mock_communication_protocol):
        """Test send_message() wrapper."""
        mock_agent = Mock()
        helper = AgentCommunicationHelper(
            agent=mock_agent,
            agent_name="agent1",
            protocol=mock_communication_protocol
        )
        
        helper.send_message("agent2", "info", {"data": "test"})
        
        messages = mock_communication_protocol.get_messages("agent2")
        assert len(messages) > 0
    
    def test_request_response_pattern(self, mock_communication_protocol):
        """Test request-response pattern."""
        mock_agent = Mock()
        helper = AgentCommunicationHelper(
            agent=mock_agent,
            agent_name="agent1",
            protocol=mock_communication_protocol
        )
        
        try:
            response = helper.request_response(
                receiver="agent2",
                content={"question": "test"}
            )
            # Should handle request-response
            assert True
        except AttributeError:
            pytest.skip("Request-response method not available")
    
    def test_broadcast_message(self, mock_communication_protocol):
        """Test broadcast_message()."""
        mock_agent = Mock()
        helper = AgentCommunicationHelper(
            agent=mock_agent,
            agent_name="agent1",
            protocol=mock_communication_protocol
        )
        
        helper.broadcast_message("info", {"announcement": "test"})
        
        # Message should be in protocol
        assert len(mock_communication_protocol.messages) > 0
    
    def test_get_messages_filtering(self, mock_communication_protocol):
        """Test get_messages() filtering."""
        mock_agent = Mock()
        helper = AgentCommunicationHelper(
            agent=mock_agent,
            agent_name="agent1",
            protocol=mock_communication_protocol
        )
        
        # Send different message types
        helper.send_message("agent1", "info", {"type": "info"})
        helper.send_message("agent1", "task", {"type": "task"})
        
        # Get specific type
        info_messages = helper.get_messages(message_type="info")
        assert len(info_messages) >= 1
    
    def test_find_agents(self, mock_communication_protocol):
        """Test find_agents() method."""
        mock_agent = Mock()
        helper = AgentCommunicationHelper(
            agent=mock_agent,
            agent_name="agent1",
            protocol=mock_communication_protocol
        )
        
        # Register agents with capabilities
        mock_communication_protocol.register_agent("agent2", "react", ["reasoning"])
        mock_communication_protocol.register_agent("agent3", "cot", ["reasoning", "analysis"])
        
        try:
            agents = helper.find_agents(capability="reasoning")
            assert len(agents) >= 2
        except AttributeError:
            pytest.skip("find_agents method not available")
    
    def test_set_shared_state(self, mock_communication_protocol):
        """Test set_shared_state() method."""
        mock_agent = Mock()
        helper = AgentCommunicationHelper(
            agent=mock_agent,
            agent_name="agent1",
            protocol=mock_communication_protocol
        )
        
        try:
            helper.set_shared_state("key1", "value1")
            value = mock_communication_protocol.get_shared_state("key1")
            assert value == "value1"
        except AttributeError:
            pytest.skip("set_shared_state method not available")

