
"""
Internal Performance Monitor Service

A comprehensive monitoring system that tracks core metrics across the agent architecture:
- Task success rates per agent and overall system
- Resource costs (API calls, tokens, compute time, memory)
- Model accuracy against real-world outcomes
- Performance trends and anomaly detection
- Real-time alerts and recommendations
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import json
import time
import statistics
from collections import defaultdict, deque
from threading import Lock, Thread
import asyncio

from utils.logging import get_logger
from database import get_session
from database.models import (
    AgentRun, Run, ModelVersion, LearningEvent,
    AgentRunStatus, RunStatus
)

logger = get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics tracked."""
    SUCCESS_RATE = "success_rate"
    LATENCY = "latency"
    TOKEN_USAGE = "token_usage"
    API_CALLS = "api_calls"
    COST = "cost"
    MEMORY = "memory"
    CPU = "cpu"
    ACCURACY = "accuracy"
    QUALITY = "quality"
    ERROR_RATE = "error_rate"


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    
    # Success metrics
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    partial_tasks: int = 0
    success_rate: float = 0.0
    
    # Timing metrics
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    
    # Resource metrics
    total_tokens: int = 0
    total_api_calls: int = 0
    total_cost: float = 0.0
    avg_memory_mb: float = 0.0
    avg_cpu_ms: float = 0.0
    
    # Quality metrics
    avg_quality_score: float = 0.0
    avg_confidence: float = 0.0
    avg_accuracy: float = 0.0
    
    # Error metrics
    error_rate: float = 0.0
    timeout_rate: float = 0.0
    retry_rate: float = 0.0
    
    # Trend indicators
    success_rate_trend: str = "stable"  # "improving", "stable", "degrading"
    latency_trend: str = "stable"
    cost_trend: str = "stable"
    
    # Metadata
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    sample_size: int = 0


@dataclass
class AgentPerformance:
    """Performance metrics for a specific agent."""
    agent_name: str
    agent_type: str
    metrics: PerformanceMetrics
    last_run: Optional[str] = None
    status: str = "active"
    
    # Agent-specific insights
    specialization_score: float = 0.0  # How well agent performs its specialty
    reliability_score: float = 0.0  # Consistency of performance
    efficiency_score: float = 0.0  # Speed vs quality balance
    
    
