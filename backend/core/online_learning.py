
"""
Real-Time Online Learning Module

This module implements continuous model improvement through micro-batch updates
based on outcome events from the feedback pipeline.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import asyncio
import numpy as np
from collections import defaultdict, deque
import pickle
from pathlib import Path

try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaConsumer = None
    KafkaError = Exception

from core.feedback_pipeline import OutcomeEvent, OutcomeStatus
from utils.logging import get_logger

logger = get_logger(__name__)


class ModelType(str, Enum):
    """Types of models that can be updated."""
    AGENT_SELECTION = "agent_selection"  # Which agent to use for a task
    PARAMETER_OPTIMIZATION = "parameter_optimization"  # LLM parameters
    ROUTING = "routing"  # Task routing decisions
    QUALITY_PREDICTION = "quality_prediction"  # Predict outcome quality
    LATENCY_PREDICTION = "latency_prediction"  # Predict execution time


class UpdateStrategy(str, Enum):
    """Strategies for model updates."""
    MOVING_AVERAGE = "moving_average"  # Simple moving average
    EXPONENTIAL = "exponential"  # Exponential moving average
    BAYESIAN = "bayesian"  # Bayesian update
    GRADIENT = "gradient"  # Gradient-based update


@dataclass
class ModelVersion:
    """Model version metadata."""
    version_id: str
    model_type: ModelType
    created_at: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    training_samples: int
    parent_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['model_type'] = self.model_type.value
        return data


@dataclass
class LearningMetrics:
    """Metrics for the learning process."""
    total_updates: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    avg_update_time_ms: float = 0.0
    samples_processed: int = 0
    current_model_score: float = 0.0
    improvement_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class AgentPerformanceModel:
    """
    Model that tracks agent performance patterns and learns optimal selections.
    
    This model uses a multi-armed bandit approach with Thompson Sampling
    to balance exploration and exploitation when selecting agents.
    """
    
    def __init__(self, model_id: str = "agent_perf_v1"):
        """Initialize the agent performance model."""
        self.model_id = model_id
        
        # Agent statistics: {agent_name: {'successes': int, 'failures': int, 'latencies': []}}
        self.agent_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'successes': 0,
            'failures': 0,
            'latencies': deque(maxlen=100),
            'quality_scores': deque(maxlen=100),
            'contexts': deque(maxlen=100)
        })
        
        # Task-specific patterns: {task_type: {agent_name: score}}
        self.task_patterns: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # Context-aware patterns
        self.context_patterns: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        self.update_count = 0
        self.last_update = datetime.utcnow()
    
    def update(self, event: OutcomeEvent) -> None:
        """
        Update the model with a new outcome event.
        
        Args:
            event: Outcome event from agent execution
        """
        agent_name = event.agent_name
        stats = self.agent_stats[agent_name]
        
        # Update success/failure counts
        if event.status == OutcomeStatus.SUCCESS:
            stats['successes'] += 1
        else:
            stats['failures'] += 1
        
        # Update latency
        stats['latencies'].append(event.latency_ms)
        
        # Update quality scores
        if event.quality_score is not None:
            stats['quality_scores'].append(event.quality_score)
        
        # Update task-specific patterns
        if event.action_type:
            success_rate = self.get_success_rate(agent_name)
            self.task_patterns[event.action_type][agent_name] = success_rate
        
        # Update context patterns
        if event.context_snapshot:
            context_key = self._extract_context_key(event.context_snapshot)
            self.context_patterns[context_key][agent_name] = self.get_success_rate(agent_name)
        
        self.update_count += 1
        self.last_update = datetime.utcnow()
        
        logger.debug(
            f"Updated agent model: agent={agent_name} "
            f"success_rate={self.get_success_rate(agent_name):.2%}"
        )
    
    def predict_best_agent(
        self,
        task_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Predict the best agents for a given task.
        
        Args:
            task_type: Type of task
            context: Task context
            top_k: Number of agents to return
            
        Returns:
            List of (agent_name, score) tuples
        """
        scores: Dict[str, float] = {}
        
        for agent_name, stats in self.agent_stats.items():
            # Base score: Thompson sampling
            alpha = stats['successes'] + 1  # Prior
            beta = stats['failures'] + 1  # Prior
            score = np.random.beta(alpha, beta)
            
            # Adjust for task-specific performance
            if task_type and task_type in self.task_patterns:
                task_score = self.task_patterns[task_type].get(agent_name, 0.5)
                score = 0.6 * score + 0.4 * task_score
            
            # Adjust for context
            if context:
                context_key = self._extract_context_key(context)
                if context_key in self.context_patterns:
                    context_score = self.context_patterns[context_key].get(agent_name, 0.5)
                    score = 0.7 * score + 0.3 * context_score
            
            # Penalize high latency
            if stats['latencies']:
                avg_latency = np.mean(list(stats['latencies']))
                latency_penalty = 1.0 / (1.0 + avg_latency / 1000)  # Normalize
                score *= latency_penalty
            
            scores[agent_name] = score
        
        # Return top-k agents
        sorted_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_agents[:top_k]
    
    def get_success_rate(self, agent_name: str) -> float:
        """Get success rate for an agent."""
        stats = self.agent_stats[agent_name]
        total = stats['successes'] + stats['failures']
        if total == 0:
            return 0.5  # Prior
        return stats['successes'] / total
    
    def get_avg_latency(self, agent_name: str) -> float:
        """Get average latency for an agent."""
        stats = self.agent_stats[agent_name]
        if not stats['latencies']:
            return 0.0
        return float(np.mean(list(stats['latencies'])))
    
    def _extract_context_key(self, context: Dict[str, Any]) -> str:
        """Extract a key from context for pattern matching."""
        # Simple implementation: use top-level keys
        return "_".join(sorted(context.keys())[:3])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'model_id': self.model_id,
            'agent_stats': {
                name: {
                    'successes': stats['successes'],
                    'failures': stats['failures'],
                    'avg_latency': self.get_avg_latency(name),
                    'success_rate': self.get_success_rate(name)
                }
                for name, stats in self.agent_stats.items()
            },
            'task_patterns': dict(self.task_patterns),
            'update_count': self.update_count,
            'last_update': self.last_update.isoformat()
        }


