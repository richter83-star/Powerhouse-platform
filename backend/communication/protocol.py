"""
High-level communication protocol that ties together all communication components.
"""

from typing import Optional, List, Dict, Any, Callable
from datetime import datetime

from .message import Message, MessageType
from .message_bus import MessageBus
from .agent_registry import AgentRegistry, AgentInfo
from .shared_context import SharedContext
from utils.logging import get_logger

logger = get_logger(__name__)


class CommunicationProtocol:
    """
    High-level communication protocol for agents.
    
    This class provides a unified interface to all communication components:
    - Message bus for messaging
    - Agent registry for discovery
    - Shared context for state sharing
    
    Agents interact with this protocol rather than individual components,
    making it easier to use and ensuring consistent behavior.
    """
    
    def __init__(
        self,
        message_bus: Optional[MessageBus] = None,
        agent_registry: Optional[AgentRegistry] = None,
        shared_context: Optional[SharedContext] = None
    ):
        """
        Initialize communication protocol.
        
        Args:
            message_bus: Message bus instance (creates new if None)
            agent_registry: Agent registry instance (creates new if None)
            shared_context: Shared context instance (creates new if None)
        """
        self.message_bus = message_bus or MessageBus()
        self.agent_registry = agent_registry or AgentRegistry()
        self.shared_context = shared_context or SharedContext()
        
        logger.info("CommunicationProtocol initialized")
    
    # ==================== Agent Lifecycle ====================
    
    def register_agent(
        self,
        name: str,
        agent_type: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentInfo:
        """
        Register an agent with the protocol.
        
        This makes the agent discoverable and ready to communicate.
        
        Args:
            name: Unique agent name
            agent_type: Type of agent
            capabilities: List of capabilities
            metadata: Additional metadata
            
        Returns:
            AgentInfo: Registered agent information
        """
        return self.agent_registry.register(
            name=name,
            agent_type=agent_type,
            capabilities=capabilities,
            metadata=metadata
        )
    
    def deregister_agent(self, name: str) -> None:
        """
        Deregister an agent.
        
        Args:
            name: Agent name
        """
        # Send shutdown notification
        self.broadcast(
            sender=name,
            message_type=MessageType.SHUTDOWN,
            content={"reason": "Agent shutting down"}
        )
        
        self.agent_registry.deregister(name)
    
    # ==================== Messaging ====================
    
    def send_message(
        self,
        sender: str,
        receiver: str,
        message_type: MessageType,
        content: Any,
        run_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: int = 5
    ) -> Message:
        """
        Send a message to another agent.
        
        Args:
            sender: Sending agent name
            receiver: Receiving agent name
            message_type: Type of message
            content: Message content
            run_id: Associated run ID
            correlation_id: Correlation ID for threading
            priority: Message priority (0-10)
            
        Returns:
            Message: The sent message
        """
        message = Message(
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            content=content,
            run_id=run_id,
            correlation_id=correlation_id,
            priority=priority
        )
        
        self.message_bus.publish(message)
        self.agent_registry.increment_message_count(sender)
        
        return message
    
    def broadcast(
        self,
        sender: str,
        message_type: MessageType,
        content: Any,
        run_id: Optional[str] = None
    ) -> Message:
        """
        Broadcast a message to all agents.
        
        Args:
            sender: Sending agent name
            message_type: Type of message
            content: Message content
            run_id: Associated run ID
            
        Returns:
            Message: The broadcast message
        """
        return self.send_message(
            sender=sender,
            receiver="broadcast",
            message_type=message_type,
            content=content,
            run_id=run_id
        )
    
    def request(
        self,
        sender: str,
        receiver: str,
        content: Any,
        run_id: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Optional[Message]:
        """
        Send a request and wait for response.
        
        Args:
            sender: Sending agent name
            receiver: Receiving agent name
            content: Request content
            run_id: Associated run ID
            timeout: Timeout in seconds
            
        Returns:
            Message: Response message or None if timeout
        """
        request_msg = self.send_message(
            sender=sender,
            receiver=receiver,
            message_type=MessageType.REQUEST,
            content=content,
            run_id=run_id
        )
        
        # Wait for response
        start_time = datetime.now()
        while True:
            messages = self.get_messages(sender)
            
            for msg in messages:
                if (msg.message_type == MessageType.RESPONSE and 
                    msg.correlation_id == request_msg.id):
                    return msg
            
            if timeout and (datetime.now() - start_time).total_seconds() > timeout:
                logger.warning(f"Request from {sender} to {receiver} timed out")
                return None
            
            # Small delay to avoid busy waiting
            import time
            time.sleep(0.1)
    
    def respond(
        self,
        sender: str,
        original_message: Message,
        content: Any
    ) -> Message:
        """
        Respond to a message.
        
        Args:
            sender: Responding agent name
            original_message: Message being responded to
            content: Response content
            
        Returns:
            Message: Response message
        """
        return self.send_message(
            sender=sender,
            receiver=original_message.sender,
            message_type=MessageType.RESPONSE,
            content=content,
            run_id=original_message.run_id,
            correlation_id=original_message.id
        )
    
    def get_messages(
        self,
        agent_name: str,
        max_messages: Optional[int] = None
    ) -> List[Message]:
        """
        Get pending messages for an agent.
        
        Args:
            agent_name: Agent name
            max_messages: Maximum messages to retrieve
            
        Returns:
            List[Message]: List of messages
        """
        return self.message_bus.get_messages(agent_name, max_messages)
    
    def subscribe(self, agent_name: str, message_type: MessageType) -> None:
        """
        Subscribe to a message type.
        
        Args:
            agent_name: Agent name
            message_type: Type to subscribe to
        """
        self.message_bus.subscribe(agent_name, message_type)
    
    # ==================== Discovery ====================
    
    def find_agents(
        self,
        agent_type: Optional[str] = None,
        capability: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[AgentInfo]:
        """
        Find agents matching criteria.
        
        Args:
            agent_type: Filter by type
            capability: Filter by capability
            status: Filter by status
            
        Returns:
            List[AgentInfo]: Matching agents
        """
        return self.agent_registry.list_agents(
            agent_type=agent_type,
            status=status,
            capability=capability
        )
    
    def get_agent_info(self, name: str) -> Optional[AgentInfo]:
        """
        Get information about a specific agent.
        
        Args:
            name: Agent name
            
        Returns:
            AgentInfo: Agent information or None
        """
        return self.agent_registry.get_agent(name)
    
    def find_by_capability(self, capability: str) -> List[str]:
        """
        Find agents with a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List[str]: List of agent names
        """
        return self.agent_registry.find_by_capability(capability)
    
    # ==================== Shared State ====================
    
    def set_state(
        self,
        key: str,
        value: Any,
        agent_name: Optional[str] = None,
        namespace: str = "global"
    ) -> None:
        """
        Set a value in shared context.
        
        Args:
            key: Key to set
            value: Value to store
            agent_name: Agent making the change
            namespace: Namespace ('global' or agent-specific)
        """
        self.shared_context.set(key, value, agent_name, namespace)
    
    def get_state(
        self,
        key: str,
        default: Any = None,
        namespace: str = "global"
    ) -> Any:
        """
        Get a value from shared context.
        
        Args:
            key: Key to retrieve
            default: Default value
            namespace: Namespace
            
        Returns:
            Any: Value or default
        """
        return self.shared_context.get(key, default, namespace)
    
    def update_state(
        self,
        updates: Dict[str, Any],
        agent_name: Optional[str] = None,
        namespace: str = "global"
    ) -> None:
        """
        Update multiple state values.
        
        Args:
            updates: Dictionary of updates
            agent_name: Agent making changes
            namespace: Namespace
        """
        self.shared_context.update(updates, agent_name, namespace)
    
    # ==================== Health & Monitoring ====================
    
    def heartbeat(self, agent_name: str) -> None:
        """
        Send a heartbeat for an agent.
        
        Args:
            agent_name: Agent name
        """
        self.agent_registry.heartbeat(agent_name)
    
    def update_agent_status(self, agent_name: str, status: str) -> None:
        """
        Update agent status.
        
        Args:
            agent_name: Agent name
            status: New status
        """
        self.agent_registry.update_status(agent_name, status)
    
    def check_health(self) -> Dict[str, str]:
        """
        Check health of all agents.
        
        Returns:
            dict: Map of agent names to health status
        """
        return self.agent_registry.check_health()
    
    # ==================== Statistics ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics.
        
        Returns:
            dict: Statistics from all components
        """
        return {
            "message_bus": self.message_bus.get_stats(),
            "agent_registry": self.agent_registry.get_stats(),
            "shared_context": self.shared_context.get_stats()
        }
    
    # ==================== Utilities ====================
    
    def reset(self) -> None:
        """Reset all components (useful for testing)."""
        self.message_bus.reset()
        self.agent_registry.reset()
        self.shared_context.reset()
        logger.info("CommunicationProtocol reset")