@dataclass
class PerformanceAlert:
    """Alert for performance issues."""
    alert_id: str
    level: AlertLevel
    metric_type: MetricType
    message: str
    current_value: Any
    threshold: Any
    agent_name: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    recommendation: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccuracyMeasurement:
    """Measurement of model/agent accuracy against real outcomes."""
    measurement_id: str
    agent_name: str
    task_id: str
    predicted_outcome: Any
    actual_outcome: Any
    accuracy_score: float  # 0-1
    timestamp: str
    feedback_source: str  # "user", "automated", "system"
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """
    Internal Performance Monitor Service.
    
    Continuously tracks and analyzes performance metrics across all agents,
    providing real-time monitoring, trend analysis, and alerting.
    """
    
    def __init__(
        self,
        window_size_minutes: int = 60,
        alert_thresholds: Optional[Dict[str, Any]] = None,
        enable_auto_alerts: bool = True,
        enable_trend_analysis: bool = True,
        enable_auto_retraining: bool = True,
        model_updater = None,
        db_session_factory=None
    ):
        """
        Initialize Performance Monitor.
        
        Args:
            window_size_minutes: Time window for rolling metrics
            alert_thresholds: Custom alert thresholds
            enable_auto_alerts: Enable automatic alerting
            enable_trend_analysis: Enable trend detection
            enable_auto_retraining: Enable automatic model retraining
            model_updater: RealTimeModelUpdater instance for autonomous retraining
            db_session_factory: Database session factory
        """
        self.window_size_minutes = window_size_minutes
        self.enable_auto_alerts = enable_auto_alerts
        self.enable_trend_analysis = enable_trend_analysis
        self.enable_auto_retraining = enable_auto_retraining
        self.model_updater = model_updater
        self.db_session_factory = db_session_factory or get_session
        
        # Default alert thresholds
        self.alert_thresholds = {
            "success_rate_min": 0.80,  # Alert if below 80%
            "error_rate_max": 0.15,  # Alert if above 15%
            "latency_p95_max_ms": 5000,  # Alert if p95 > 5s
            "cost_per_task_max": 1.0,  # Alert if > $1 per task
            "accuracy_min": 0.70,  # Alert if accuracy < 70%
            "memory_max_mb": 1024,  # Alert if memory > 1GB
            "token_per_task_max": 5000,  # Alert if > 5k tokens per task
        }
        if alert_thresholds:
            self.alert_thresholds.update(alert_thresholds)
        
        # In-memory metric storage (for real-time tracking)
        self._lock = Lock()
        self._metrics_buffer: deque = deque(maxlen=10000)  # Last 10k events
        self._agent_metrics: Dict[str, List[Dict]] = defaultdict(list)
        self._accuracy_measurements: deque = deque(maxlen=1000)
        self._alerts: deque = deque(maxlen=100)
        
        # Running statistics
        self._running_stats: Dict[str, Any] = defaultdict(dict)
        
        # Background processing
        self._monitoring_active = False
        self._monitor_thread: Optional[Thread] = None
        
        logger.info(
            f"PerformanceMonitor initialized (window={window_size_minutes}m, "
            f"auto_alerts={enable_auto_alerts})"
        )
    
    def start(self):
        """Start background monitoring thread."""
        if self._monitoring_active:
            logger.warning("PerformanceMonitor already running")
            return
        
        self._monitoring_active = True
        self._monitor_thread = Thread(target=self._background_monitor, daemon=True)
        self._monitor_thread.start()
        logger.info("PerformanceMonitor background thread started")
    
    def stop(self):
        """Stop background monitoring."""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("PerformanceMonitor stopped")
    
    def _background_monitor(self):
        """Background thread for periodic monitoring tasks."""
        while self._monitoring_active:
            try:
                # Perform periodic analysis
                self._analyze_trends()
                self._check_alerts()
                self._cleanup_old_data()
                
                # Sleep for a minute
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in background monitor: {e}", exc_info=True)
    
    # ==================== Event Recording ====================
    
    def record_agent_run(
        self,
        run_id: str,
        agent_name: str,
        agent_type: str,
        status: str,
        duration_ms: float,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None,
        memory_mb: Optional[float] = None,
        cpu_ms: Optional[float] = None,
        quality_score: Optional[float] = None,
        confidence: Optional[float] = None,
        error_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Record an agent run event.
        
        Args:
            run_id: Run identifier
            agent_name: Agent name
            agent_type: Agent type
            status: Run status ('success', 'failure', 'partial', etc.)
            duration_ms: Execution duration in milliseconds
            tokens_used: LLM tokens consumed
            cost: Estimated cost in dollars
            memory_mb: Memory used in MB
            cpu_ms: CPU time in milliseconds
            quality_score: Quality score (0-1)
            confidence: Confidence score (0-1)
            error_type: Error type if failed
            metadata: Additional metadata
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": run_id,
            "agent_name": agent_name,
            "agent_type": agent_type,
            "status": status,
            "duration_ms": duration_ms,
            "tokens_used": tokens_used or 0,
            "cost": cost or 0.0,
            "memory_mb": memory_mb or 0.0,
            "cpu_ms": cpu_ms or 0.0,
            "quality_score": quality_score,
            "confidence": confidence,
            "error_type": error_type,
            "metadata": metadata or {}
        }
        
        with self._lock:
            self._metrics_buffer.append(event)
            self._agent_metrics[agent_name].append(event)
            
            # Keep only recent events per agent
            if len(self._agent_metrics[agent_name]) > 1000:
                self._agent_metrics[agent_name] = self._agent_metrics[agent_name][-1000:]
        
        # Check for immediate alerts
        if self.enable_auto_alerts:
            self._check_event_alerts(event)
        
        logger.debug(f"Recorded performance event for {agent_name}: {status}")
    
    def record_accuracy(
        self,
        agent_name: str,
        task_id: str,
        predicted_outcome: Any,
        actual_outcome: Any,
        feedback_source: str = "user",
        metadata: Optional[Dict] = None
    ):
        """
        Record accuracy measurement against real-world outcome.
        
        Args:
            agent_name: Agent that made the prediction
            task_id: Task identifier
            predicted_outcome: What the agent predicted
            actual_outcome: What actually happened
            feedback_source: Source of feedback ('user', 'automated', 'system')
            metadata: Additional metadata
        """
        # Calculate accuracy score
        accuracy_score = self._calculate_accuracy_score(
            predicted_outcome, actual_outcome
        )
        
        measurement = AccuracyMeasurement(
            measurement_id=f"{task_id}_{int(time.time()*1000)}",
            agent_name=agent_name,
            task_id=task_id,
            predicted_outcome=predicted_outcome,
            actual_outcome=actual_outcome,
            accuracy_score=accuracy_score,
            timestamp=datetime.utcnow().isoformat(),
            feedback_source=feedback_source,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._accuracy_measurements.append(asdict(measurement))
        
        logger.info(
            f"Recorded accuracy for {agent_name}: {accuracy_score:.2f} "
            f"(source={feedback_source})"
        )
    
    def _calculate_accuracy_score(self, predicted: Any, actual: Any) -> float:
        """
        Calculate accuracy score between predicted and actual outcomes.
        
        This is a flexible scoring function that handles different types of outputs.
        """
        try:
            # Exact match
            if predicted == actual:
                return 1.0
            
            # For numeric values, use relative error
            if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
                if actual == 0:
                    return 0.0 if predicted != 0 else 1.0
                error = abs(predicted - actual) / abs(actual)
                return max(0.0, 1.0 - error)
            
            # For strings, use similarity
            if isinstance(predicted, str) and isinstance(actual, str):
                # Simple word overlap similarity
                pred_words = set(predicted.lower().split())
                actual_words = set(actual.lower().split())
                if not actual_words:
                    return 0.0
                overlap = len(pred_words & actual_words)
                return overlap / len(actual_words)
            
            # For dictionaries, check key overlap and value similarity
            if isinstance(predicted, dict) and isinstance(actual, dict):
                if not actual:
                    return 1.0 if not predicted else 0.0
                key_overlap = len(set(predicted.keys()) & set(actual.keys()))
                key_score = key_overlap / len(actual.keys())
                
                # Check value accuracy for common keys
                value_scores = []
                for key in set(predicted.keys()) & set(actual.keys()):
                    value_scores.append(
                        self._calculate_accuracy_score(predicted[key], actual[key])
                    )
                value_score = statistics.mean(value_scores) if value_scores else 0.0
                
                return (key_score + value_score) / 2
            
            # For lists, check element overlap
            if isinstance(predicted, list) and isinstance(actual, list):
                if not actual:
                    return 1.0 if not predicted else 0.0
                overlap = len(set(predicted) & set(actual))
                return overlap / len(actual)
            
            # Default: partial credit for being the same type
            return 0.3 if type(predicted) == type(actual) else 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating accuracy: {e}")
            return 0.0
    
    # ==================== Metrics Calculation ====================
    
    def get_system_metrics(
        self,
        time_window_minutes: Optional[int] = None
    ) -> PerformanceMetrics:
        """
        Get system-wide performance metrics.
        
        Args:
            time_window_minutes: Time window to analyze (default: use configured window)
            
        Returns:
            PerformanceMetrics: Aggregated system metrics
        """
        window = time_window_minutes or self.window_size_minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=window)
        
        with self._lock:
            # Filter events within time window
            events = [
                e for e in self._metrics_buffer
                if datetime.fromisoformat(e["timestamp"]) >= cutoff_time
            ]
        
        return self._calculate_metrics(events)
    
    def get_agent_metrics(
        self,
        agent_name: str,
        time_window_minutes: Optional[int] = None
    ) -> AgentPerformance:
        """
        Get performance metrics for a specific agent.
        
        Args:
            agent_name: Agent name
            time_window_minutes: Time window to analyze
            
        Returns:
            AgentPerformance: Agent-specific metrics
        """
        window = time_window_minutes or self.window_size_minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=window)
        
        with self._lock:
            if agent_name not in self._agent_metrics:
                return AgentPerformance(
                    agent_name=agent_name,
                    agent_type="unknown",
                    metrics=PerformanceMetrics()
                )
            
            # Filter events
            events = [
                e for e in self._agent_metrics[agent_name]
                if datetime.fromisoformat(e["timestamp"]) >= cutoff_time
            ]
        
        if not events:
            return AgentPerformance(
                agent_name=agent_name,
                agent_type="unknown",
                metrics=PerformanceMetrics(),
                status="inactive"
            )
        
        metrics = self._calculate_metrics(events)
        agent_type = events[0]["agent_type"]
        last_run = events[-1]["timestamp"]
        
        # Calculate agent-specific scores
        specialization_score = self._calculate_specialization_score(events)
        reliability_score = metrics.success_rate
        efficiency_score = self._calculate_efficiency_score(metrics)
        
        return AgentPerformance(
            agent_name=agent_name,
            agent_type=agent_type,
            metrics=metrics,
            last_run=last_run,
            status="active",
            specialization_score=specialization_score,
            reliability_score=reliability_score,
            efficiency_score=efficiency_score
        )
    
    def _calculate_metrics(self, events: List[Dict]) -> PerformanceMetrics:
        """Calculate performance metrics from event list."""
        if not events:
            return PerformanceMetrics()
        
        # Count statuses
        total = len(events)
        successful = sum(1 for e in events if e["status"] == "success")
        failed = sum(1 for e in events if e["status"] == "failure")
        partial = sum(1 for e in events if e["status"] == "partial")
        
        # Latency metrics
        latencies = [e["duration_ms"] for e in events]
        latencies.sort()
        
        # Resource metrics
        total_tokens = sum(e.get("tokens_used", 0) for e in events)
        total_cost = sum(e.get("cost", 0.0) for e in events)
        memory_values = [e.get("memory_mb", 0) for e in events if e.get("memory_mb")]
        cpu_values = [e.get("cpu_ms", 0) for e in events if e.get("cpu_ms")]
        
        # Quality metrics
        quality_values = [
            e["quality_score"] for e in events
            if e.get("quality_score") is not None
        ]
        confidence_values = [
            e["confidence"] for e in events
            if e.get("confidence") is not None
        ]
        
        # Get accuracy metrics
        accuracy_values = self._get_accuracy_for_events(events)
        
        return PerformanceMetrics(
            total_tasks=total,
            successful_tasks=successful,
            failed_tasks=failed,
            partial_tasks=partial,
            success_rate=successful / total if total > 0 else 0.0,
            
            avg_latency_ms=statistics.mean(latencies) if latencies else 0.0,
            p50_latency_ms=latencies[len(latencies)//2] if latencies else 0.0,
            p95_latency_ms=latencies[int(len(latencies)*0.95)] if latencies else 0.0,
            p99_latency_ms=latencies[int(len(latencies)*0.99)] if latencies else 0.0,
            max_latency_ms=max(latencies) if latencies else 0.0,
            
            total_tokens=total_tokens,
            total_api_calls=total,
            total_cost=total_cost,
            avg_memory_mb=statistics.mean(memory_values) if memory_values else 0.0,
            avg_cpu_ms=statistics.mean(cpu_values) if cpu_values else 0.0,
            
            avg_quality_score=statistics.mean(quality_values) if quality_values else 0.0,
            avg_confidence=statistics.mean(confidence_values) if confidence_values else 0.0,
            avg_accuracy=statistics.mean(accuracy_values) if accuracy_values else 0.0,
            
            error_rate=failed / total if total > 0 else 0.0,
            timeout_rate=sum(1 for e in events if e.get("error_type") == "timeout") / total if total > 0 else 0.0,
            retry_rate=sum(1 for e in events if e.get("metadata", {}).get("retry_count", 0) > 0) / total if total > 0 else 0.0,
            
            window_start=events[0]["timestamp"] if events else None,
            window_end=events[-1]["timestamp"] if events else None,
            sample_size=total
        )
    
    def _get_accuracy_for_events(self, events: List[Dict]) -> List[float]:
        """Get accuracy measurements matching the given events."""
        with self._lock:
            accuracies = []
            event_ids = {e["run_id"] for e in events}
            
            for measurement in self._accuracy_measurements:
                if measurement["task_id"] in event_ids:
                    accuracies.append(measurement["accuracy_score"])
            
            return accuracies
    
    def _calculate_specialization_score(self, events: List[Dict]) -> float:
        """
        Calculate how well an agent performs its specialized tasks.
        
        Higher scores mean the agent consistently performs well on its specialty.
        """
        if not events:
            return 0.0
        
        # For now, use success rate weighted by quality scores
        success_count = 0
        quality_sum = 0.0
        
        for event in events:
            if event["status"] == "success":
                success_count += 1
                quality_sum += event.get("quality_score", 0.5)
        
        if success_count == 0:
            return 0.0
        
        avg_quality = quality_sum / success_count
        success_rate = success_count / len(events)
        
        return (success_rate + avg_quality) / 2
    
    def _calculate_efficiency_score(self, metrics: PerformanceMetrics) -> float:
        """
        Calculate efficiency score (balance of speed and quality).
        
        Lower latency + higher quality = higher efficiency.
        """
        if metrics.total_tasks == 0:
            return 0.0
        
        # Normalize latency (inverse relationship - lower is better)
        # Assume 1000ms is the target, 5000ms is very slow
        latency_score = max(0.0, 1.0 - (metrics.avg_latency_ms - 1000) / 4000)
        
        # Quality score (direct relationship - higher is better)
        quality_score = metrics.avg_quality_score
        
        # Success rate
        success_score = metrics.success_rate
        
        # Weighted average
        efficiency = (
            0.3 * latency_score +
            0.4 * quality_score +
            0.3 * success_score
        )
        
        return max(0.0, min(1.0, efficiency))
    
    # ==================== Alerting ====================
    
    def _check_event_alerts(self, event: Dict):
        """Check if single event triggers any alerts."""
        alerts = []
        
        # Check latency
        if event["duration_ms"] > self.alert_thresholds["latency_p95_max_ms"]:
            alerts.append(PerformanceAlert(
                alert_id=f"latency_{event['run_id']}",
                level=AlertLevel.WARNING,
                metric_type=MetricType.LATENCY,
                message=f"High latency detected for {event['agent_name']}",
                current_value=event["duration_ms"],
                threshold=self.alert_thresholds["latency_p95_max_ms"],
                agent_name=event["agent_name"],
                recommendation="Check agent workload and LLM performance"
            ))
        
        # Check memory
        if event.get("memory_mb", 0) > self.alert_thresholds["memory_max_mb"]:
            alerts.append(PerformanceAlert(
                alert_id=f"memory_{event['run_id']}",
                level=AlertLevel.CRITICAL,
                metric_type=MetricType.MEMORY,
                message=f"High memory usage by {event['agent_name']}",
                current_value=event["memory_mb"],
                threshold=self.alert_thresholds["memory_max_mb"],
                agent_name=event["agent_name"],
                recommendation="Investigate memory leaks or optimize data structures"
            ))
        
        # Store alerts
        if alerts:
            with self._lock:
                self._alerts.extend(alerts)
            
            for alert in alerts:
                logger.warning(f"ALERT: {alert.message}")
    
    def _check_alerts(self):
        """Periodic alert checking based on aggregated metrics."""
        if not self.enable_auto_alerts:
            return
        
        try:
            # Get system metrics
            metrics = self.get_system_metrics()
            
            alerts = []
            
            # Check success rate
            if metrics.success_rate < self.alert_thresholds["success_rate_min"]:
                alerts.append(PerformanceAlert(
                    alert_id=f"success_rate_{int(time.time())}",
                    level=AlertLevel.CRITICAL,
                    metric_type=MetricType.SUCCESS_RATE,
                    message="System success rate below threshold",
                    current_value=metrics.success_rate,
                    threshold=self.alert_thresholds["success_rate_min"],
                    recommendation="Review recent failures and adjust agent configurations"
                ))
            
            # Check error rate
            if metrics.error_rate > self.alert_thresholds["error_rate_max"]:
                alerts.append(PerformanceAlert(
                    alert_id=f"error_rate_{int(time.time())}",
                    level=AlertLevel.WARNING,
                    metric_type=MetricType.ERROR_RATE,
                    message="High error rate detected",
                    current_value=metrics.error_rate,
                    threshold=self.alert_thresholds["error_rate_max"],
                    recommendation="Check logs for common error patterns"
                ))
            
            # Check cost
            if metrics.total_tasks > 0:
                cost_per_task = metrics.total_cost / metrics.total_tasks
                if cost_per_task > self.alert_thresholds["cost_per_task_max"]:
                    alerts.append(PerformanceAlert(
                        alert_id=f"cost_{int(time.time())}",
                        level=AlertLevel.WARNING,
                        metric_type=MetricType.COST,
                        message="High cost per task detected",
                        current_value=cost_per_task,
                        threshold=self.alert_thresholds["cost_per_task_max"],
                        recommendation="Optimize LLM prompts or consider cheaper models"
                    ))
            
            # Check accuracy
            if metrics.avg_accuracy > 0 and metrics.avg_accuracy < self.alert_thresholds["accuracy_min"]:
                alerts.append(PerformanceAlert(
                    alert_id=f"accuracy_{int(time.time())}",
                    level=AlertLevel.CRITICAL,
                    metric_type=MetricType.ACCURACY,
                    message="Low accuracy against real-world outcomes",
                    current_value=metrics.avg_accuracy,
                    threshold=self.alert_thresholds["accuracy_min"],
                    recommendation="Review model training data and retrain if necessary"
                ))
                
                # AUTONOMOUS RETRAINING TRIGGER
                if self.enable_auto_retraining and self.model_updater:
                    logger.warning(
                        f"🚨 Accuracy degraded to {metrics.avg_accuracy:.1%} "
                        f"(threshold: {self.alert_thresholds['accuracy_min']:.1%}) - "
                        f"Triggering autonomous retraining..."
                    )
                    
                    try:
                        # Import here to avoid circular dependency
                        from core.online_learning import ModelType
                        
                        # Trigger retraining
                        retrain_result = self.model_updater.trigger_retraining(
                            model_type=ModelType.AGENT_SELECTION,
                            reason=f"Accuracy dropped to {metrics.avg_accuracy:.1%}",
                            force_full_retrain=False  # Start with incremental
                        )
                        
                        if retrain_result.get('success'):
                            logger.info(
                                f"✅ Autonomous retraining completed: "
                                f"{retrain_result.get('events_processed', 0)} events processed"
                            )
                            
                            # Create success alert
                            alerts.append(PerformanceAlert(
                                alert_id=f"retrain_success_{int(time.time())}",
                                level=AlertLevel.INFO,
                                metric_type=MetricType.ACCURACY,
                                message="Autonomous retraining completed successfully",
                                current_value=retrain_result.get('events_processed', 0),
                                threshold=0,
                                recommendation="Monitor accuracy over next hour to verify improvement",
                                details=retrain_result
                            ))
                        else:
                            logger.error(f"Autonomous retraining failed: {retrain_result.get('error')}")
                            
                    except Exception as e:
                        logger.error(f"Failed to trigger autonomous retraining: {e}", exc_info=True)
            
            # Store alerts
            if alerts:
                with self._lock:
                    self._alerts.extend(alerts)
                
                for alert in alerts:
                    logger.warning(f"PERIODIC ALERT: {alert.message}")
        
        except Exception as e:
            logger.error(f"Error checking alerts: {e}", exc_info=True)
    
    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        agent_name: Optional[str] = None,
        limit: int = 50
    ) -> List[PerformanceAlert]:
        """
        Get recent alerts.
        
        Args:
            level: Filter by alert level
            agent_name: Filter by agent
            limit: Maximum alerts to return
            
        Returns:
            List[PerformanceAlert]: Filtered alerts
        """
        with self._lock:
            alerts = list(self._alerts)
        
        # Apply filters
        if level:
            alerts = [a for a in alerts if a.level == level]
        if agent_name:
            alerts = [a for a in alerts if a.agent_name == agent_name]
        
        return alerts[-limit:]
    
    # ==================== Trend Analysis ====================
    
    def _analyze_trends(self):
        """Analyze performance trends."""
        if not self.enable_trend_analysis:
            return
        
        try:
            # Get metrics for two time windows
            current_metrics = self.get_system_metrics(time_window_minutes=60)
            previous_metrics = self.get_system_metrics(time_window_minutes=120)
            
            # Calculate trends
            success_rate_trend = self._calculate_trend(
                previous_metrics.success_rate,
                current_metrics.success_rate
            )
            
            latency_trend = self._calculate_trend(
                previous_metrics.avg_latency_ms,
                current_metrics.avg_latency_ms,
                inverse=True  # Lower latency is better
            )
            
            cost_trend = self._calculate_trend(
                previous_metrics.total_cost / max(previous_metrics.total_tasks, 1),
                current_metrics.total_cost / max(current_metrics.total_tasks, 1),
                inverse=True
            )
            
            # Store trends
            current_metrics.success_rate_trend = success_rate_trend
            current_metrics.latency_trend = latency_trend
            current_metrics.cost_trend = cost_trend
            
            with self._lock:
                self._running_stats["trends"] = {
                    "success_rate": success_rate_trend,
                    "latency": latency_trend,
                    "cost": cost_trend,
                    "updated_at": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}", exc_info=True)
    
    def _calculate_trend(
        self,
        previous_value: float,
        current_value: float,
        inverse: bool = False
    ) -> str:
        """
        Calculate trend direction.
        
        Args:
            previous_value: Previous metric value
            current_value: Current metric value
            inverse: If True, lower values are better
            
        Returns:
            str: "improving", "stable", or "degrading"
        """
        if previous_value == 0:
            return "stable"
        
        change_pct = (current_value - previous_value) / previous_value
        
        # Threshold for "stable" (within 5%)
        if abs(change_pct) < 0.05:
            return "stable"
        
        # Determine if change is positive or negative
        if inverse:
            return "improving" if change_pct < 0 else "degrading"
        else:
            return "improving" if change_pct > 0 else "degrading"
    
    # ==================== Reporting ====================
    
    def generate_report(
        self,
        include_agents: bool = True,
        time_window_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Args:
            include_agents: Include per-agent metrics
            time_window_minutes: Time window to analyze
            
        Returns:
            Dict: Complete performance report
        """
        system_metrics = self.get_system_metrics(time_window_minutes)
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "time_window_minutes": time_window_minutes or self.window_size_minutes,
            "system_metrics": asdict(system_metrics),
            "health_score": self._calculate_health_score(system_metrics),
        }
        
        if include_agents:
            with self._lock:
                agent_names = list(self._agent_metrics.keys())
            
            report["agent_metrics"] = {
                agent_name: asdict(self.get_agent_metrics(agent_name, time_window_minutes))
                for agent_name in agent_names
            }
        
        # Add alerts
        recent_alerts = self.get_alerts(limit=20)
        report["recent_alerts"] = [asdict(alert) for alert in recent_alerts]
        
        # Add recommendations
        report["recommendations"] = self._generate_recommendations(system_metrics)
        
        return report
    
    def _calculate_health_score(self, metrics: PerformanceMetrics) -> float:
        """
        Calculate overall system health score (0-100).
        
        Combines multiple factors into a single health indicator.
        """
        if metrics.total_tasks == 0:
            return 100.0  # No data = assumed healthy
        
        # Weight factors
        success_score = metrics.success_rate * 40  # 40 points
        latency_score = max(0, 30 - (metrics.avg_latency_ms / 1000) * 3)  # 30 points
        error_score = max(0, 20 - (metrics.error_rate * 100))  # 20 points
        accuracy_score = metrics.avg_accuracy * 10 if metrics.avg_accuracy > 0 else 10  # 10 points
        
        health_score = success_score + latency_score + error_score + accuracy_score
        
        return min(100.0, max(0.0, health_score))
    
    def _generate_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """Generate actionable recommendations based on metrics."""
        recommendations = []
        
        if metrics.success_rate < 0.90:
            recommendations.append(
                f"Success rate is {metrics.success_rate:.1%}. "
                "Review failure logs and consider adjusting agent prompts or retry strategies."
            )
        
        if metrics.avg_latency_ms > 3000:
            recommendations.append(
                f"Average latency is {metrics.avg_latency_ms:.0f}ms. "
                "Consider using faster LLM models or implementing caching."
            )
        
        if metrics.total_tasks > 0:
            cost_per_task = metrics.total_cost / metrics.total_tasks
            if cost_per_task > 0.50:
                recommendations.append(
                    f"Cost per task is ${cost_per_task:.2f}. "
                    "Optimize prompts, reduce token usage, or switch to cheaper models."
                )
        
        if metrics.avg_accuracy > 0 and metrics.avg_accuracy < 0.75:
            recommendations.append(
                f"Accuracy is {metrics.avg_accuracy:.1%}. "
                "Consider retraining models with recent feedback data."
            )
        
        if metrics.error_rate > 0.10:
            recommendations.append(
                f"Error rate is {metrics.error_rate:.1%}. "
                "Implement better error handling and increase retry limits."
            )
        
        if not recommendations:
            recommendations.append("System is performing well. No immediate actions needed.")
        
        return recommendations
    
    # ==================== Database Integration ====================
    
    def sync_with_database(self, lookback_hours: int = 24):
        """
        Sync performance metrics from database.
        
        Loads recent agent runs from the database to build a complete picture.
        
        Args:
            lookback_hours: Hours to look back in database
        """
        try:
            db = self.db_session_factory()
            cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            
            # Query recent agent runs
            agent_runs = db.query(AgentRun).filter(
                AgentRun.created_at >= cutoff_time
            ).all()
            
            logger.info(f"Syncing {len(agent_runs)} agent runs from database")
            
            for agent_run in agent_runs:
                # Convert to performance event
                status = "success" if agent_run.status == AgentRunStatus.COMPLETED else "failure"
                
                self.record_agent_run(
                    run_id=agent_run.run_id,
                    agent_name=agent_run.agent_name,
                    agent_type=agent_run.agent_type,
                    status=status,
                    duration_ms=agent_run.execution_time_ms or 0,
                    metadata=agent_run.output_data or {}
                )
            
            db.close()
            logger.info("Database sync completed")
            
        except Exception as e:
            logger.error(f"Error syncing with database: {e}", exc_info=True)
    
    # ==================== Cleanup ====================
    
    def _cleanup_old_data(self):
        """Clean up old data to prevent memory bloat."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            with self._lock:
                # Clean metrics buffer
                self._metrics_buffer = deque(
                    [e for e in self._metrics_buffer
                     if datetime.fromisoformat(e["timestamp"]) >= cutoff_time],
                    maxlen=10000
                )
                
                # Clean agent metrics
                for agent_name in list(self._agent_metrics.keys()):
                    self._agent_metrics[agent_name] = [
                        e for e in self._agent_metrics[agent_name]
                        if datetime.fromisoformat(e["timestamp"]) >= cutoff_time
                    ]
                
                # Clean accuracy measurements
                self._accuracy_measurements = deque(
                    [m for m in self._accuracy_measurements
                     if datetime.fromisoformat(m["timestamp"]) >= cutoff_time],
                    maxlen=1000
                )
        
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}", exc_info=True)
    
    def trigger_retraining(
        self,
        reason: str = "Manual trigger from PerformanceMonitor",
        force_full_retrain: bool = False
    ) -> Dict[str, Any]:
        """
        Manually trigger model retraining.
        
        This can be called directly or is automatically called when
        performance degrades below thresholds (if auto_retraining is enabled).
        
        Args:
            reason: Reason for triggering retraining
            force_full_retrain: If True, perform full retrain instead of incremental
            
        Returns:
            Dict with retraining results
        """
        if not self.model_updater:
            logger.error("Cannot trigger retraining: model_updater not configured")
            return {
                'success': False,
                'error': 'No model updater configured'
            }
        
        try:
            from core.online_learning import ModelType
            
            logger.info(f"Manually triggering retraining: {reason}")
            
            result = self.model_updater.trigger_retraining(
                model_type=ModelType.AGENT_SELECTION,
                reason=reason,
                force_full_retrain=force_full_retrain
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to trigger retraining: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics."""
        with self._lock:
            return {
                "events_buffered": len(self._metrics_buffer),
                "agents_tracked": len(self._agent_metrics),
                "accuracy_measurements": len(self._accuracy_measurements),
                "active_alerts": len(self._alerts),
                "monitoring_active": self._monitoring_active,
                "auto_retraining_enabled": self.enable_auto_retraining,
                "model_updater_connected": self.model_updater is not None
            }
    
    def __repr__(self) -> str:
        """String representation."""
        stats = self.get_stats()
        return (
            f"<PerformanceMonitor(events={stats['events_buffered']}, "
            f"agents={stats['agents_tracked']}, alerts={stats['active_alerts']})>"
        )


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
        _performance_monitor.start()
    return _performance_monitor


def init_performance_monitor(**kwargs) -> PerformanceMonitor:
    """
    Initialize global performance monitor with custom settings.
    
    Args:
        **kwargs: Arguments to pass to PerformanceMonitor constructor
        
    Returns:
        PerformanceMonitor: Initialized monitor
    """
    global _performance_monitor
    if _performance_monitor is not None:
        _performance_monitor.stop()
    
    _performance_monitor = PerformanceMonitor(**kwargs)
    _performance_monitor.start()
    return _performance_monitor
