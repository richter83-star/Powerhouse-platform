
"""
Dynamic Self-Configuration Manager

Enables agents to autonomously adjust runtime parameters based on
performance metrics from the PerformanceMonitor.

Features:
- Real-time parameter adjustment based on performance metrics
- Configurable adjustment policies and rules
- Safe parameter bounds and validation
- Automatic rollback on performance degradation
- Configuration history and audit trail
- Multiple adjustment strategies (gradual, aggressive, conservative)
"""

from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import time
from threading import Lock
from collections import deque

from utils.logging import get_logger
from core.performance_monitor import PerformanceMetrics, MetricType

logger = get_logger(__name__)


class AdjustmentStrategy(str, Enum):
    """Strategy for parameter adjustments."""
    CONSERVATIVE = "conservative"  # Small, safe adjustments
    BALANCED = "balanced"          # Moderate adjustments
    AGGRESSIVE = "aggressive"      # Large, fast adjustments
    GRADUAL = "gradual"           # Very slow, gradual changes


class ConfigurationScope(str, Enum):
    """Scope of configuration changes."""
    GLOBAL = "global"           # Affects all agents
    AGENT_TYPE = "agent_type"   # Affects specific agent type
    AGENT_INSTANCE = "instance" # Affects single agent instance
    ORCHESTRATOR = "orchestrator" # Affects orchestrator only


@dataclass
class ParameterBounds:
    """Define safe bounds for a parameter."""
    min_value: float
    max_value: float
    default_value: float
    step_size: float
    parameter_type: str = "float"  # float, int, bool, string


@dataclass
class AdjustmentRule:
    """Rule for automatic parameter adjustment."""
    name: str
    description: str
    trigger_metric: MetricType
    trigger_threshold: float
    trigger_operator: str  # "gt", "lt", "gte", "lte", "eq"
    target_parameter: str
    adjustment_value: float
    adjustment_type: str  # "absolute", "relative", "multiply"
    scope: ConfigurationScope
    cooldown_seconds: int = 60
    max_adjustments_per_hour: int = 10
    enabled: bool = True
    priority: int = 5  # 1-10, higher = more important
    
    # State tracking
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    adjustment_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ConfigurationChange:
    """Record of a configuration change."""
    timestamp: datetime
    parameter_name: str
    old_value: Any
    new_value: Any
    reason: str
    rule_name: Optional[str]
    scope: ConfigurationScope
    agent_name: Optional[str] = None
    triggered_by_metric: Optional[str] = None
    metric_value: Optional[float] = None
    success: bool = True
    rollback_at: Optional[datetime] = None


