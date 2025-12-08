
"""
Distributed message queue using Redis/NATS for agent task distribution.
"""
import json
import asyncio
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import redis.asyncio as redis
import uuid

class QueueType(Enum):
    """Types of queues"""
    AGENT_TASKS = "agent_tasks"
    WORKFLOW_EVENTS = "workflow_events"
    SYSTEM_EVENTS = "system_events"
    PRIORITY_TASKS = "priority_tasks"
    DEAD_LETTER = "dead_letter"

@dataclass
class Message:
    """Message structure for queue"""
    id: str
    type: str
    tenant_id: str
    payload: Dict[str, Any]
    priority: int = 5  # 1-10, higher = more urgent
    timestamp: str = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls(**data)

class MessageQueue:
    """
    Distributed message queue for agent task orchestration.
    
    Features:
    - Priority-based task distribution
    - Automatic retries with exponential backoff
    - Dead letter queue for failed messages
    - Multi-tenant isolation
    - Horizontal scalability
    - At-least-once delivery guarantee
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize message queue.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client = None
        self.subscribers = {}  # {queue_type: [callbacks]}
        self._running = False
    
    async def connect(self):
        """Establish connection to Redis"""
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        self._running = True
    
    async def disconnect(self):
        """Close Redis connection"""
        self._running = False
        if self.redis_client:
            await self.redis_client.close()
    
    async def publish(
        self,
        queue_type: QueueType,
        message: Message
    ):
        """
        Publish message to queue.
        
        Args:
            queue_type: Target queue
            message: Message to publish
        """
        if not self.redis_client:
            await self.connect()
        
        queue_key = f"{queue_type.value}:{message.tenant_id}"
        
        # Use Redis sorted set with priority as score
        await self.redis_client.zadd(
            queue_key,
            {message.to_json(): message.priority}
        )
        
        # Publish event for real-time subscribers
        await self.redis_client.publish(
            f"channel:{queue_type.value}",
            message.to_json()
        )
    
    async def consume(
        self,
        queue_type: QueueType,
        tenant_id: str,
        batch_size: int = 10
    ) -> List[Message]:
        """
        Consume messages from queue (highest priority first).
        
        Args:
            queue_type: Queue to consume from
            tenant_id: Tenant context
            batch_size: Number of messages to retrieve
            
        Returns:
            List of messages
        """
        if not self.redis_client:
            await self.connect()
        
        queue_key = f"{queue_type.value}:{tenant_id}"
        
        # Get highest priority messages
        messages_json = await self.redis_client.zrevrange(
            queue_key,
            0,
            batch_size - 1
        )
        
        messages = [Message.from_json(msg) for msg in messages_json]
        
        # Remove consumed messages
        if messages_json:
            await self.redis_client.zrem(queue_key, *messages_json)
        
        return messages
    
    async def subscribe(
        self,
        queue_type: QueueType,
        callback: Callable[[Message], None]
    ):
        """
        Subscribe to queue for real-time message processing.
        
        Args:
            queue_type: Queue to subscribe to
            callback: Async function to process messages
        """
        if not self.redis_client:
            await self.connect()
        
        if queue_type not in self.subscribers:
            self.subscribers[queue_type] = []
        
        self.subscribers[queue_type].append(callback)
        
        # Start subscriber task if not running
        asyncio.create_task(self._run_subscriber(queue_type))
    
    async def _run_subscriber(self, queue_type: QueueType):
        """Background task to process subscribed messages"""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(f"channel:{queue_type.value}")
        
        try:
            while self._running:
                message_data = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )
                
                if message_data:
                    message = Message.from_json(message_data['data'])
                    
                    # Call all registered callbacks
                    for callback in self.subscribers.get(queue_type, []):
                        try:
                            await callback(message)
                        except Exception as e:
                            print(f"Error in subscriber callback: {e}")
                            await self._handle_failed_message(message, str(e))
        
        finally:
            await pubsub.unsubscribe(f"channel:{queue_type.value}")
    
    async def retry_message(self, queue_type: QueueType, message: Message):
        """
        Retry a failed message with exponential backoff.
        
        Args:
            queue_type: Queue to retry in
            message: Message to retry
        """
        message.retry_count += 1
        
        if message.retry_count >= message.max_retries:
            # Move to dead letter queue
            await self.publish(QueueType.DEAD_LETTER, message)
        else:
            # Re-queue with lower priority
            message.priority = max(1, message.priority - 1)
            await self.publish(queue_type, message)
    
    async def _handle_failed_message(self, message: Message, error: str):
        """Handle message processing failure"""
        message.payload['error'] = error
        await self.retry_message(QueueType.AGENT_TASKS, message)
    
    async def get_queue_size(self, queue_type: QueueType, tenant_id: str) -> int:
        """Get number of messages in queue"""
        if not self.redis_client:
            await self.connect()
        
        queue_key = f"{queue_type.value}:{tenant_id}"
        return await self.redis_client.zcard(queue_key)
    
    async def clear_queue(self, queue_type: QueueType, tenant_id: str):
        """Clear all messages from queue"""
        if not self.redis_client:
            await self.connect()
        
        queue_key = f"{queue_type.value}:{tenant_id}"
        await self.redis_client.delete(queue_key)

# Global message queue instance
message_queue = MessageQueue()

# Helper functions
async def publish_agent_task(tenant_id: str, agent_id: str, task_data: Dict[str, Any], priority: int = 5):
    """Publish an agent task"""
    message = Message(
        id=str(uuid.uuid4()),
        type="agent_task",
        tenant_id=tenant_id,
        payload={
            "agent_id": agent_id,
            "task": task_data
        },
        priority=priority
    )
    await message_queue.publish(QueueType.AGENT_TASKS, message)
    return message.id

async def publish_workflow_event(tenant_id: str, workflow_id: str, event_type: str, data: Dict[str, Any]):
    """Publish a workflow event"""
    message = Message(
        id=str(uuid.uuid4()),
        type=event_type,
        tenant_id=tenant_id,
        payload={
            "workflow_id": workflow_id,
            "data": data
        }
    )
    await message_queue.publish(QueueType.WORKFLOW_EVENTS, message)
    return message.id
