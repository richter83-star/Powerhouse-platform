"""
Helper utilities for enabling agent-to-agent communication.
"""

from typing import Dict, Any, Optional, List
from communication import CommunicationProtocol, MessageType
from utils.logging import get_logger

logger = get_logger(__name__)


class AgentCommunicationHelper:
    """
    Helper class to enable communication for agents that don't natively support it.
    
    Wraps agents to add communication capabilities without requiring
    them to inherit from BaseAgent.
    """
    
    def __init__(self, agent, agent_name: str, protocol: CommunicationProtocol):
        """
        Initialize communication helper.
        
        Args:
            agent: The agent instance to wrap
            agent_name: Name of the agent
            protocol: Communication protocol instance
        """
        self.agent = agent
        self.agent_name = agent_name
        self.protocol = protocol
    
    def run_with_communication(self, context: Dict[str, Any]) -> Any:
        """
        Run agent with communication enabled.
        
        Before execution:
        - Checks for messages from other agents
        - Updates shared context
        
        After execution:
        - Stores output in shared context
        - Allows agent to send messages
        
        Args:
            context: Execution context
            
        Returns:
            Agent output
        """
        # Check for incoming messages
        messages = self.protocol.get_messages(self.agent_name)
        if messages:
            logger.debug(f"Agent {self.agent_name} received {len(messages)} messages")
            
            # Add messages to context
            if "messages" not in context:
                context["messages"] = []
            context["messages"].extend([self._message_to_dict(msg) for msg in messages])
            
            # Process task assignment messages
            for msg in messages:
                if msg.message_type == MessageType.TASK_ASSIGNMENT:
                    # Agent has been assigned a task
                    if "delegated_tasks" not in context:
                        context["delegated_tasks"] = []
                    context["delegated_tasks"].append({
                        "task": msg.content.get("task"),
                        "from": msg.sender,
                        "context": msg.content.get("context", {})
                    })
        
        # Check shared context for updates
        shared_state = self.protocol.shared_context.get_all("global")
        if shared_state:
            context["shared_state"] = shared_state
        
        # Execute agent
        try:
            output = self.agent.run(context)
        except Exception as e:
            logger.error(f"Agent {self.agent_name} execution failed: {e}", exc_info=True)
            raise
        
        # Store output in shared context
        output_key = f"{self.agent_name}_output"
        self.protocol.shared_context.set(output_key, output, namespace="global")
        
        # Check if output contains delegation request
        if isinstance(output, dict):
            # Check for delegation
            if "delegate_to" in output:
                self._handle_delegation_request(output, context)
            
            # Check for messages to send
            if "send_message" in output:
                self._send_agent_message(output["send_message"])
            
            # Check for broadcast
            if "broadcast" in output:
                self._broadcast_agent_message(output["broadcast"])
        
        return output
    
    def _handle_delegation_request(self, output: Dict[str, Any], context: Dict[str, Any]):
        """Handle delegation request from agent output."""
        delegate_to = output.get("delegate_to")
        delegation_task = output.get("delegation_task", context.get("task", ""))
        
        logger.info(f"Agent {self.agent_name} requesting delegation to {delegate_to}")
        
        # Store delegation request in output
        output["_delegation_request"] = {
            "to": delegate_to,
            "task": delegation_task
        }
    
    def _send_agent_message(self, message_config: Dict[str, Any]):
        """Send message on behalf of agent."""
        receiver = message_config.get("receiver")
        content = message_config.get("content", {})
        message_type_str = message_config.get("message_type", "NOTIFICATION")
        
        try:
            message_type = MessageType[message_type_str]
        except KeyError:
            logger.warning(f"Unknown message type: {message_type_str}, using NOTIFICATION")
            message_type = MessageType.NOTIFICATION
        
        self.protocol.send_message(
            sender=self.agent_name,
            receiver=receiver,
            message_type=message_type,
            content=content
        )
    
    def _broadcast_agent_message(self, broadcast_config: Dict[str, Any]):
        """Broadcast message on behalf of agent."""
        content = broadcast_config.get("content", {})
        message_type_str = broadcast_config.get("message_type", "NOTIFICATION")
        
        try:
            message_type = MessageType[message_type_str]
        except KeyError:
            message_type = MessageType.NOTIFICATION
        
        self.protocol.broadcast(
            sender=self.agent_name,
            message_type=message_type,
            content=content
        )
    
    def _message_to_dict(self, message) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": getattr(message, "id", None),
            "sender": getattr(message, "sender", None),
            "receiver": getattr(message, "receiver", None),
            "message_type": str(getattr(message, "message_type", None)),
            "content": getattr(message, "content", None),
            "timestamp": getattr(message, "timestamp", None)
        }


def enable_agent_communication(
    agent,
    agent_name: str,
    protocol: CommunicationProtocol
) -> AgentCommunicationHelper:
    """
    Enable communication for an agent.
    
    Args:
        agent: Agent instance
        agent_name: Agent name
        protocol: Communication protocol
        
    Returns:
        Communication helper wrapper
    """
    return AgentCommunicationHelper(agent, agent_name, protocol)