class DynamicConfigManager:
    """
    Manages dynamic runtime configuration adjustments for the agent system.
    """
    
    def __init__(
        self,
        strategy: AdjustmentStrategy = AdjustmentStrategy.BALANCED,
        enable_auto_rollback: bool = True,
        rollback_window_minutes: int = 5,
        history_size: int = 1000
    ):
        """
        Initialize dynamic configuration manager.
        
        Args:
            strategy: Adjustment strategy to use
            enable_auto_rollback: Enable automatic rollback on degradation
            rollback_window_minutes: Time window for rollback evaluation
            history_size: Number of changes to keep in history
        """
        self.strategy = strategy
        self.enable_auto_rollback = enable_auto_rollback
        self.rollback_window_minutes = rollback_window_minutes
        
        # Configuration state
        self.parameters: Dict[str, Any] = {}
        self.parameter_bounds: Dict[str, ParameterBounds] = {}
        self.adjustment_rules: Dict[str, AdjustmentRule] = {}
        
        # History and state
        self.change_history: deque = deque(maxlen=history_size)
        self.pending_rollbacks: List[ConfigurationChange] = []
        
        # Thread safety
        self._lock = Lock()
        
        # Performance baseline (for rollback decisions)
        self.baseline_metrics: Optional[PerformanceMetrics] = None
        
        # Initialize default parameters and rules
        self._initialize_defaults()
        
        logger.info(f"Dynamic Configuration Manager initialized with {strategy} strategy")
    
    def _initialize_defaults(self):
        """Initialize default parameters and adjustment rules."""
        
        # Define configurable parameters with bounds
        self.register_parameter(
            name="planner_search_depth",
            bounds=ParameterBounds(
                min_value=1,
                max_value=10,
                default_value=5,
                step_size=1,
                parameter_type="int"
            ),
            scope=ConfigurationScope.AGENT_TYPE,
            description="Search depth for planning algorithms"
        )
        
        self.register_parameter(
            name="max_retries",
            bounds=ParameterBounds(
                min_value=0,
                max_value=5,
                default_value=3,
                step_size=1,
                parameter_type="int"
            ),
            scope=ConfigurationScope.GLOBAL,
            description="Maximum retry attempts for failed operations"
        )
        
        self.register_parameter(
            name="timeout_seconds",
            bounds=ParameterBounds(
                min_value=5,
                max_value=300,
                default_value=60,
                step_size=5,
                parameter_type="int"
            ),
            scope=ConfigurationScope.GLOBAL,
            description="Operation timeout in seconds"
        )
        
        self.register_parameter(
            name="batch_size",
            bounds=ParameterBounds(
                min_value=1,
                max_value=100,
                default_value=10,
                step_size=5,
                parameter_type="int"
            ),
            scope=ConfigurationScope.GLOBAL,
            description="Batch size for parallel processing"
        )
        
        self.register_parameter(
            name="memory_cache_size_mb",
            bounds=ParameterBounds(
                min_value=10,
                max_value=1000,
                default_value=100,
                step_size=10,
                parameter_type="int"
            ),
            scope=ConfigurationScope.GLOBAL,
            description="Memory cache size in MB"
        )
        
        self.register_parameter(
            name="quality_threshold",
            bounds=ParameterBounds(
                min_value=0.0,
                max_value=1.0,
                default_value=0.7,
                step_size=0.05,
                parameter_type="float"
            ),
            scope=ConfigurationScope.GLOBAL,
            description="Minimum quality threshold for outputs"
        )
        
        # Define default adjustment rules
        
        # Rule 1: Reduce search depth on high latency
        self.add_adjustment_rule(
            AdjustmentRule(
                name="reduce_depth_on_high_latency",
                description="Reduce planner search depth when latency is high",
                trigger_metric=MetricType.LATENCY,
                trigger_threshold=5000,  # 5 seconds
                trigger_operator="gt",
                target_parameter="planner_search_depth",
                adjustment_value=-1,
                adjustment_type="relative",
                scope=ConfigurationScope.AGENT_TYPE,
                cooldown_seconds=120,
                max_adjustments_per_hour=5,
                priority=8
            )
        )
        
        # Rule 2: Increase retries on high error rate
        self.add_adjustment_rule(
            AdjustmentRule(
                name="increase_retries_on_errors",
                description="Increase retry attempts when error rate is high",
                trigger_metric=MetricType.ERROR_RATE,
                trigger_threshold=0.15,  # 15%
                trigger_operator="gt",
                target_parameter="max_retries",
                adjustment_value=1,
                adjustment_type="relative",
                scope=ConfigurationScope.GLOBAL,
                cooldown_seconds=300,
                max_adjustments_per_hour=3,
                priority=7
            )
        )
        
        # Rule 3: Increase timeout on timeout rate
        self.add_adjustment_rule(
            AdjustmentRule(
                name="increase_timeout_on_timeouts",
                description="Increase timeout when timeout rate is high",
                trigger_metric=MetricType.LATENCY,
                trigger_threshold=50000,  # Very high latency
                trigger_operator="gt",
                target_parameter="timeout_seconds",
                adjustment_value=1.2,
                adjustment_type="multiply",
                scope=ConfigurationScope.GLOBAL,
                cooldown_seconds=180,
                max_adjustments_per_hour=4,
                priority=6
            )
        )
        
        # Rule 4: Reduce batch size on high memory usage
        self.add_adjustment_rule(
            AdjustmentRule(
                name="reduce_batch_on_memory",
                description="Reduce batch size when memory usage is high",
                trigger_metric=MetricType.MEMORY,
                trigger_threshold=500,  # 500 MB average
                trigger_operator="gt",
                target_parameter="batch_size",
                adjustment_value=-2,
                adjustment_type="relative",
                scope=ConfigurationScope.GLOBAL,
                cooldown_seconds=240,
                max_adjustments_per_hour=3,
                priority=7
            )
        )
        
        # Rule 5: Increase search depth on good performance
        self.add_adjustment_rule(
            AdjustmentRule(
                name="increase_depth_on_good_perf",
                description="Increase planner depth when performance is good",
                trigger_metric=MetricType.SUCCESS_RATE,
                trigger_threshold=0.95,  # 95% success
                trigger_operator="gt",
                target_parameter="planner_search_depth",
                adjustment_value=1,
                adjustment_type="relative",
                scope=ConfigurationScope.AGENT_TYPE,
                cooldown_seconds=300,
                max_adjustments_per_hour=2,
                priority=4
            )
        )
        
        # Rule 6: Adjust quality threshold based on success rate
        self.add_adjustment_rule(
            AdjustmentRule(
                name="lower_threshold_on_low_success",
                description="Lower quality threshold when success rate is low",
                trigger_metric=MetricType.SUCCESS_RATE,
                trigger_threshold=0.70,  # Below 70%
                trigger_operator="lt",
                target_parameter="quality_threshold",
                adjustment_value=-0.05,
                adjustment_type="relative",
                scope=ConfigurationScope.GLOBAL,
                cooldown_seconds=600,
                max_adjustments_per_hour=2,
                priority=5
            )
        )
    
    def register_parameter(
        self,
        name: str,
        bounds: ParameterBounds,
        scope: ConfigurationScope,
        description: str = "",
        initial_value: Optional[Any] = None
    ):
        """
        Register a configurable parameter.
        
        Args:
            name: Parameter name
            bounds: Parameter bounds
            scope: Configuration scope
            description: Parameter description
            initial_value: Initial value (uses default if None)
        """
        with self._lock:
            self.parameter_bounds[name] = bounds
            value = initial_value if initial_value is not None else bounds.default_value
            self.parameters[name] = self._validate_parameter(name, value)
            
            logger.info(f"Registered parameter '{name}' = {self.parameters[name]} "
                       f"(bounds: {bounds.min_value}-{bounds.max_value})")
    
    def add_adjustment_rule(self, rule: AdjustmentRule):
        """
        Add an adjustment rule.
        
        Args:
            rule: Adjustment rule to add
        """
        with self._lock:
            self.adjustment_rules[rule.name] = rule
            logger.info(f"Added adjustment rule: {rule.name}")
    
    def get_parameter(self, name: str, agent_name: Optional[str] = None) -> Any:
        """
        Get current parameter value.
        
        Args:
            name: Parameter name
            agent_name: Optional agent-specific override
            
        Returns:
            Current parameter value
        """
        with self._lock:
            return self.parameters.get(name)
    
    def set_parameter(
        self,
        name: str,
        value: Any,
        reason: str = "manual",
        rule_name: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> bool:
        """
        Set parameter value with validation.
        
        Args:
            name: Parameter name
            value: New value
            reason: Reason for change
            rule_name: Rule that triggered change
            agent_name: Agent name if agent-specific
            
        Returns:
            bool: True if successful
        """
        with self._lock:
            if name not in self.parameter_bounds:
                logger.warning(f"Parameter '{name}' not registered")
                return False
            
            # Validate new value
            validated_value = self._validate_parameter(name, value)
            old_value = self.parameters.get(name)
            
            if validated_value == old_value:
                logger.debug(f"Parameter '{name}' unchanged: {old_value}")
                return True
            
            # Update parameter
            self.parameters[name] = validated_value
            
            # Record change
            change = ConfigurationChange(
                timestamp=datetime.now(),
                parameter_name=name,
                old_value=old_value,
                new_value=validated_value,
                reason=reason,
                rule_name=rule_name,
                scope=ConfigurationScope.GLOBAL,
                agent_name=agent_name,
                success=True
            )
            
            self.change_history.append(change)
            
            # Schedule rollback check if enabled
            if self.enable_auto_rollback:
                change.rollback_at = datetime.now() + timedelta(
                    minutes=self.rollback_window_minutes
                )
                self.pending_rollbacks.append(change)
            
            logger.info(f"Parameter '{name}' changed: {old_value} -> {validated_value} "
                       f"(reason: {reason})")
            
            return True
    
    def _validate_parameter(self, name: str, value: Any) -> Any:
        """Validate and clamp parameter value."""
        bounds = self.parameter_bounds[name]
        
        # Type conversion
        if bounds.parameter_type == "int":
            value = int(round(value))
        elif bounds.parameter_type == "float":
            value = float(value)
        elif bounds.parameter_type == "bool":
            value = bool(value)
        
        # Bounds checking
        if bounds.parameter_type in ["int", "float"]:
            value = max(bounds.min_value, min(bounds.max_value, value))
        
        return value
    
    def evaluate_and_adjust(
        self,
        metrics: PerformanceMetrics,
        force: bool = False
    ) -> List[ConfigurationChange]:
        """
        Evaluate metrics and apply adjustments based on rules.
        
        Args:
            metrics: Current performance metrics
            force: Force evaluation ignoring cooldowns
            
        Returns:
            List of changes made
        """
        changes = []
        
        with self._lock:
            # Update baseline if first run
            if self.baseline_metrics is None:
                self.baseline_metrics = metrics
            
            # Evaluate each rule
            for rule_name, rule in sorted(
                self.adjustment_rules.items(),
                key=lambda x: x[1].priority,
                reverse=True
            ):
                if not rule.enabled:
                    continue
                
                # Check cooldown
                if not force and rule.last_triggered:
                    elapsed = (datetime.now() - rule.last_triggered).total_seconds()
                    if elapsed < rule.cooldown_seconds:
                        continue
                
                # Check rate limit
                recent_triggers = sum(
                    1 for ts in [h.get("timestamp") for h in rule.adjustment_history[-10:]]
                    if ts and (datetime.now() - datetime.fromisoformat(ts)).total_seconds() < 3600
                )
                if recent_triggers >= rule.max_adjustments_per_hour:
                    logger.debug(f"Rule '{rule_name}' rate limited")
                    continue
                
                # Evaluate trigger condition
                if self._evaluate_rule(rule, metrics):
                    # Apply adjustment
                    change = self._apply_adjustment(rule, metrics)
                    if change and change.success:
                        changes.append(change)
                        
                        # Update rule state
                        rule.last_triggered = datetime.now()
                        rule.trigger_count += 1
                        rule.adjustment_history.append({
                            "timestamp": change.timestamp.isoformat(),
                            "metric_value": change.metric_value,
                            "adjustment": f"{change.old_value} -> {change.new_value}"
                        })
        
        if changes:
            logger.info(f"Applied {len(changes)} configuration changes")
        
        return changes
    
    def _evaluate_rule(self, rule: AdjustmentRule, metrics: PerformanceMetrics) -> bool:
        """Evaluate if rule condition is met."""
        
        # Extract metric value
        metric_value = self._extract_metric_value(rule.trigger_metric, metrics)
        if metric_value is None:
            return False
        
        # Evaluate condition
        operators = {
            "gt": lambda a, b: a > b,
            "lt": lambda a, b: a < b,
            "gte": lambda a, b: a >= b,
            "lte": lambda a, b: a <= b,
            "eq": lambda a, b: abs(a - b) < 0.001
        }
        
        op = operators.get(rule.trigger_operator)
        if not op:
            logger.warning(f"Unknown operator: {rule.trigger_operator}")
            return False
        
        return op(metric_value, rule.trigger_threshold)
    
    def _extract_metric_value(
        self,
        metric_type: MetricType,
        metrics: PerformanceMetrics
    ) -> Optional[float]:
        """Extract metric value from metrics object."""
        
        metric_map = {
            MetricType.SUCCESS_RATE: metrics.success_rate,
            MetricType.LATENCY: metrics.avg_latency_ms,
            MetricType.ERROR_RATE: metrics.error_rate,
            MetricType.MEMORY: metrics.avg_memory_mb,
            MetricType.CPU: metrics.avg_cpu_ms,
            MetricType.COST: metrics.total_cost,
            MetricType.QUALITY: metrics.avg_quality_score,
            MetricType.ACCURACY: metrics.avg_accuracy,
        }
        
        return metric_map.get(metric_type)
    
    def _apply_adjustment(
        self,
        rule: AdjustmentRule,
        metrics: PerformanceMetrics
    ) -> Optional[ConfigurationChange]:
        """Apply adjustment defined by rule."""
        
        param_name = rule.target_parameter
        current_value = self.parameters.get(param_name)
        
        if current_value is None:
            logger.warning(f"Parameter '{param_name}' not found")
            return None
        
        # Calculate new value based on adjustment type
        if rule.adjustment_type == "absolute":
            new_value = rule.adjustment_value
        elif rule.adjustment_type == "relative":
            new_value = current_value + rule.adjustment_value
        elif rule.adjustment_type == "multiply":
            new_value = current_value * rule.adjustment_value
        else:
            logger.warning(f"Unknown adjustment type: {rule.adjustment_type}")
            return None
        
        # Apply strategy modifier
        new_value = self._apply_strategy_modifier(current_value, new_value)
        
        # Set parameter
        metric_value = self._extract_metric_value(rule.trigger_metric, metrics)
        
        success = self.set_parameter(
            name=param_name,
            value=new_value,
            reason=f"Auto-adjustment: {rule.description}",
            rule_name=rule.name
        )
        
        if success:
            change = self.change_history[-1]
            change.triggered_by_metric = rule.trigger_metric.value
            change.metric_value = metric_value
            return change
        
        return None
    
    def _apply_strategy_modifier(self, old_value: float, new_value: float) -> float:
        """Apply strategy-based modifier to adjustment."""
        
        delta = new_value - old_value
        
        if self.strategy == AdjustmentStrategy.CONSERVATIVE:
            # Reduce change by 50%
            return old_value + (delta * 0.5)
        elif self.strategy == AdjustmentStrategy.GRADUAL:
            # Reduce change by 75%
            return old_value + (delta * 0.25)
        elif self.strategy == AdjustmentStrategy.AGGRESSIVE:
            # Increase change by 50%
            return old_value + (delta * 1.5)
        else:  # BALANCED
            return new_value
    
    def check_and_rollback(self, current_metrics: PerformanceMetrics) -> List[str]:
        """
        Check pending rollbacks and execute if performance degraded.
        
        Args:
            current_metrics: Current performance metrics
            
        Returns:
            List of rolled back parameter names
        """
        rolled_back = []
        
        with self._lock:
            if not self.enable_auto_rollback or not self.baseline_metrics:
                return rolled_back
            
            now = datetime.now()
            remaining_rollbacks = []
            
            for change in self.pending_rollbacks:
                if change.rollback_at and now >= change.rollback_at:
                    # Check if performance degraded
                    if self._performance_degraded(current_metrics):
                        # Rollback
                        self.set_parameter(
                            name=change.parameter_name,
                            value=change.old_value,
                            reason=f"Auto-rollback: performance degraded after change"
                        )
                        rolled_back.append(change.parameter_name)
                        logger.warning(f"Rolled back parameter '{change.parameter_name}' "
                                     f"due to performance degradation")
                    else:
                        # Performance improved or stable, update baseline
                        self.baseline_metrics = current_metrics
                else:
                    remaining_rollbacks.append(change)
            
            self.pending_rollbacks = remaining_rollbacks
        
        return rolled_back
    
    def _performance_degraded(self, current: PerformanceMetrics) -> bool:
        """Check if performance degraded compared to baseline."""
        
        if not self.baseline_metrics:
            return False
        
        baseline = self.baseline_metrics
        
        # Check multiple indicators
        degradation_score = 0
        
        # Success rate dropped significantly
        if current.success_rate < baseline.success_rate - 0.05:
            degradation_score += 3
        
        # Latency increased significantly
        if current.avg_latency_ms > baseline.avg_latency_ms * 1.3:
            degradation_score += 2
        
        # Error rate increased
        if current.error_rate > baseline.error_rate + 0.05:
            degradation_score += 2
        
        # Cost increased significantly
        if current.total_cost > baseline.total_cost * 1.5:
            degradation_score += 1
        
        # Quality dropped
        if current.avg_quality_score < baseline.avg_quality_score - 0.1:
            degradation_score += 2
        
        return degradation_score >= 3
    
    def get_configuration_snapshot(self) -> Dict[str, Any]:
        """Get current configuration snapshot."""
        
        with self._lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "strategy": self.strategy.value,
                "parameters": dict(self.parameters),
                "active_rules": {
                    name: {
                        "enabled": rule.enabled,
                        "trigger_count": rule.trigger_count,
                        "last_triggered": rule.last_triggered.isoformat() 
                                        if rule.last_triggered else None
                    }
                    for name, rule in self.adjustment_rules.items()
                },
                "recent_changes": [
                    {
                        "timestamp": change.timestamp.isoformat(),
                        "parameter": change.parameter_name,
                        "old_value": change.old_value,
                        "new_value": change.new_value,
                        "reason": change.reason
                    }
                    for change in list(self.change_history)[-10:]
                ]
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration change statistics."""
        
        with self._lock:
            total_changes = len(self.change_history)
            
            if total_changes == 0:
                return {
                    "total_changes": 0,
                    "changes_by_parameter": {},
                    "changes_by_rule": {},
                    "rollbacks": 0
                }
            
            changes_by_param = {}
            changes_by_rule = {}
            rollback_count = 0
            
            for change in self.change_history:
                # Count by parameter
                param = change.parameter_name
                changes_by_param[param] = changes_by_param.get(param, 0) + 1
                
                # Count by rule
                if change.rule_name:
                    rule = change.rule_name
                    changes_by_rule[rule] = changes_by_rule.get(rule, 0) + 1
                
                # Count rollbacks
                if "rollback" in change.reason.lower():
                    rollback_count += 1
            
            return {
                "total_changes": total_changes,
                "changes_by_parameter": changes_by_param,
                "changes_by_rule": changes_by_rule,
                "rollbacks": rollback_count,
                "avg_changes_per_hour": self._calculate_change_rate()
            }
    
    def _calculate_change_rate(self) -> float:
        """Calculate average changes per hour."""
        
        if len(self.change_history) < 2:
            return 0.0
        
        first_change = list(self.change_history)[0]
        last_change = list(self.change_history)[-1]
        
        duration_hours = (last_change.timestamp - first_change.timestamp).total_seconds() / 3600
        
        if duration_hours == 0:
            return 0.0
        
        return len(self.change_history) / duration_hours
    
    def reset_to_defaults(self):
        """Reset all parameters to default values."""
        
        with self._lock:
            for name, bounds in self.parameter_bounds.items():
                self.set_parameter(
                    name=name,
                    value=bounds.default_value,
                    reason="Reset to defaults"
                )
            
            logger.info("All parameters reset to defaults")


# Singleton instance
_config_manager_instance: Optional[DynamicConfigManager] = None
_config_manager_lock = Lock()


def get_config_manager(
    strategy: AdjustmentStrategy = AdjustmentStrategy.BALANCED
) -> DynamicConfigManager:
    """
    Get or create the global configuration manager instance.
    
    Args:
        strategy: Adjustment strategy (only used on first call)
        
    Returns:
        DynamicConfigManager instance
    """
    global _config_manager_instance
    
    if _config_manager_instance is None:
        with _config_manager_lock:
            if _config_manager_instance is None:
                _config_manager_instance = DynamicConfigManager(strategy=strategy)
    
    return _config_manager_instance

