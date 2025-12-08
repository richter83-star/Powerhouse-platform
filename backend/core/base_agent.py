"""
Base agent class that all agents must inherit from.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime

from communication import CommunicationProtocol, Message, MessageType
from llm import BaseLLMProvider
from utils.logging import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    All agents in the platform must inherit from this class and implement
    the execute() method. This ensures consistent behavior and enables
    seamless communication between agents.
    
    Attributes:
        name: Unique agent name
        agent_type: Type/class of agent
        capabilities: List of capabilities this agent provides
        protocol: Communication protocol for inter-agent communication
        llm_provider: LLM provider for AI capabilities
    """
    
    def __init__(
        self,
        name: str,
        agent_type: str,
        capabilities: Optional[List[str]] = None,
        protocol: Optional[CommunicationProtocol] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base agent.
        
        Args:
            name: Unique agent name
            agent_type: Type of agent
            capabilities: List of capabilities
            protocol: Communication protocol
            llm_provider: LLM provider
            metadata: Additional metadata
        """
        self.name = name
        self.agent_type = agent_type
        self.capabilities = capabilities or []
        self.protocol = protocol
        self.llm_provider = llm_provider
        self.metadata = metadata or {}
        
        self._is_registered = False
        self._run_id: Optional[str] = None
        
        logger.info(f"Initialized agent: {name} (type={agent_type})")
    
    def register(self, protocol: CommunicationProtocol) -> None:
        """
        Register this agent with the communication protocol.
        
        Args:
            protocol: Communication protocol to register with
        """
        if self._is_registered:
            logger.warning(f"Agent {self.name} already registered")
            return
        
        self.protocol = protocol
        self.protocol.register_agent(
            name=self.name,
            agent_type=self.agent_type,
            capabilities=self.capabilities,
            metadata=self.metadata
        )
        self._is_registered = True
        logger.info(f"Agent {self.name} registered with protocol")
    
    def deregister(self) -> None:
        """Deregister this agent from the protocol."""
        if not self._is_registered or not self.protocol:
            return
        
        self.protocol.deregister_agent(self.name)
        self._is_registered = False
        logger.info(f"Agent {self.name} deregistered")
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        
        This is the core method that must be implemented by all agents.
        
        Args:
            input_data: Input data for this agent
            context: Shared context from orchestrator
            
        Returns:
            dict: Output data with keys:
                - status: 'success', 'failure', or 'partial'
                - output: The agent's output
                - metadata: Additional metadata (metrics, etc.)
                - next_actions: Optional list of suggested next steps
        """
        pass
    
    # ==================== Communication Helpers ====================
    
    def send_message(
        self,
        receiver: str,
        message_type: MessageType,
        content: Any,
        correlation_id: Optional[str] = None
    ) -> Message:
        """
        Send a message to another agent.
        
        Args:
            receiver: Receiving agent name
            message_type: Type of message
            content: Message content
            correlation_id: Correlation ID
            
        Returns:
            Message: Sent message
        """
        if not self.protocol:
            raise RuntimeError(f"Agent {self.name} not registered with protocol")
        
        return self.protocol.send_message(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            content=content,
            run_id=self._run_id,
            correlation_id=correlation_id
        )
    
    def broadcast(self, message_type: MessageType, content: Any) -> Message:
        """
        Broadcast a message to all agents.
        
        Args:
            message_type: Type of message
            content: Message content
            
        Returns:
            Message: Broadcast message
        """
        if not self.protocol:
            raise RuntimeError(f"Agent {self.name} not registered with protocol")
        
        return self.protocol.broadcast(
            sender=self.name,
            message_type=message_type,
            content=content,
            run_id=self._run_id
        )
    
    def get_messages(self, max_messages: Optional[int] = None) -> List[Message]:
        """
        Get pending messages for this agent.
        
        Args:
            max_messages: Maximum messages to retrieve
            
        Returns:
            List[Message]: List of messages
        """
        if not self.protocol:
            return []
        
        return self.protocol.get_messages(self.name, max_messages)
    
    def request(
        self,
        receiver: str,
        content: Any,
        timeout: Optional[float] = 30.0
    ) -> Optional[Message]:
        """
        Send a request and wait for response.
        
        Args:
            receiver: Receiving agent name
            content: Request content
            timeout: Timeout in seconds
            
        Returns:
            Message: Response message or None
        """
        if not self.protocol:
            raise RuntimeError(f"Agent {self.name} not registered with protocol")
        
        return self.protocol.request(
            sender=self.name,
            receiver=receiver,
            content=content,
            run_id=self._run_id,
            timeout=timeout
        )
    
    def respond(self, original_message: Message, content: Any) -> Message:
        """
        Respond to a message.
        
        Args:
            original_message: Message being responded to
            content: Response content
            
        Returns:
            Message: Response message
        """
        if not self.protocol:
            raise RuntimeError(f"Agent {self.name} not registered with protocol")
        
        return self.protocol.respond(self.name, original_message, content)
    
    # ==================== State Management ====================
    
    def set_state(self, key: str, value: Any, namespace: str = "global") -> None:
        """
        Set a value in shared context.
        
        Args:
            key: Key to set
            value: Value to store
            namespace: Namespace ('global' or agent-specific)
        """
        if not self.protocol:
            raise RuntimeError(f"Agent {self.name} not registered with protocol")
        
        self.protocol.set_state(key, value, self.name, namespace)
    
    def get_state(self, key: str, default: Any = None, namespace: str = "global") -> Any:
        """
        Get a value from shared context.
        
        Args:
            key: Key to retrieve
            default: Default value
            namespace: Namespace
            
        Returns:
            Any: Value or default
        """
        if not self.protocol:
            return default
        
        return self.protocol.get_state(key, default, namespace)
    
    # ==================== Discovery ====================
    
    def find_agents(
        self,
        agent_type: Optional[str] = None,
        capability: Optional[str] = None
    ) -> List[str]:
        """
        Find other agents matching criteria.
        
        Args:
            agent_type: Filter by type
            capability: Filter by capability
            
        Returns:
            List[str]: List of agent names
        """
        if not self.protocol:
            return []
        
        agents = self.protocol.find_agents(agent_type=agent_type, capability=capability)
        return [a.name for a in agents if a.name != self.name]
    
    # ==================== LLM Helpers ====================
    
    def invoke_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Invoke the LLM provider.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            str: LLM response content
        """
        if not self.llm_provider:
            raise RuntimeError(f"Agent {self.name} has no LLM provider configured")
        
        response = self.llm_provider.invoke(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            **kwargs
        )
        
        return response.content
    
    # ==================== Lifecycle ====================
    
    def set_run_id(self, run_id: str) -> None:
        """
        Set the current run ID.
        
        Args:
            run_id: Run ID
        """
        self._run_id = run_id
    
    def heartbeat(self) -> None:
        """Send a heartbeat to indicate this agent is alive."""
        if self.protocol:
            self.protocol.heartbeat(self.name)
    
    def update_status(self, status: str) -> None:
        """
        Update agent status.
        
        Args:
            status: New status ('active', 'idle', 'busy', 'offline')
        """
        if self.protocol:
            self.protocol.update_agent_status(self.name, status)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}(name={self.name}, type={self.agent_type})>"
