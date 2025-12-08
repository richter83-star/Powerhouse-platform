
"""
Autonomous Goal Executor

Autonomously executes and pursues goals set by the proactive goal setter.

Key Features:
- Autonomous action planning and execution
- Priority-based goal scheduling
- Adaptive execution strategies
- Continuous monitoring and adjustment
- Learning from goal outcomes
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from threading import Thread, Lock
import time

from utils.logging import get_logger
from core.proactive_goal_setter import Goal, GoalType, GoalStatus, GoalPriority

logger = get_logger(__name__)


class ExecutionStrategy(str, Enum):
    """Strategies for goal execution."""
    IMMEDIATE = "immediate"  # Execute immediately
    SCHEDULED = "scheduled"  # Schedule for optimal time
    ADAPTIVE = "adaptive"  # Adapt based on system state
    COLLABORATIVE = "collaborative"  # Coordinate with other goals


@dataclass
class ExecutionPlan:
    """Plan for executing a goal."""
    goal_id: str
    strategy: ExecutionStrategy
    scheduled_time: datetime
    estimated_duration: timedelta
    resource_requirements: Dict[str, float]
    dependencies: List[str]
    actions: List[Dict[str, Any]]
    priority_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "strategy": self.strategy,
            "scheduled_time": self.scheduled_time.isoformat(),
            "estimated_duration": str(self.estimated_duration),
            "resource_requirements": self.resource_requirements,
            "dependencies": self.dependencies,
            "actions": self.actions,
            "priority_score": self.priority_score
        }


@dataclass
class ExecutionResult:
    """Result of goal execution."""
    goal_id: str
    success: bool
    actions_completed: List[str]
    actions_failed: List[str]
    impact: Dict[str, float]
    execution_time: timedelta
    lessons_learned: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "success": self.success,
            "actions_completed": self.actions_completed,
            "actions_failed": self.actions_failed,
            "impact": self.impact,
            "execution_time": str(self.execution_time),
            "lessons_learned": self.lessons_learned
        }


class AutonomousGoalExecutor:
    """
    Autonomously executes goals and learns from outcomes.
    
    Features:
    - Continuous goal monitoring
    - Intelligent action scheduling
    - Adaptive execution strategies
    - Impact measurement
    - Learning from outcomes
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.lock = Lock()
        
        # Configuration
        self.execution_interval_seconds = self.config.get("execution_interval_seconds", 60)
        self.max_concurrent_goals = self.config.get("max_concurrent_goals", 3)
        self.enable_learning = self.config.get("enable_learning", True)
        
        # State
        self.execution_plans: Dict[str, ExecutionPlan] = {}
        self.execution_history: List[ExecutionResult] = []
        self.active_executions: Dict[str, asyncio.Task] = {}
        
        # Action registry
        self.action_handlers: Dict[str, Callable] = {}
        
        # Background execution
        self.running = False
        self.execution_thread: Optional[Thread] = None
        
        # Statistics
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_actions_executed": 0,
            "average_execution_time": 0.0,
            "last_execution_time": None
        }
        
        # Learning database
        self.action_success_rates: Dict[str, List[bool]] = {}
        self.goal_type_strategies: Dict[GoalType, ExecutionStrategy] = {}
        
        logger.info("AutonomousGoalExecutor initialized")
    
    def register_action_handler(self, action_name: str, handler: Callable):
        """Register a handler function for a specific action type."""
        self.action_handlers[action_name] = handler
        logger.info(f"Registered action handler: {action_name}")
    
    def start(self):
        """Start autonomous goal execution loop."""
        if self.running:
            logger.warning("AutonomousGoalExecutor already running")
            return
        
        self.running = True
        self.execution_thread = Thread(target=self._execution_loop, daemon=True)
        self.execution_thread.start()
        logger.info("AutonomousGoalExecutor started")
    
    def stop(self):
        """Stop autonomous goal execution."""
        self.running = False
        if self.execution_thread:
            self.execution_thread.join(timeout=10)
        logger.info("AutonomousGoalExecutor stopped")
    
    def _execution_loop(self):
        """Main execution loop running in background thread."""
        while self.running:
            try:
                # Execute goals asynchronously
                asyncio.run(self._execute_pending_goals())
                time.sleep(self.execution_interval_seconds)
            except Exception as e:
                logger.error(f"Error in execution loop: {e}", exc_info=True)
                time.sleep(10)  # Wait before retrying
    
    async def _execute_pending_goals(self):
        """Execute pending goals based on priority and schedule."""
        with self.lock:
            # Get executable plans
            now = datetime.now()
            executable_plans = [
                plan for plan in self.execution_plans.values()
                if plan.scheduled_time <= now and plan.goal_id not in self.active_executions
            ]
            
            # Sort by priority
            executable_plans.sort(key=lambda p: p.priority_score, reverse=True)
        
        # Execute top priority goals (respecting concurrency limit)
        available_slots = self.max_concurrent_goals - len(self.active_executions)
        for plan in executable_plans[:available_slots]:
            task = asyncio.create_task(self._execute_goal(plan))
            self.active_executions[plan.goal_id] = task
    
    async def _execute_goal(self, plan: ExecutionPlan) -> ExecutionResult:
        """Execute a specific goal according to its plan."""
        goal_id = plan.goal_id
        start_time = datetime.now()
        
        logger.info(f"Executing goal: {goal_id} with strategy {plan.strategy}")
        
        actions_completed = []
        actions_failed = []
        impact = {}
        lessons = []
        
        try:
            for action in plan.actions:
                action_name = action.get("name", "unknown")
                action_params = action.get("params", {})
                
                try:
                    # Execute action
                    result = await self._execute_action(action_name, action_params, goal_id)
                    
                    if result.get("success", False):
                        actions_completed.append(action_name)
                        self._record_action_success(action_name, True)
                        
                        # Collect impact metrics
                        if "impact" in result:
                            impact.update(result["impact"])
                        
                        logger.info(f"Action completed: {action_name} for goal {goal_id}")
                    else:
                        actions_failed.append(action_name)
                        self._record_action_success(action_name, False)
                        lesson = f"Action {action_name} failed: {result.get('error', 'unknown')}"
                        lessons.append(lesson)
                        logger.warning(lesson)
                    
                    # Small delay between actions
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    actions_failed.append(action_name)
                    self._record_action_success(action_name, False)
                    lesson = f"Action {action_name} error: {str(e)}"
                    lessons.append(lesson)
                    logger.error(lesson, exc_info=True)
            
            # Determine overall success
            success = len(actions_completed) > 0 and len(actions_failed) == 0
            
            # Create execution result
            execution_time = datetime.now() - start_time
            result = ExecutionResult(
                goal_id=goal_id,
                success=success,
                actions_completed=actions_completed,
                actions_failed=actions_failed,
                impact=impact,
                execution_time=execution_time,
                lessons_learned=lessons
            )
            
            # Update statistics
            with self.lock:
                self.stats["total_executions"] += 1
                if success:
                    self.stats["successful_executions"] += 1
                else:
                    self.stats["failed_executions"] += 1
                self.stats["total_actions_executed"] += len(actions_completed)
                self.stats["last_execution_time"] = datetime.now().isoformat()
                
                # Update average execution time
                current_avg = self.stats["average_execution_time"]
                total_execs = self.stats["total_executions"]
                self.stats["average_execution_time"] = (
                    (current_avg * (total_execs - 1) + execution_time.total_seconds()) / total_execs
                )
                
                # Store result
                self.execution_history.append(result)
                
                # Remove from active executions
                if goal_id in self.active_executions:
                    del self.active_executions[goal_id]
                
                # Remove execution plan
                if goal_id in self.execution_plans:
                    del self.execution_plans[goal_id]
            
            logger.info(f"Goal execution completed: {goal_id} - Success: {success}")
            return result
            
        except Exception as e:
            logger.error(f"Fatal error executing goal {goal_id}: {e}", exc_info=True)
            
            # Clean up
            with self.lock:
                if goal_id in self.active_executions:
                    del self.active_executions[goal_id]
                if goal_id in self.execution_plans:
                    del self.execution_plans[goal_id]
            
            raise
    
    async def _execute_action(
        self,
        action_name: str,
        params: Dict[str, Any],
        goal_id: str
    ) -> Dict[str, Any]:
        """Execute a single action."""
        # Check if we have a registered handler
        if action_name in self.action_handlers:
            try:
                handler = self.action_handlers[action_name]
                result = handler(params, goal_id)
                
                # If result is a coroutine, await it
                if asyncio.iscoroutine(result):
                    result = await result
                
                return result if isinstance(result, dict) else {"success": True, "result": result}
            except Exception as e:
                logger.error(f"Handler error for {action_name}: {e}", exc_info=True)
                return {"success": False, "error": str(e)}
        else:
            # No handler - simulate execution
            logger.info(f"Simulating action: {action_name} (no handler registered)")
            await asyncio.sleep(0.5)  # Simulate work
            return {
                "success": True,
                "simulated": True,
                "action": action_name,
                "params": params
            }
    
    def _record_action_success(self, action_name: str, success: bool):
        """Record action success/failure for learning."""
        if not self.enable_learning:
            return
        
        if action_name not in self.action_success_rates:
            self.action_success_rates[action_name] = []
        
        self.action_success_rates[action_name].append(success)
        
        # Keep only last 100 results
        if len(self.action_success_rates[action_name]) > 100:
            self.action_success_rates[action_name] = self.action_success_rates[action_name][-100:]
    
    def create_execution_plan(
        self,
        goal: Goal,
        strategy: Optional[ExecutionStrategy] = None
    ) -> ExecutionPlan:
        """
        Create an execution plan for a goal.
        
        Args:
            goal: Goal to create plan for
            strategy: Execution strategy (auto-selected if None)
        
        Returns:
            ExecutionPlan
        """
        # Auto-select strategy if not provided
        if strategy is None:
            strategy = self._select_optimal_strategy(goal)
        
        # Calculate priority score
        priority_score = self._calculate_priority_score(goal)
        
        # Determine scheduled time
        scheduled_time = self._determine_schedule_time(goal, strategy)
        
        # Estimate duration
        estimated_duration = self._estimate_duration(goal)
        
        # Extract resource requirements
        resource_requirements = goal.metadata.get("resource_requirements", {})
        
        # Convert goal actions to execution actions
        actions = []
        for action_str in goal.actions:
            actions.append({
                "name": action_str,
                "params": {
                    "goal_id": goal.goal_id,
                    "goal_type": goal.goal_type,
                    "target_metric": goal.target_metric,
                    "target_value": goal.target_value
                }
            })
        
        plan = ExecutionPlan(
            goal_id=goal.goal_id,
            strategy=strategy,
            scheduled_time=scheduled_time,
            estimated_duration=estimated_duration,
            resource_requirements=resource_requirements,
            dependencies=goal.dependencies,
            actions=actions,
            priority_score=priority_score
        )
        
        with self.lock:
            self.execution_plans[goal.goal_id] = plan
        
        logger.info(
            f"Created execution plan for goal {goal.goal_id} "
            f"(strategy: {strategy}, priority: {priority_score:.2f})"
        )
        
        return plan
    
    def _select_optimal_strategy(self, goal: Goal) -> ExecutionStrategy:
        """Select optimal execution strategy for a goal."""
        # Use learned strategy if available
        if goal.goal_type in self.goal_type_strategies:
            return self.goal_type_strategies[goal.goal_type]
        
        # Default strategy based on goal type and priority
        if goal.priority == GoalPriority.CRITICAL:
            return ExecutionStrategy.IMMEDIATE
        elif goal.goal_type == GoalType.CAPACITY_PLANNING:
            return ExecutionStrategy.SCHEDULED
        elif goal.goal_type == GoalType.PATTERN_ADAPTATION:
            return ExecutionStrategy.ADAPTIVE
        else:
            return ExecutionStrategy.ADAPTIVE
    
    def _calculate_priority_score(self, goal: Goal) -> float:
        """Calculate numeric priority score for a goal."""
        # Base score from priority
        priority_scores = {
            GoalPriority.CRITICAL: 100.0,
            GoalPriority.HIGH: 75.0,
            GoalPriority.MEDIUM: 50.0,
            GoalPriority.LOW: 25.0
        }
        score = priority_scores.get(goal.priority, 50.0)
        
        # Adjust based on deadline urgency
        time_to_deadline = (goal.deadline - datetime.now()).total_seconds()
        if time_to_deadline < 3600:  # Less than 1 hour
            score += 25.0
        elif time_to_deadline < 86400:  # Less than 1 day
            score += 15.0
        
        # Adjust based on progress (lower progress = higher priority)
        score += (1.0 - goal.progress) * 10.0
        
        return min(150.0, score)  # Cap at 150
    
    def _determine_schedule_time(self, goal: Goal, strategy: ExecutionStrategy) -> datetime:
        """Determine when to schedule goal execution."""
        if strategy == ExecutionStrategy.IMMEDIATE:
            return datetime.now()
        elif strategy == ExecutionStrategy.SCHEDULED:
            # Schedule for optimal time (e.g., during low-load periods)
            # For now, schedule 5 minutes in the future
            return datetime.now() + timedelta(minutes=5)
        else:  # ADAPTIVE or COLLABORATIVE
            # Adaptive scheduling based on system state
            return datetime.now() + timedelta(minutes=2)
    
    def _estimate_duration(self, goal: Goal) -> timedelta:
        """Estimate how long goal execution will take."""
        # Base estimate on number of actions
        num_actions = len(goal.actions)
        base_minutes = num_actions * 2  # 2 minutes per action
        
        # Adjust based on goal type
        if goal.goal_type == GoalType.CAPACITY_PLANNING:
            base_minutes *= 2  # Capacity planning takes longer
        elif goal.goal_type == GoalType.PERFORMANCE_TARGET:
            base_minutes *= 1.5
        
        return timedelta(minutes=base_minutes)
    
    def schedule_goal(self, goal: Goal, strategy: Optional[ExecutionStrategy] = None):
        """Schedule a goal for autonomous execution."""
        plan = self.create_execution_plan(goal, strategy)
        logger.info(f"Scheduled goal {goal.goal_id} for execution at {plan.scheduled_time}")
    
    def get_execution_status(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status for a goal."""
        with self.lock:
            if goal_id in self.active_executions:
                return {
                    "status": "executing",
                    "goal_id": goal_id
                }
            elif goal_id in self.execution_plans:
                plan = self.execution_plans[goal_id]
                return {
                    "status": "scheduled",
                    "goal_id": goal_id,
                    "scheduled_time": plan.scheduled_time.isoformat(),
                    "strategy": plan.strategy
                }
            else:
                # Check history
                for result in reversed(self.execution_history):
                    if result.goal_id == goal_id:
                        return {
                            "status": "completed",
                            "goal_id": goal_id,
                            "success": result.success,
                            "execution_time": str(result.execution_time)
                        }
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get executor statistics."""
        with self.lock:
            stats = self.stats.copy()
            stats["active_executions"] = len(self.active_executions)
            stats["scheduled_plans"] = len(self.execution_plans)
            stats["success_rate"] = (
                self.stats["successful_executions"] / self.stats["total_executions"]
                if self.stats["total_executions"] > 0 else 0.0
            )
            
            # Add action success rates
            action_rates = {}
            for action, results in self.action_success_rates.items():
                if results:
                    action_rates[action] = sum(results) / len(results)
            stats["action_success_rates"] = action_rates
        
        return stats
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning system."""
        if not self.enable_learning:
            return {"enabled": False}
        
        with self.lock:
            insights = {
                "enabled": True,
                "action_success_rates": {},
                "best_strategies": {},
                "common_failures": []
            }
            
            # Calculate action success rates
            for action, results in self.action_success_rates.items():
                if results:
                    success_rate = sum(results) / len(results)
                    insights["action_success_rates"][action] = {
                        "rate": success_rate,
                        "samples": len(results)
                    }
            
            # Best strategies per goal type
            insights["best_strategies"] = {
                gt.value: strategy.value
                for gt, strategy in self.goal_type_strategies.items()
            }
            
            # Analyze common failures
            recent_failures = [
                r for r in self.execution_history[-50:]
                if not r.success
            ]
            
            if recent_failures:
                # Count failed action types
                failed_actions = {}
                for result in recent_failures:
                    for action in result.actions_failed:
                        failed_actions[action] = failed_actions.get(action, 0) + 1
                
                # Sort by frequency
                sorted_failures = sorted(
                    failed_actions.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                insights["common_failures"] = [
                    {"action": action, "count": count}
                    for action, count in sorted_failures[:5]
                ]
        
        return insights
    
    def to_dict(self) -> Dict[str, Any]:
        """Export executor state."""
        with self.lock:
            return {
                "statistics": self.get_statistics(),
                "scheduled_plans": [p.to_dict() for p in self.execution_plans.values()],
                "recent_executions": [r.to_dict() for r in self.execution_history[-20:]],
                "learning_insights": self.get_learning_insights(),
                "running": self.running
            }

