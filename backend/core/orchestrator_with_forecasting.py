
"""
Orchestrator with Forecasting Integration

Extends the orchestrator with forecasting engine capabilities for:
- Proactive resource management
- Predictive bottleneck prevention
- Autonomous goal-driven optimization
"""

from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from utils.logging import get_logger
from core.orchestrator_with_monitoring import MonitoredOrchestrator
from core.forecasting_engine import ForecastingEngine
from core.proactive_goal_setter import Goal, GoalType, GoalStatus

logger = get_logger(__name__)


class OrchestratorWithForecasting(MonitoredOrchestrator):
    """
    Advanced orchestrator with forecasting and proactive goal setting.
    
    Extends OrchestratorWithMonitoring with:
    - Automatic forecasting of resource needs
    - Pattern-based optimization
    - Proactive goal setting and execution
    - Predictive bottleneck prevention
    """
    
    def __init__(
        self,
        performance_monitor_config: Optional[Dict[str, Any]] = None,
        config_manager_config: Optional[Dict[str, Any]] = None,
        forecasting_config: Optional[Dict[str, Any]] = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, enable_monitoring=True, **kwargs)
        
        # Store configs
        self.performance_monitor_config = performance_monitor_config or {}
        self.config_manager_config = config_manager_config or {}
        self.config_manager = None  # For compatibility
        
        # Initialize forecasting engine
        self.forecasting_engine = ForecastingEngine(forecasting_config)
        self.forecasting_engine.start()
        
        # Register goal action callbacks
        self._register_goal_callbacks()
        
        logger.info("OrchestratorWithForecasting initialized")
    
    def _register_goal_callbacks(self):
        """Register callbacks for automatic goal action execution."""
        goal_setter = self.forecasting_engine.goal_setter
        
        # Resource optimization callback
        def optimize_resources(goal: Goal):
            logger.info(f"Executing resource optimization for goal: {goal.goal_id}")
            # Trigger dynamic config adjustment
            if self.config_manager:
                # Implement resource optimization logic
                pass
        
        # Capacity planning callback
        def plan_capacity(goal: Goal):
            logger.info(f"Executing capacity planning for goal: {goal.goal_id}")
            # Alert administrators, trigger scaling
            pass
        
        # Bottleneck prevention callback
        def prevent_bottleneck(goal: Goal):
            logger.info(f"Executing bottleneck prevention for goal: {goal.goal_id}")
            # Adjust configurations, scale resources
            pass
        
        goal_setter.register_action_callback("optimize_resources", optimize_resources)
        goal_setter.register_action_callback("plan_capacity", plan_capacity)
        goal_setter.register_action_callback("prevent_bottleneck", prevent_bottleneck)
    
    async def execute_with_forecasting(
        self,
        agent_name: str,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute agent with forecasting-driven optimization.
        
        Args:
            agent_name: Name of agent to execute
            task_description: Description of the task
            context: Additional context
        
        Returns:
            Execution result with forecasting metadata
        """
        # Record event for pattern recognition
        self.forecasting_engine.add_event(
            f"agent_execution_{agent_name}",
            datetime.now(),
            {"task": task_description}
        )
        
        # Execute with monitoring (adapter for parent class 'run' method)
        try:
            run_result = self.run(
                task=task_description,
                project_id=context.get("project_id", "default") if context else "default",
                execution_strategy=context.get("strategy", "sequential") if context else "sequential"
            )
            result = {
                "status": "success",
                "result": run_result,
                "metrics": {}
            }
        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            result = {
                "status": "error",
                "error": str(e),
                "metrics": {}
            }
        
        # Add forecasting metrics
        if "metrics" in result:
            for metric_name, value in result["metrics"].items():
                self.forecasting_engine.add_metric_data(metric_name, value)
        
        # Check and execute relevant goals
        await self._check_and_execute_goals(agent_name, result)
        
        # Add forecasting info to result
        result["forecasting"] = {
            "active_goals": len(self.forecasting_engine.get_active_goals()),
            "detected_patterns": len(self.forecasting_engine.get_patterns())
        }
        
        return result
    
    async def _check_and_execute_goals(self, agent_name: str, execution_result: Dict[str, Any]):
        """Check if any goals are relevant to this execution and take action."""
        active_goals = self.forecasting_engine.get_active_goals()
        
        for goal in active_goals:
            # Check if goal is related to this agent
            if agent_name in goal.description or goal.target_metric in execution_result.get("metrics", {}):
                # Update goal progress based on execution result
                if goal.target_metric in execution_result.get("metrics", {}):
                    current_value = execution_result["metrics"][goal.target_metric]
                    
                    # Calculate progress
                    if goal.target_value != goal.current_value:
                        progress = abs(current_value - goal.current_value) / abs(goal.target_value - goal.current_value)
                        progress = min(1.0, max(0.0, progress))
                        
                        self.forecasting_engine.update_goal_progress(
                            goal.goal_id,
                            progress,
                            current_value
                        )
    
    def get_forecasting_report(self) -> Dict[str, Any]:
        """Get comprehensive forecasting report."""
        # Get current metrics from performance monitor
        current_metrics = {}
        if self.performance_monitor:
            perf_data = self.performance_monitor.get_performance_data()
            if "current_metrics" in perf_data:
                current_metrics = perf_data["current_metrics"]
        
        return self.forecasting_engine.get_comprehensive_report(current_metrics)
    
    def predict_future_state(self, horizon_hours: int = 24) -> Dict[str, Any]:
        """Predict future system state."""
        current_metrics = {}
        if self.performance_monitor:
            perf_data = self.performance_monitor.get_performance_data()
            if "current_metrics" in perf_data:
                current_metrics = perf_data["current_metrics"]
        
        prediction = self.forecasting_engine.predict_system_state(
            current_metrics,
            horizon_hours
        )
        
        return prediction.to_dict()
    
    def trigger_proactive_analysis(self) -> Dict[str, Any]:
        """Manually trigger proactive analysis and goal setting."""
        current_metrics = {}
        if self.performance_monitor:
            perf_data = self.performance_monitor.get_performance_data()
            if "current_metrics" in perf_data:
                current_metrics = perf_data["current_metrics"]
        
        goals = self.forecasting_engine.analyze_and_set_goals(current_metrics)
        
        return {
            "status": "success",
            "goals_set": len(goals),
            "goals": [g.to_dict() for g in goals]
        }
    
    def shutdown(self):
        """Shutdown orchestrator and all components."""
        logger.info("Shutting down orchestrator with forecasting...")
        
        if self.forecasting_engine:
            self.forecasting_engine.stop()
        
        # Call parent shutdown
        super().shutdown()
        
        logger.info("Orchestrator shutdown complete")
