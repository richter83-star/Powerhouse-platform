
"""
Proactive Goal Setter

Autonomously sets system goals based on:
- Forecasted metrics
- Detected patterns
- Predicted system states
- Historical performance

Goals are set to:
- Prevent bottlenecks before they occur
- Optimize resource utilization
- Maintain performance SLAs
- Adapt to predicted workload changes
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid

from utils.logging import get_logger
from core.predictive_state_model import (
    PredictiveStateModel, SystemStatePrediction, SystemState, ResourceType
)
from core.pattern_recognizer import PatternRecognizer, Pattern, PatternType

logger = get_logger(__name__)


class GoalType(str, Enum):
    """Types of goals that can be set."""
    RESOURCE_OPTIMIZATION = "resource_optimization"
    PERFORMANCE_TARGET = "performance_target"
    CAPACITY_PLANNING = "capacity_planning"
    BOTTLENECK_PREVENTION = "bottleneck_prevention"
    COST_REDUCTION = "cost_reduction"
    SLA_MAINTENANCE = "sla_maintenance"
    PATTERN_ADAPTATION = "pattern_adaptation"


class GoalPriority(str, Enum):
    """Priority levels for goals."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GoalStatus(str, Enum):
    """Status of a goal."""
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Goal:
    """Represents a system goal."""
    goal_id: str
    goal_type: GoalType
    priority: GoalPriority
    description: str
    target_metric: str
    current_value: float
    target_value: float
    deadline: datetime
    status: GoalStatus = GoalStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    actions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "goal_type": self.goal_type,
            "priority": self.priority,
            "description": self.description,
            "target_metric": self.target_metric,
            "current_value": self.current_value,
            "target_value": self.target_value,
            "deadline": self.deadline.isoformat(),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "actions": self.actions,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "progress": self.progress
        }


@dataclass
class GoalAchievementReport:
    """Report on goal achievement."""
    goal_id: str
    achieved: bool
    achievement_time: datetime
    final_value: float
    target_value: float
    actions_taken: List[str]
    time_to_achieve: timedelta
    notes: str


