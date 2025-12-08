
"""
Real-Time Feedback Pipeline for Agent Actions

This module provides a Kafka-based feedback pipeline that captures structured
outcome events from agent actions, enabling real-time monitoring, analytics,
and adaptive learning.
"""

from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from enum import Enum
import json
import asyncio
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaProducer = None
    KafkaError = Exception

from utils.logging import get_logger

logger = get_logger(__name__)


class OutcomeStatus(str, Enum):
    """Outcome status enum."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PENDING = "pending"


class EventSeverity(str, Enum):
    """Event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class OutcomeEvent:
    """
    Structured outcome event from an agent action.
    
    This event captures the complete context of an agent action execution,
    including performance metrics, errors, and contextual information.
    """
    # Identification
    event_id: str
    run_id: str
    agent_name: str
    agent_type: str
    action_type: str
    
    # Timing
    timestamp: str
    start_time: str
    end_time: str
    duration_ms: float
    
    # Outcome
    status: OutcomeStatus
    severity: EventSeverity
    
    # Performance
    latency_ms: float
    llm_latency_ms: Optional[float] = None
    tokens_used: Optional[int] = None
    
    # Results
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Context
    input_data: Optional[Dict[str, Any]] = None
    context_snapshot: Optional[Dict[str, Any]] = None
    
    # Metrics
    retry_count: int = 0
    memory_used_mb: Optional[float] = None
    cpu_time_ms: Optional[float] = None
    
    # Business metrics
    cost_estimate: Optional[float] = None
    quality_score: Optional[float] = None
    confidence_score: Optional[float] = None
    
    # Relationships
    parent_event_id: Optional[str] = None
    correlation_id: Optional[str] = None
    workflow_id: Optional[str] = None
    
    # Tags and metadata
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert enums to strings
        data['status'] = self.status.value
        data['severity'] = self.severity.value
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class KafkaPublisher:
    """
    Kafka publisher for outcome events.
    
    Handles asynchronous publishing of events to Kafka with error handling,
    retry logic, and monitoring.
    """
    
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str = "agent-outcomes",
        batch_size: int = 100,
        linger_ms: int = 100,
        compression_type: str = "gzip",
        max_retries: int = 3,
        enable_monitoring: bool = True
    ):
        """
        Initialize Kafka publisher.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Topic name for outcome events
            batch_size: Number of messages to batch
            linger_ms: Time to wait before sending batch
            compression_type: Compression algorithm
            max_retries: Maximum retry attempts
            enable_monitoring: Enable internal monitoring
        """
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka library not available. Events will be logged only.")
            self.producer = None
            self.enabled = False
            return
        
        self.topic = topic
        self.enabled = True
        self.max_retries = max_retries
        self.enable_monitoring = enable_monitoring
        
        # Monitoring metrics
        self._events_sent = 0
        self._events_failed = 0
        self._total_latency_ms = 0.0
        
        # Thread pool for async operations
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                batch_size=batch_size,
                linger_ms=linger_ms,
                compression_type=compression_type,
                retries=max_retries,
                acks='all'
            )
            logger.info(f"Kafka publisher initialized (topic={topic})")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None
            self.enabled = False
    
    async def publish(self, event: OutcomeEvent) -> bool:
        """
        Publish an outcome event to Kafka.
        
        Args:
            event: Outcome event to publish
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled or not self.producer:
            logger.debug(f"Kafka disabled, logging event: {event.event_id}")
            return False
        
        try:
            start = datetime.now()
            
            # Convert event to dict
            event_data = event.to_dict()
            
            # Send to Kafka
            future = self.producer.send(self.topic, value=event_data, key=event.event_id.encode('utf-8'))
            
            # Wait for confirmation (with timeout)
            record_metadata = future.get(timeout=10)
            
            # Update metrics
            if self.enable_monitoring:
                latency = (datetime.now() - start).total_seconds() * 1000
                self._events_sent += 1
                self._total_latency_ms += latency
                
            logger.debug(
                f"Event published: {event.event_id} "
                f"(partition={record_metadata.partition}, offset={record_metadata.offset})"
            )
            
            return True
            
        except KafkaError as e:
            self._events_failed += 1
            logger.error(f"Kafka error publishing event {event.event_id}: {e}")
            return False
        except Exception as e:
            self._events_failed += 1
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            return False
    
    async def publish_batch(self, events: List[OutcomeEvent]) -> Dict[str, int]:
        """
        Publish multiple events in batch.
        
        Args:
            events: List of outcome events
            
        Returns:
            dict: Statistics (sent, failed)
        """
        results = await asyncio.gather(
            *[self.publish(event) for event in events],
            return_exceptions=True
        )
        
        sent = sum(1 for r in results if r is True)
        failed = len(results) - sent
        
        return {"sent": sent, "failed": failed}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get publisher metrics."""
        if not self.enable_monitoring:
            return {}
        
        avg_latency = (
            self._total_latency_ms / self._events_sent
            if self._events_sent > 0 else 0.0
        )
        
        return {
            "events_sent": self._events_sent,
            "events_failed": self._events_failed,
            "average_latency_ms": avg_latency,
            "success_rate": (
                self._events_sent / (self._events_sent + self._events_failed)
                if (self._events_sent + self._events_failed) > 0 else 0.0
            )
        }
    
    def close(self):
        """Close the Kafka producer."""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka publisher closed")
        
        if self._executor:
            self._executor.shutdown(wait=True)