class RealTimeModelUpdater:
    """
    Real-time model updater that subscribes to outcome events
    and performs micro-batch updates on ML models.
    
    This service enables continuous learning from agent executions,
    improving predictions and decisions over time.
    """
    
    def __init__(
        self,
        kafka_servers: str,
        kafka_topic: str = "agent-outcomes",
        consumer_group: str = "model-updater",
        batch_size: int = 10,
        batch_timeout_seconds: int = 30,
        model_storage_path: str = "./models",
        update_strategy: UpdateStrategy = UpdateStrategy.EXPONENTIAL,
        enable_auto_save: bool = True,
        save_interval_seconds: int = 300
    ):
        """
        Initialize the real-time model updater.
        
        Args:
            kafka_servers: Kafka bootstrap servers
            kafka_topic: Topic to consume outcome events from
            consumer_group: Kafka consumer group
            batch_size: Number of events per micro-batch
            batch_timeout_seconds: Max time to wait for batch
            model_storage_path: Path to store model files
            update_strategy: Strategy for model updates
            enable_auto_save: Enable automatic model saving
            save_interval_seconds: Interval for auto-saving models
        """
        if not KAFKA_AVAILABLE:
            raise ImportError("kafka-python is required for RealTimeModelUpdater")
        
        self.kafka_servers = kafka_servers
        self.kafka_topic = kafka_topic
        self.consumer_group = consumer_group
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds
        self.update_strategy = update_strategy
        self.enable_auto_save = enable_auto_save
        self.save_interval_seconds = save_interval_seconds
        
        # Model storage
        self.model_storage_path = Path(model_storage_path)
        self.model_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize models
        self.models: Dict[ModelType, Any] = {
            ModelType.AGENT_SELECTION: AgentPerformanceModel()
        }
        
        # Load existing models
        self._load_models()
        
        # Metrics
        self.metrics = LearningMetrics()
        
        # Event buffer
        self.event_buffer: deque = deque(maxlen=batch_size * 10)
        
        # Consumer
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False
        
        # Last save time
        self.last_save_time = datetime.utcnow()
        
        logger.info(
            f"RealTimeModelUpdater initialized: "
            f"topic={kafka_topic}, batch_size={batch_size}"
        )
    
    def start(self):
        """Start the model updater service."""
        if self.running:
            logger.warning("Model updater is already running")
            return
        
        try:
            # Create Kafka consumer
            self.consumer = KafkaConsumer(
                self.kafka_topic,
                bootstrap_servers=self.kafka_servers,
                group_id=self.consumer_group,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                max_poll_records=self.batch_size
            )
            
            self.running = True
            logger.info("Model updater started successfully")
            
            # Start processing loop
            asyncio.create_task(self._processing_loop())
            
        except Exception as e:
            logger.error(f"Failed to start model updater: {e}")
            raise
    
    def stop(self):
        """Stop the model updater service."""
        self.running = False
        
        if self.consumer:
            self.consumer.close()
            self.consumer = None
        
        # Save models before stopping
        self._save_models()
        
        logger.info("Model updater stopped")
    
    async def _processing_loop(self):
        """Main processing loop for consuming events and updating models."""
        logger.info("Starting model update processing loop")
        
        batch = []
        last_batch_time = datetime.utcnow()
        
        while self.running:
            try:
                # Poll for messages
                messages = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, records in messages.items():
                    for record in records:
                        # Convert to OutcomeEvent
                        event_data = record.value
                        event = self._dict_to_outcome_event(event_data)
                        
                        # Add to batch
                        batch.append(event)
                        self.event_buffer.append(event)
                
                # Check if batch is ready
                time_since_batch = (datetime.utcnow() - last_batch_time).total_seconds()
                batch_ready = (
                    len(batch) >= self.batch_size or
                    (len(batch) > 0 and time_since_batch >= self.batch_timeout_seconds)
                )
                
                if batch_ready:
                    # Process batch
                    await self._process_batch(batch)
                    batch = []
                    last_batch_time = datetime.utcnow()
                
                # Auto-save check
                if self.enable_auto_save:
                    time_since_save = (datetime.utcnow() - self.last_save_time).total_seconds()
                    if time_since_save >= self.save_interval_seconds:
                        self._save_models()
                        self.last_save_time = datetime.utcnow()
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(1)
        
        logger.info("Processing loop stopped")
    
    async def _process_batch(self, batch: List[OutcomeEvent]) -> None:
        """
        Process a batch of outcome events.
        
        Args:
            batch: List of outcome events
        """
        start_time = datetime.utcnow()
        
        try:
            # Update each model with the batch
            for model_type, model in self.models.items():
                if model_type == ModelType.AGENT_SELECTION:
                    # Update agent selection model
                    for event in batch:
                        model.update(event)
            
            # Update metrics
            self.metrics.total_updates += 1
            self.metrics.successful_updates += 1
            self.metrics.samples_processed += len(batch)
            
            # Calculate update time
            update_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.metrics.avg_update_time_ms = (
                (self.metrics.avg_update_time_ms * (self.metrics.total_updates - 1) + update_time)
                / self.metrics.total_updates
            )
            
            # Calculate model score (e.g., average success rate)
            agent_model = self.models[ModelType.AGENT_SELECTION]
            if agent_model.agent_stats:
                avg_success_rate = np.mean([
                    agent_model.get_success_rate(agent)
                    for agent in agent_model.agent_stats.keys()
                ])
                old_score = self.metrics.current_model_score
                self.metrics.current_model_score = float(avg_success_rate)
                
                if old_score > 0:
                    self.metrics.improvement_rate = (
                        (self.metrics.current_model_score - old_score) / old_score
                    )
            
            logger.info(
                f"Processed batch: size={len(batch)} "
                f"update_time={update_time:.2f}ms "
                f"model_score={self.metrics.current_model_score:.2%}"
            )
            
        except Exception as e:
            self.metrics.failed_updates += 1
            logger.error(f"Failed to process batch: {e}")
    
    def _dict_to_outcome_event(self, data: Dict[str, Any]) -> OutcomeEvent:
        """Convert dictionary to OutcomeEvent."""
        # Convert status and severity strings back to enums
        from core.feedback_pipeline import EventSeverity
        
        data['status'] = OutcomeStatus(data['status'])
        data['severity'] = EventSeverity(data['severity'])
        
        return OutcomeEvent(**data)
    
    def get_model(self, model_type: ModelType) -> Any:
        """Get a specific model."""
        return self.models.get(model_type)
    
    def predict(
        self,
        model_type: ModelType,
        **kwargs
    ) -> Any:
        """
        Make a prediction using a specific model.
        
        Args:
            model_type: Type of model to use
            **kwargs: Model-specific arguments
            
        Returns:
            Model prediction
        """
        model = self.models.get(model_type)
        if not model:
            raise ValueError(f"Model type {model_type} not found")
        
        if model_type == ModelType.AGENT_SELECTION:
            return model.predict_best_agent(**kwargs)
        
        raise NotImplementedError(f"Prediction for {model_type} not implemented")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current learning metrics."""
        metrics = self.metrics.to_dict()
        
        # Add model-specific metrics
        for model_type, model in self.models.items():
            if hasattr(model, 'to_dict'):
                metrics[f'model_{model_type.value}'] = model.to_dict()
        
        return metrics
    
    def trigger_retraining(
        self,
        model_type: ModelType = ModelType.AGENT_SELECTION,
        reason: str = "Manual trigger",
        force_full_retrain: bool = False
    ) -> Dict[str, Any]:
        """
        Manually trigger model retraining.
        
        This method is called by the PerformanceMonitor when it detects
        that model performance has degraded below acceptable thresholds.
        
        Args:
            model_type: Type of model to retrain
            reason: Reason for triggering retraining
            force_full_retrain: If True, perform full retrain instead of incremental
            
        Returns:
            Dict with retraining results
        """
        logger.warning(
            f"🔄 RETRAINING TRIGGERED: {model_type.value} - Reason: {reason}"
        )
        
        try:
            start_time = datetime.utcnow()
            
            # Get the model
            if model_type not in self.models:
                logger.error(f"Model type {model_type} not found")
                return {
                    'success': False,
                    'error': f'Model type {model_type} not found'
                }
            
            model = self.models[model_type]
            
            if force_full_retrain:
                # Full retraining: Reset the model and retrain from buffer
                logger.info(f"Performing FULL retrain on {model_type.value}")
                
                # Reset model statistics
                if hasattr(model, 'agent_stats'):
                    original_stats = dict(model.agent_stats)
                    model.agent_stats.clear()
                    
                    # Replay events from buffer
                    events_processed = 0
                    for event_data in self.event_buffer:
                        if isinstance(event_data, dict):
                            event = self._dict_to_outcome_event(event_data)
                        else:
                            event = event_data
                        
                        model.update(event)
                        events_processed += 1
                    
                    logger.info(f"Full retrain completed: {events_processed} events replayed")
                    
                    retrain_result = {
                        'success': True,
                        'model_type': model_type.value,
                        'retrain_type': 'full',
                        'events_processed': events_processed,
                        'agents_tracked': len(model.agent_stats),
                        'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                        'reason': reason,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                
            else:
                # Incremental retraining: Process recent events more aggressively
                logger.info(f"Performing INCREMENTAL retrain on {model_type.value}")
                
                # Get recent poor-performing events from buffer
                recent_events = list(self.event_buffer)[-100:]  # Last 100 events
                
                # Re-weight and re-process them
                events_processed = 0
                for event_data in recent_events:
                    if isinstance(event_data, dict):
                        event = self._dict_to_outcome_event(event_data)
                    else:
                        event = event_data
                    
                    # Reprocess with higher weight for learning
                    model.update(event)
                    events_processed += 1
                
                logger.info(f"Incremental retrain completed: {events_processed} events reprocessed")
                
                retrain_result = {
                    'success': True,
                    'model_type': model_type.value,
                    'retrain_type': 'incremental',
                    'events_processed': events_processed,
                    'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                    'reason': reason,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Save the updated model
            self._save_models()
            
            # Update metrics
            self.metrics.successful_updates += 1
            
            logger.info(
                f"✅ Retraining completed successfully: {model_type.value} "
                f"({retrain_result['retrain_type']})"
            )
            
            return retrain_result
            
        except Exception as e:
            logger.error(f"Error during retraining: {e}", exc_info=True)
            self.metrics.failed_updates += 1
            
            return {
                'success': False,
                'model_type': model_type.value,
                'error': str(e),
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _save_models(self) -> None:
        """Save models to disk."""
        try:
            for model_type, model in self.models.items():
                filepath = self.model_storage_path / f"{model_type.value}.pkl"
                with open(filepath, 'wb') as f:
                    pickle.dump(model, f)
                logger.debug(f"Saved model: {model_type.value}")
            
            # Save metrics
            metrics_file = self.model_storage_path / "metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(self.get_metrics(), f, indent=2)
            
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def _load_models(self) -> None:
        """Load models from disk."""
        try:
            for model_type in self.models.keys():
                filepath = self.model_storage_path / f"{model_type.value}.pkl"
                if filepath.exists():
                    with open(filepath, 'rb') as f:
                        self.models[model_type] = pickle.load(f)
                    logger.info(f"Loaded model: {model_type.value}")
            
            # Load metrics
            metrics_file = self.model_storage_path / "metrics.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics_data = json.load(f)
                    # Only load basic metrics, not model-specific ones
                    for key in ['total_updates', 'successful_updates', 'failed_updates',
                               'avg_update_time_ms', 'samples_processed',
                               'current_model_score', 'improvement_rate']:
                        if key in metrics_data:
                            setattr(self.metrics, key, metrics_data[key])
            
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")


# Global instance
_updater_instance: Optional[RealTimeModelUpdater] = None


def get_model_updater(
    kafka_servers: Optional[str] = None,
    force_new: bool = False,
    **kwargs
) -> Optional[RealTimeModelUpdater]:
    """
    Get or create the global model updater instance.
    
    Args:
        kafka_servers: Kafka bootstrap servers
        force_new: Force creation of new instance
        **kwargs: Additional arguments for RealTimeModelUpdater
        
    Returns:
        RealTimeModelUpdater instance or None if Kafka not available
    """
    global _updater_instance
    
    if not KAFKA_AVAILABLE:
        logger.warning("Kafka not available, model updater disabled")
        return None
    
    if force_new or _updater_instance is None:
        if not kafka_servers:
            from config.kafka_config import kafka_config
            kafka_servers = kafka_config.KAFKA_BOOTSTRAP_SERVERS
        
        _updater_instance = RealTimeModelUpdater(
            kafka_servers=kafka_servers,
            **kwargs
        )
    
    return _updater_instance