class ProactiveGoalSetter:
    """
    Main proactive goal setting engine.
    
    Analyzes predictions and patterns to autonomously set system goals.
    """
    
    def __init__(
        self,
        predictive_model: PredictiveStateModel,
        pattern_recognizer: PatternRecognizer,
        config: Optional[Dict[str, Any]] = None
    ):
        self.predictive_model = predictive_model
        self.pattern_recognizer = pattern_recognizer
        self.config = config or {}
        
        self.goals: Dict[str, Goal] = {}  # goal_id -> Goal
        self.goal_history: List[GoalAchievementReport] = []
        
        # Configuration
        self.auto_goal_setting = self.config.get("auto_goal_setting", True)
        self.goal_review_interval = self.config.get("goal_review_interval_hours", 6)
        self.max_active_goals = self.config.get("max_active_goals", 10)
        
        # Callbacks for goal actions
        self.action_callbacks: Dict[str, Callable] = {}
        
        logger.info("ProactiveGoalSetter initialized")
    
    def register_action_callback(self, action_name: str, callback: Callable):
        """Register a callback function for a specific action."""
        self.action_callbacks[action_name] = callback
        logger.info(f"Registered action callback: {action_name}")
    
    def analyze_and_set_goals(
        self,
        current_metrics: Optional[Dict[str, float]] = None,
        horizon_hours: int = 24
    ) -> List[Goal]:
        """
        Analyze system predictions and set proactive goals.
        
        Args:
            current_metrics: Current system metrics
            horizon_hours: Prediction horizon
        
        Returns:
            List of newly created goals
        """
        if not self.auto_goal_setting:
            logger.info("Auto goal setting is disabled")
            return []
        
        # Get system state prediction
        prediction = self.predictive_model.predict_system_state(
            horizon_hours=horizon_hours,
            current_metrics=current_metrics
        )
        
        # Get detected patterns
        patterns = self.pattern_recognizer.get_all_patterns()
        
        new_goals = []
        
        # Set goals based on prediction
        new_goals.extend(self._set_goals_from_prediction(prediction))
        
        # Set goals based on patterns
        new_goals.extend(self._set_goals_from_patterns(patterns))
        
        # Set general optimization goals
        new_goals.extend(self._set_optimization_goals(current_metrics))
        
        # Add goals to tracking
        for goal in new_goals:
            self.goals[goal.goal_id] = goal
        
        # Clean up if too many active goals
        self._prioritize_goals()
        
        logger.info(f"Set {len(new_goals)} new goals")
        return new_goals
    
    def _set_goals_from_prediction(self, prediction: SystemStatePrediction) -> List[Goal]:
        """Set goals based on system state prediction."""
        goals = []
        
        # If system will be degraded or worse, set prevention goals
        if prediction.predicted_state in [SystemState.DEGRADED, SystemState.CRITICAL, SystemState.OVERLOADED]:
            for bottleneck in prediction.predicted_bottlenecks:
                goal = Goal(
                    goal_id=str(uuid.uuid4()),
                    goal_type=GoalType.BOTTLENECK_PREVENTION,
                    priority=GoalPriority.CRITICAL if bottleneck.severity == "critical" else GoalPriority.HIGH,
                    description=f"Prevent bottleneck: {bottleneck.description}",
                    target_metric=bottleneck.location,
                    current_value=0.0,  # Will be updated
                    target_value=80.0,  # Target 80% utilization
                    deadline=bottleneck.predicted_time - timedelta(hours=2),  # Before predicted time
                    actions=bottleneck.mitigation_suggestions,
                    metadata={
                        "bottleneck_id": bottleneck.bottleneck_id,
                        "severity": bottleneck.severity,
                        "prediction_confidence": bottleneck.confidence
                    }
                )
                goals.append(goal)
                logger.info(f"Created bottleneck prevention goal: {goal.description}")
        
        # Set resource optimization goals for high utilization resources
        for demand in prediction.resource_demands:
            if demand.utilization_percent > 75:
                goal = Goal(
                    goal_id=str(uuid.uuid4()),
                    goal_type=GoalType.RESOURCE_OPTIMIZATION,
                    priority=GoalPriority.HIGH if demand.utilization_percent > 85 else GoalPriority.MEDIUM,
                    description=f"Optimize {demand.resource_type.value} usage",
                    target_metric=demand.resource_type.value,
                    current_value=demand.current_usage,
                    target_value=demand.capacity * 0.7,  # Target 70% utilization
                    deadline=datetime.now() + timedelta(hours=12),
                    actions=[
                        f"Analyze {demand.resource_type.value} usage patterns",
                        "Implement optimization strategies",
                        "Monitor impact of optimizations"
                    ],
                    metadata={
                        "predicted_utilization": demand.utilization_percent,
                        "capacity": demand.capacity
                    }
                )
                goals.append(goal)
                logger.info(f"Created resource optimization goal: {goal.description}")
        
        # Capacity planning goals if resources will exceed capacity
        exceeded_resources = [d for d in prediction.resource_demands if d.will_exceed_capacity]
        if exceeded_resources:
            for demand in exceeded_resources:
                goal = Goal(
                    goal_id=str(uuid.uuid4()),
                    goal_type=GoalType.CAPACITY_PLANNING,
                    priority=GoalPriority.CRITICAL,
                    description=f"Increase capacity for {demand.resource_type.value}",
                    target_metric=f"{demand.resource_type.value}_capacity",
                    current_value=demand.capacity,
                    target_value=demand.predicted_usage * 1.2,  # 20% buffer
                    deadline=demand.time_to_capacity or timedelta(hours=24),
                    actions=[
                        "Review current capacity limits",
                        "Plan capacity increase",
                        "Implement scaling strategy",
                        "Validate new capacity"
                    ],
                    metadata={
                        "will_exceed_at": demand.prediction_time.isoformat(),
                        "predicted_usage": demand.predicted_usage
                    }
                )
                goals.append(goal)
                logger.info(f"Created capacity planning goal: {goal.description}")
        
        return goals
    
    def _set_goals_from_patterns(self, patterns: List[Pattern]) -> List[Goal]:
        """Set goals based on detected patterns."""
        goals = []
        
        # Find recurring tasks that can be optimized
        recurring_tasks = [p for p in patterns if p.pattern_type == PatternType.RECURRING_TASK]
        for pattern in recurring_tasks[:3]:  # Limit to top 3
            goal = Goal(
                goal_id=str(uuid.uuid4()),
                goal_type=GoalType.PATTERN_ADAPTATION,
                priority=GoalPriority.MEDIUM,
                description=f"Optimize recurring pattern: {pattern.description}",
                target_metric="task_efficiency",
                current_value=1.0,
                target_value=1.2,  # 20% improvement
                deadline=datetime.now() + timedelta(days=7),
                actions=[
                    "Analyze task execution patterns",
                    "Identify optimization opportunities",
                    "Implement caching or pre-computation",
                    "Measure improvement"
                ],
                metadata={
                    "pattern_id": pattern.pattern_id,
                    "frequency": pattern.frequency,
                    "occurrences": pattern.occurrences
                }
            )
            goals.append(goal)
            logger.info(f"Created pattern adaptation goal: {goal.description}")
        
        # Prepare for periodic spikes
        spike_patterns = [p for p in patterns if p.pattern_type == PatternType.PERIODIC_SPIKE]
        for pattern in spike_patterns:
            spike_hours = pattern.metadata.get("spike_hours", [])
            if spike_hours:
                goal = Goal(
                    goal_id=str(uuid.uuid4()),
                    goal_type=GoalType.CAPACITY_PLANNING,
                    priority=GoalPriority.HIGH,
                    description=f"Prepare for activity spikes at hours: {spike_hours}",
                    target_metric="spike_readiness",
                    current_value=0.0,
                    target_value=1.0,
                    deadline=datetime.now() + timedelta(hours=24),
                    actions=[
                        "Pre-scale resources before spike hours",
                        "Enable request queuing",
                        "Pre-warm caches",
                        "Monitor spike performance"
                    ],
                    metadata={
                        "spike_hours": spike_hours,
                        "pattern_id": pattern.pattern_id
                    }
                )
                goals.append(goal)
                logger.info(f"Created spike preparation goal: {goal.description}")
        
        return goals
    
    def _set_optimization_goals(self, current_metrics: Optional[Dict[str, float]]) -> List[Goal]:
        """Set general optimization goals."""
        goals = []
        
        # Cost reduction goal
        if current_metrics and "cost" in current_metrics:
            current_cost = current_metrics["cost"]
            goal = Goal(
                goal_id=str(uuid.uuid4()),
                goal_type=GoalType.COST_REDUCTION,
                priority=GoalPriority.MEDIUM,
                description="Reduce operational costs by 10%",
                target_metric="cost",
                current_value=current_cost,
                target_value=current_cost * 0.9,
                deadline=datetime.now() + timedelta(days=30),
                actions=[
                    "Audit resource usage",
                    "Implement cost-saving measures",
                    "Optimize API usage",
                    "Review and adjust budgets"
                ],
                metadata={"target_reduction_percent": 10}
            )
            goals.append(goal)
        
        # Performance target goal
        if current_metrics and "latency" in current_metrics:
            current_latency = current_metrics["latency"]
            goal = Goal(
                goal_id=str(uuid.uuid4()),
                goal_type=GoalType.PERFORMANCE_TARGET,
                priority=GoalPriority.HIGH,
                description="Maintain low latency < 200ms",
                target_metric="latency",
                current_value=current_latency,
                target_value=200.0,  # ms
                deadline=datetime.now() + timedelta(days=7),
                actions=[
                    "Profile slow operations",
                    "Implement caching strategies",
                    "Optimize database queries",
                    "Monitor latency continuously"
                ],
                metadata={"target_latency_ms": 200}
            )
            goals.append(goal)
        
        return goals
    
    def _prioritize_goals(self):
        """Prioritize and limit active goals."""
        active_goals = [g for g in self.goals.values() if g.status == GoalStatus.ACTIVE]
        
        if len(active_goals) <= self.max_active_goals:
            return
        
        # Sort by priority and creation time
        priority_order = {
            GoalPriority.CRITICAL: 0,
            GoalPriority.HIGH: 1,
            GoalPriority.MEDIUM: 2,
            GoalPriority.LOW: 3
        }
        
        sorted_goals = sorted(
            active_goals,
            key=lambda g: (priority_order[g.priority], g.created_at)
        )
        
        # Keep top goals, cancel others
        for goal in sorted_goals[self.max_active_goals:]:
            goal.status = GoalStatus.CANCELLED
            logger.info(f"Cancelled low-priority goal: {goal.goal_id}")
    
    def update_goal_progress(self, goal_id: str, progress: float, current_value: Optional[float] = None):
        """Update progress on a goal."""
        goal = self.goals.get(goal_id)
        if not goal:
            logger.warning(f"Goal not found: {goal_id}")
            return
        
        goal.progress = max(0.0, min(1.0, progress))
        if current_value is not None:
            goal.current_value = current_value
        
        # Check if goal is achieved
        if progress >= 1.0:
            self._mark_goal_achieved(goal)
        
        logger.info(f"Updated goal {goal_id} progress: {progress:.2%}")
    
    def _mark_goal_achieved(self, goal: Goal):
        """Mark a goal as achieved."""
        goal.status = GoalStatus.ACHIEVED
        
        report = GoalAchievementReport(
            goal_id=goal.goal_id,
            achieved=True,
            achievement_time=datetime.now(),
            final_value=goal.current_value,
            target_value=goal.target_value,
            actions_taken=goal.actions,
            time_to_achieve=datetime.now() - goal.created_at,
            notes=f"Goal achieved: {goal.description}"
        )
        
        self.goal_history.append(report)
        logger.info(f"Goal achieved: {goal.goal_id} - {goal.description}")
    
    def execute_goal_actions(self, goal_id: str) -> List[str]:
        """Execute actions for a goal."""
        goal = self.goals.get(goal_id)
        if not goal:
            logger.warning(f"Goal not found: {goal_id}")
            return []
        
        goal.status = GoalStatus.IN_PROGRESS
        executed_actions = []
        
        for action in goal.actions:
            # Check if callback exists
            if action in self.action_callbacks:
                try:
                    self.action_callbacks[action](goal)
                    executed_actions.append(action)
                    logger.info(f"Executed action: {action} for goal {goal_id}")
                except Exception as e:
                    logger.error(f"Failed to execute action {action}: {e}")
            else:
                logger.debug(f"No callback for action: {action}")
        
        return executed_actions
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a specific goal."""
        return self.goals.get(goal_id)
    
    def get_active_goals(self) -> List[Goal]:
        """Get all active goals."""
        return [g for g in self.goals.values() if g.status in [GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS]]
    
    def get_goals_by_type(self, goal_type: GoalType) -> List[Goal]:
        """Get goals of a specific type."""
        return [g for g in self.goals.values() if g.goal_type == goal_type]
    
    def get_goals_by_priority(self, priority: GoalPriority) -> List[Goal]:
        """Get goals of a specific priority."""
        return [g for g in self.goals.values() if g.priority == priority]
    
    def get_achievement_report(self) -> Dict[str, Any]:
        """Get goal achievement report."""
        total_goals = len(self.goals)
        achieved_goals = len([g for g in self.goals.values() if g.status == GoalStatus.ACHIEVED])
        active_goals = len([g for g in self.goals.values() if g.status == GoalStatus.ACTIVE])
        
        return {
            "total_goals": total_goals,
            "achieved_goals": achieved_goals,
            "active_goals": active_goals,
            "achievement_rate": achieved_goals / total_goals if total_goals > 0 else 0.0,
            "recent_achievements": [r.__dict__ for r in self.goal_history[-10:]]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export goal setter state."""
        return {
            "active_goals": [g.to_dict() for g in self.get_active_goals()],
            "total_goals": len(self.goals),
            "achievement_report": self.get_achievement_report(),
            "config": self.config
        }
