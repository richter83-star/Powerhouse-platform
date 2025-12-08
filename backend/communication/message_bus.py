"""
Message bus for routing messages between agents.
"""

from typing import Dict, List, Callable, Optional, Set
from collections import defaultdict, deque
from datetime import datetime, timedelta
import asyncio
from threading import Lock

from .message import Message, MessageType
from utils.logging import get_logger
from utils.errors import CommunicationError

logger = get_logger(__name__)


class MessageBus:
    """
    Central message bus for inter-agent communication.
    
    The message bus provides:
    - Direct messaging (agent-to-agent)
    - Broadcast messaging (agent-to-all)
    - Message queuing and delivery
    - Subscription-based routing
    - Message history and logging
    
    This is the core component that enables the modular business model,
    allowing any combination of agents to communicate seamlessly.
    """
    
    def __init__(
        self,
        max_queue_size: int = 1000,
        message_retention_seconds: int = 3600,
        enable_persistence: bool = True
    ):
        """
        Initialize message bus.
        
        Args:
            max_queue_size: Maximum messages per agent queue
            message_retention_seconds: How long to keep message history
            enable_persistence: Whether to persist messages to database
        """
        self._queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_queue_size))
        self._subscribers: Dict[MessageType, Set[str]] = defaultdict(set)
        self._message_history: deque = deque(maxlen=10000)
        self._lock = Lock()
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        self.max_queue_size = max_queue_size
        self.message_retention_seconds = message_retention_seconds
        self.enable_persistence = enable_persistence
        
        logger.info("MessageBus initialized")
    
    def publish(self, message: Message) -> None:
        """
        Publish a message to the bus.
        
        The message will be routed to:
        - The specific receiver (if direct message)
        - All agents (if broadcast)
        - All subscribers to the message type
        
        Args:
            message: Message to publish
            
        Raises:
            CommunicationError: If message delivery fails
        """
        try:
            with self._lock:
                # Add to history
                self._message_history.append(message)
                
                # Determine recipients
                recipients = set()
                
                if message.is_broadcast():
                    # Broadcast to all registered agents
                    recipients.update(self._queues.keys())
                    logger.debug(f"Broadcasting message {message.id} to all agents")
                else:
                    # Direct message
                    recipients.add(message.receiver)
                    logger.debug(f"Routing message {message.id} to {message.receiver}")
                
                # Add subscribers to this message type
                recipients.update(self._subscribers.get(message.message_type, set()))
                
                # Remove sender from recipients
                recipients.discard(message.sender)
                
                # Deliver to each recipient
                for recipient in recipients:
                    self._queues[recipient].append(message)
                    
                    # Call registered handlers
                    for handler in self._handlers.get(recipient, []):
                        try:
                            handler(message)
                        except Exception as e:
                            logger.error(f"Handler error for {recipient}: {e}")
                
                logger.info(
                    f"Published message {message.id[:8]} from {message.sender} "
                    f"to {len(recipients)} recipient(s)"
                )
                
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise CommunicationError(f"Message publish failed: {str(e)}")
    
    def subscribe(self, agent_name: str, message_type: MessageType) -> None:
        """
        Subscribe an agent to a specific message type.
        
        The agent will receive all messages of this type, even if not
        directly addressed to them.
        
        Args:
            agent_name: Name of subscribing agent
            message_type: Type of messages to receive
        """
        with self._lock:
            self._subscribers[message_type].add(agent_name)
            logger.info(f"Agent {agent_name} subscribed to {message_type.value}")
    
    def unsubscribe(self, agent_name: str, message_type: MessageType) -> None:
        """
        Unsubscribe an agent from a message type.
        
        Args:
            agent_name: Name of agent
            message_type: Type to unsubscribe from
        """
        with self._lock:
            self._subscribers[message_type].discard(agent_name)
            logger.info(f"Agent {agent_name} unsubscribed from {message_type.value}")
    
    def register_handler(self, agent_name: str, handler: Callable[[Message], None]) -> None:
        """
        Register a callback handler for incoming messages.
        
        Args:
            agent_name: Name of agent
            handler: Callback function that takes a Message
        """
        with self._lock:
            self._handlers[agent_name].append(handler)
            logger.info(f"Registered handler for {agent_name}")
    
    def get_messages(
        self,
        agent_name: str,
        max_messages: Optional[int] = None,
        block: bool = False,
        timeout: Optional[float] = None
    ) -> List[Message]:
        """
        Get messages for an agent.
        
        Args:
            agent_name: Name of agent
            max_messages: Maximum number of messages to retrieve
            block: Whether to block until messages arrive
            timeout: Timeout for blocking (seconds)
            
        Returns:
            List[Message]: List of messages
        """
        messages = []
        
        if block and not self._queues[agent_name]:
            # Wait for messages
            start_time = datetime.now()
            while not self._queues[agent_name]:
                if timeout and (datetime.now() - start_time).total_seconds() > timeout:
                    break
                asyncio.sleep(0.1)
        
        with self._lock:
            queue = self._queues[agent_name]
            count = min(len(queue), max_messages) if max_messages else len(queue)
            
            for _ in range(count):
                if queue:
                    messages.append(queue.popleft())
        
        if messages:
            logger.debug(f"Retrieved {len(messages)} message(s) for {agent_name}")
        
        return messages
    
    def peek_messages(self, agent_name: str, max_messages: Optional[int] = None) -> List[Message]:
        """
        Peek at messages without removing them from queue.
        
        Args:
            agent_name: Name of agent
            max_messages: Maximum number to peek
            
        Returns:
            List[Message]: List of messages
        """
        with self._lock:
            queue = self._queues[agent_name]
            count = min(len(queue), max_messages) if max_messages else len(queue)
            return list(queue)[:count]
    
    def get_message_count(self, agent_name: str) -> int:
        """
        Get number of pending messages for an agent.
        
        Args:
            agent_name: Name of agent
            
        Returns:
            int: Number of pending messages
        """
        with self._lock:
            return len(self._queues[agent_name])
    
    def clear_queue(self, agent_name: str) -> None:
        """
        Clear all messages for an agent.
        
        Args:
            agent_name: Name of agent
        """
        with self._lock:
            self._queues[agent_name].clear()
            logger.info(f"Cleared message queue for {agent_name}")
    
    def get_history(
        self,
        agent_name: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Message]:
        """
        Get message history with optional filtering.
        
        Args:
            agent_name: Filter by sender or receiver
            message_type: Filter by message type
            since: Only messages after this time
            limit: Maximum messages to return
            
        Returns:
            List[Message]: Filtered message history
        """
        with self._lock:
            messages = list(self._message_history)
        
        # Apply filters
        if agent_name:
            messages = [
                m for m in messages
                if m.sender == agent_name or m.receiver == agent_name
            ]
        
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        
        if since:
            messages = [m for m in messages if m.timestamp >= since]
        
        # Sort by timestamp (newest first) and limit
        messages.sort(key=lambda m: m.timestamp, reverse=True)
        return messages[:limit]
    
    def get_conversation(self, correlation_id: str) -> List[Message]:
        """
        Get all messages in a conversation thread.
        
        Args:
            correlation_id: Correlation ID linking messages
            
        Returns:
            List[Message]: Messages in conversation
        """
        with self._lock:
            messages = [
                m for m in self._message_history
                if m.id == correlation_id or m.correlation_id == correlation_id
            ]
        
        messages.sort(key=lambda m: m.timestamp)
        return messages
    
    def cleanup_old_messages(self) -> int:
        """
        Remove old messages from history.
        
        Returns:
            int: Number of messages removed
        """
        cutoff = datetime.now() - timedelta(seconds=self.message_retention_seconds)
        
        with self._lock:
            original_count = len(self._message_history)
            self._message_history = deque(
                [m for m in self._message_history if m.timestamp >= cutoff],
                maxlen=self._message_history.maxlen
            )
            removed = original_count - len(self._message_history)
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} old messages")
        
        return removed
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get message bus statistics.
        
        Returns:
            dict: Statistics including queue sizes, message counts, etc.
        """
        with self._lock:
            return {
                "total_agents": len(self._queues),
                "total_messages_in_queues": sum(len(q) for q in self._queues.values()),
                "history_size": len(self._message_history),
                "queue_sizes": {name: len(queue) for name, queue in self._queues.items()},
                "subscribers": {
                    msg_type.value: list(agents)
                    for msg_type, agents in self._subscribers.items()
                }
            }
    
    def reset(self) -> None:
        """Reset the message bus (useful for testing)."""
        with self._lock:
            self._queues.clear()
            self._subscribers.clear()
            self._message_history.clear()
            self._handlers.clear()
            logger.info("MessageBus reset")