class FeedbackPipeline:
    """
    Centralized feedback pipeline for collecting and publishing outcome events.
    
    This pipeline serves as the main interface for capturing agent outcomes
    and publishing them to downstream systems (Kafka, logging, analytics).
    """
    
    def __init__(
        self,
        kafka_servers: Optional[str] = None,
        kafka_topic: str = "agent-outcomes",
        enable_kafka: bool = True,
        enable_logging: bool = True
    ):
        """
        Initialize feedback pipeline.
        
        Args:
            kafka_servers: Kafka bootstrap servers
            kafka_topic: Kafka topic name
            enable_kafka: Enable Kafka publishing
            enable_logging: Enable log-based fallback
        """
        self.enable_kafka = enable_kafka and kafka_servers is not None
        self.enable_logging = enable_logging
        
        # Initialize Kafka publisher
        self.kafka_publisher = None
        if self.enable_kafka and KAFKA_AVAILABLE:
            self.kafka_publisher = KafkaPublisher(
                bootstrap_servers=kafka_servers,
                topic=kafka_topic
            )
        
        # Local event buffer (for fallback and testing)
        self._event_buffer: List[OutcomeEvent] = []
        self._buffer_max_size = 1000
        
        logger.info(
            f"Feedback pipeline initialized "
            f"(kafka={self.enable_kafka}, logging={self.enable_logging})"
        )
    
    async def record_outcome(self, event: OutcomeEvent) -> None:
        """
        Record an outcome event.
        
        Args:
            event: Outcome event to record
        """
        # Add to buffer
        if len(self._event_buffer) >= self._buffer_max_size:
            self._event_buffer.pop(0)  # Remove oldest
        self._event_buffer.append(event)
        
        # Publish to Kafka
        if self.kafka_publisher:
            await self.kafka_publisher.publish(event)
        
        # Log the event
        if self.enable_logging:
            self._log_event(event)
    
    def _log_event(self, event: OutcomeEvent) -> None:
        """Log an outcome event."""
        log_level = {
            EventSeverity.INFO: logger.info,
            EventSeverity.WARNING: logger.warning,
            EventSeverity.ERROR: logger.error,
            EventSeverity.CRITICAL: logger.critical
        }.get(event.severity, logger.info)
        
        log_level(
            f"Outcome: agent={event.agent_name} action={event.action_type} "
            f"status={event.status.value} duration={event.duration_ms:.2f}ms "
            f"latency={event.latency_ms:.2f}ms"
        )
    
    def get_recent_events(
        self,
        count: int = 10,
        agent_name: Optional[str] = None,
        status: Optional[OutcomeStatus] = None
    ) -> List[OutcomeEvent]:
        """
        Get recent events from buffer.
        
        Args:
            count: Number of events to retrieve
            agent_name: Filter by agent name
            status: Filter by status
            
        Returns:
            List[OutcomeEvent]: Recent events
        """
        events = self._event_buffer[-count:]
        
        # Apply filters
        if agent_name:
            events = [e for e in events if e.agent_name == agent_name]
        if status:
            events = [e for e in events if e.status == status]
        
        return events
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics."""
        metrics = {
            "buffer_size": len(self._event_buffer),
            "buffer_max_size": self._buffer_max_size
        }
        
        if self.kafka_publisher:
            metrics["kafka"] = self.kafka_publisher.get_metrics()
        
        return metrics
    
    def close(self):
        """Close the feedback pipeline."""
        if self.kafka_publisher:
            self.kafka_publisher.close()
        logger.info("Feedback pipeline closed")


# Singleton instance
_pipeline_instance: Optional[FeedbackPipeline] = None


def get_feedback_pipeline(
    kafka_servers: Optional[str] = None,
    kafka_topic: str = "agent-outcomes",
    force_new: bool = False
) -> FeedbackPipeline:
    """
    Get or create the global feedback pipeline instance.
    
    Args:
        kafka_servers: Kafka bootstrap servers
        kafka_topic: Kafka topic name
        force_new: Force creation of new instance
        
    Returns:
        FeedbackPipeline: Pipeline instance
    """
    global _pipeline_instance
    
    if force_new or _pipeline_instance is None:
        _pipeline_instance = FeedbackPipeline(
            kafka_servers=kafka_servers,
            kafka_topic=kafka_topic
        )
    
    return _pipeline_instance
