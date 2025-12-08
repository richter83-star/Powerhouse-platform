
"""
Webhook System for Event-Driven Integrations
Supports incoming and outgoing webhooks with signature verification
"""

import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

import httpx
from pydantic import BaseModel, HttpUrl


class WebhookEvent(str, Enum):
    """Supported webhook events"""
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    METRIC_THRESHOLD = "metric.threshold"
    ALERT_TRIGGERED = "alert.triggered"
    CUSTOM = "custom"


class WebhookDeliveryStatus(str, Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookSubscription(BaseModel):
    """Webhook subscription model"""
    id: str
    url: HttpUrl
    events: List[WebhookEvent]
    secret: str
    active: bool = True
    max_retries: int = 3
    timeout: int = 30
    headers: Dict[str, str] = {}
    created_at: datetime = datetime.utcnow()


class WebhookPayload(BaseModel):
    """Webhook payload structure"""
    id: str
    event: WebhookEvent
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None


class WebhookDelivery(BaseModel):
    """Webhook delivery record"""
    id: str
    subscription_id: str
    payload: WebhookPayload
    status: WebhookDeliveryStatus
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None


class WebhookSystem:
    """Manages webhook subscriptions and deliveries"""
    
    def __init__(self):
        self.subscriptions: Dict[str, WebhookSubscription] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.retry_queue: asyncio.Queue = asyncio.Queue()
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
    def create_subscription(
        self,
        url: str,
        events: List[WebhookEvent],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
        timeout: int = 30
    ) -> WebhookSubscription:
        """Create a new webhook subscription"""
        subscription = WebhookSubscription(
            id=str(uuid4()),
            url=url,
            events=events,
            secret=secret or self._generate_secret(),
            headers=headers or {},
            max_retries=max_retries,
            timeout=timeout
        )
        self.subscriptions[subscription.id] = subscription
        return subscription
    
    def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get subscription by ID"""
        return self.subscriptions.get(subscription_id)
    
    def list_subscriptions(self, active_only: bool = False) -> List[WebhookSubscription]:
        """List all subscriptions"""
        subs = list(self.subscriptions.values())
        if active_only:
            subs = [s for s in subs if s.active]
        return subs
    
    def update_subscription(
        self,
        subscription_id: str,
        **kwargs
    ) -> Optional[WebhookSubscription]:
        """Update subscription"""
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            return None
        
        for key, value in kwargs.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)
        
        return subscription
    
    def delete_subscription(self, subscription_id: str) -> bool:
        """Delete subscription"""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            return True
        return False
    
    async def trigger_event(
        self,
        event: WebhookEvent,
        data: Dict[str, Any]
    ) -> List[WebhookDelivery]:
        """Trigger a webhook event"""
        payload = WebhookPayload(
            id=str(uuid4()),
            event=event,
            timestamp=datetime.utcnow(),
            data=data
        )
        
        # Find matching subscriptions
        matching_subs = [
            sub for sub in self.subscriptions.values()
            if sub.active and event in sub.events
        ]
        
        # Trigger internal handlers
        await self._trigger_internal_handlers(event, data)
        
        # Send webhooks
        deliveries = []
        for sub in matching_subs:
            delivery = await self._send_webhook(sub, payload)
            deliveries.append(delivery)
        
        return deliveries
    
    async def _send_webhook(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload
    ) -> WebhookDelivery:
        """Send webhook to a subscription"""
        delivery = WebhookDelivery(
            id=str(uuid4()),
            subscription_id=subscription.id,
            payload=payload,
            status=WebhookDeliveryStatus.PENDING
        )
        self.deliveries[delivery.id] = delivery
        
        # Add signature
        payload.signature = self._generate_signature(
            payload.model_dump_json(),
            subscription.secret
        )
        
        # Attempt delivery
        await self._attempt_delivery(subscription, delivery)
        
        return delivery
    
    async def _attempt_delivery(
        self,
        subscription: WebhookSubscription,
        delivery: WebhookDelivery
    ):
        """Attempt to deliver webhook"""
        delivery.attempts += 1
        delivery.last_attempt = datetime.utcnow()
        delivery.status = WebhookDeliveryStatus.PENDING
        
        try:
            headers = {
                **subscription.headers,
                "Content-Type": "application/json",
                "X-Webhook-Signature": delivery.payload.signature or "",
                "X-Webhook-Event": delivery.payload.event,
                "X-Webhook-Id": delivery.payload.id
            }
            
            response = await self.http_client.post(
                str(subscription.url),
                json=delivery.payload.model_dump(mode='json'),
                headers=headers,
                timeout=subscription.timeout
            )
            
            delivery.response_code = response.status_code
            delivery.response_body = response.text[:1000]  # Limit response body
            
            if 200 <= response.status_code < 300:
                delivery.status = WebhookDeliveryStatus.DELIVERED
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            delivery.error = str(e)[:500]
            
            # Retry logic
            if delivery.attempts < subscription.max_retries:
                delivery.status = WebhookDeliveryStatus.RETRYING
                await self.retry_queue.put((subscription, delivery))
            else:
                delivery.status = WebhookDeliveryStatus.FAILED
    
    async def process_retry_queue(self):
        """Process webhook retry queue"""
        while True:
            try:
                subscription, delivery = await asyncio.wait_for(
                    self.retry_queue.get(),
                    timeout=1.0
                )
                
                # Exponential backoff
                delay = min(2 ** delivery.attempts, 300)  # Max 5 minutes
                await asyncio.sleep(delay)
                
                await self._attempt_delivery(subscription, delivery)
                
            except asyncio.TimeoutError:
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error processing retry queue: {e}")
    
    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        expected = self._generate_signature(payload, secret)
        return hmac.compare_digest(signature, expected)
    
    def register_handler(self, event: WebhookEvent, handler: Callable):
        """Register internal event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
    
    async def _trigger_internal_handlers(self, event: WebhookEvent, data: Dict[str, Any]):
        """Trigger internal event handlers"""
        handlers = self.event_handlers.get(event, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                print(f"Error in handler for {event}: {e}")
    
    def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get delivery by ID"""
        return self.deliveries.get(delivery_id)
    
    def list_deliveries(
        self,
        subscription_id: Optional[str] = None,
        status: Optional[WebhookDeliveryStatus] = None
    ) -> List[WebhookDelivery]:
        """List deliveries with filters"""
        deliveries = list(self.deliveries.values())
        
        if subscription_id:
            deliveries = [d for d in deliveries if d.subscription_id == subscription_id]
        
        if status:
            deliveries = [d for d in deliveries if d.status == status]
        
        return deliveries
    
    @staticmethod
    def _generate_secret() -> str:
        """Generate webhook secret"""
        return hashlib.sha256(str(uuid4()).encode()).hexdigest()
    
    @staticmethod
    def _generate_signature(payload: str, secret: str) -> str:
        """Generate HMAC signature"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()


# Global instance
webhook_system = WebhookSystem()
