"""
Message format and types for inter-agent communication.
"""

from enum import Enum
from typing import Any, Optional, Dict
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json
import uuid


class MessageType(str, Enum):
    """
    Types of messages that can be sent between agents.
    """
    # Direct communication
    REQUEST = "request"           # Request for action/information
    RESPONSE = "response"         # Response to a request
    NOTIFICATION = "notification" # One-way notification
    
    # Coordination
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    
    # Collaboration
    QUERY = "query"              # Question to other agents
    ANSWER = "answer"            # Answer to a query
    PROPOSAL = "proposal"        # Suggest an approach
    VOTE = "vote"                # Vote on a proposal
    
    # System
    HEARTBEAT = "heartbeat"      # Agent health check
    SHUTDOWN = "shutdown"        # Agent shutting down
    ERROR = "error"              # Error notification
    
    # Broadcast
    BROADCAST = "broadcast"      # Message to all agents


@dataclass
class Message:
    """
    Standardized message format for inter-agent communication.
    
    This format ensures all agents can communicate regardless of their
    implementation details.
    
    Attributes:
        id: Unique message identifier
        sender: Name/ID of sending agent
        receiver: Name/ID of receiving agent (or "broadcast" for all)
        message_type: Type of message
        content: Message payload (can be any JSON-serializable data)
        timestamp: When message was created
        run_id: Associated run ID for tracking
        correlation_id: ID linking related messages (e.g., request/response)
        metadata: Additional metadata
        priority: Message priority (0=lowest, 10=highest)
    """
    sender: str
    receiver: str
    message_type: MessageType
    content: Any
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    run_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary.
        
        Returns:
            dict: Message as dictionary
        """
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['message_type'] = self.message_type.value
        return data
    
    def to_json(self) -> str:
        """
        Convert message to JSON string.
        
        Returns:
            str: JSON representation
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create message from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Message: Message instance
        """
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """
        Create message from JSON string.
        
        Args:
            json_str: JSON representation
            
        Returns:
            Message: Message instance
        """
        return cls.from_dict(json.loads(json_str))
    
    def create_response(
        self,
        content: Any,
        sender: str,
        message_type: MessageType = MessageType.RESPONSE
    ) -> 'Message':
        """
        Create a response message to this message.
        
        Args:
            content: Response content
            sender: Name of responding agent
            message_type: Type of response message
            
        Returns:
            Message: Response message with correlation_id set
        """
        return Message(
            sender=sender,
            receiver=self.sender,
            message_type=message_type,
            content=content,
            run_id=self.run_id,
            correlation_id=self.id,
            priority=self.priority
        )
    
    def is_broadcast(self) -> bool:
        """Check if this is a broadcast message."""
        return self.receiver.lower() == "broadcast" or self.message_type == MessageType.BROADCAST
    
    def is_for_agent(self, agent_name: str) -> bool:
        """
        Check if this message is intended for a specific agent.
        
        Args:
            agent_name: Name of agent to check
            
        Returns:
            bool: True if message is for this agent
        """
        return self.is_broadcast() or self.receiver == agent_name
    
    def __repr__(self) -> str:
        """String representation of message."""
        return (
            f"Message(id={self.id[:8]}..., "
            f"sender={self.sender}, "
            f"receiver={self.receiver}, "
            f"type={self.message_type.value})"
        )
