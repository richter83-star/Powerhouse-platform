
"""
Goal-Driven Autonomous Agent

Main agent that:
1. Monitors system state via forecasting
2. Autonomously sets goals based on predictions
3. Plans and executes actions to achieve goals
4. Learns from outcomes and adapts

This is the top-level integration of all autonomous behavior components.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from threading import Thread, Lock
import time
import asyncio

from utils.logging import get_logger
from core.forecasting_engine import ForecastingEngine
from core.autonomous_goal_executor import AutonomousGoalExecutor, ExecutionStrategy
from core.proactive_goal_setter import Goal, GoalType, GoalStatus, GoalPriority

logger = get_logger(__name__)


class GoalDrivenAgent:
    """
    Fully autonomous goal-driven agent.
    
    Continuously:
    - Predicts future states
    - Sets proactive goals
    - Plans action sequences
    - Executes plans autonomously
    - Learns and adapts
    
    Operates without external commands.
    """
    
    def __init__(
        self,
        forecasting_config: Optional[Dict[str, Any]] = None,
        executor_config: Optional[Dict[str, Any]] = None,
        agent_config: Optional[Dict[str, Any]] = None
    ):
        self.config = agent_config or {}
        self.lock = Lock()
        
        # Initialize forecasting engine
        self.forecasting_engine = ForecastingEngine(forecasting_config)
        
        # Initialize goal executor
        self.executor = AutonomousGoalExecutor(executor_config)
        
        # Configuration
        self.autonomous_mode = self.config.get("autonomous_mode", True)
        self.goal_sync_interval = self.config.get("goal_sync_interval_seconds", 30)
        self.analysis_interval = self.config.get("analysis_interval_minutes", 60)
        
        # State
        self.running = False
        self.sync_thread: Optional[Thread] = None
        self.last_analysis_time: Optional[datetime] = None
        
        # Statistics
        self.stats = {
            "uptime_seconds": 0,
            "goals_created": 0,
            "goals_executed": 0,
            "goals_achieved": 0,
            "total_predictions": 0,
            "total_actions": 0,
            "start_time": None
        }
        
        # Register default action handlers
        self._register_default_handlers()
        
        logger.info("GoalDrivenAgent initialized")
    
    def _register_default_handlers(self):
        """Register default action handlers."""
        
        # Resource optimization handler
        def optimize_resources(params: Dict[str, Any], goal_id: str) -> Dict[str, Any]:
            logger.info(f"Optimizing resources for goal {goal_id}")
            # Implementation would adjust resource allocation
            return {
                "success": True,
                "impact": {"resource_utilization": -0.05}  # 5% improvement
            }
        
        # Capacity planning handler
        def plan_capacity(params: Dict[str, Any], goal_id: str) -> Dict[str, Any]:
            logger.info(f"Planning capacity for goal {goal_id}")
            # Implementation would trigger scaling operations
            return {
                "success": True,
                "impact": {"capacity": 1.2}  # 20% increase
            }
        
        # Bottleneck prevention handler
        def prevent_bottleneck(params: Dict[str, Any], goal_id: str) -> Dict[str, Any]:
            logger.info(f"Preventing bottleneck for goal {goal_id}")
            # Implementation would adjust configurations
            return {
                "success": True,
                "impact": {"bottleneck_risk": -0.3}  # 30% reduction
            }
        
        # Performance optimization handler
        def optimize_performance(params: Dict[str, Any], goal_id: str) -> Dict[str, Any]:
            logger.info(f"Optimizing performance for goal {goal_id}")
            # Implementation would optimize algorithms, caching, etc.
            return {
                "success": True,
                "impact": {"latency": -0.1}  # 10% reduction
            }
        
        # Pattern adaptation handler
        def adapt_to_pattern(params: Dict[str, Any], goal_id: str) -> Dict[str, Any]:
            logger.info(f"Adapting to pattern for goal {goal_id}")
            # Implementation would adjust behavior based on patterns
            return {
                "success": True,
                "impact": {"efficiency": 0.15}  # 15% improvement
            }
        
        self.executor.register_action_handler("optimize_resources", optimize_resources)
        self.executor.register_action_handler("plan_capacity", plan_capacity)
        self.executor.register_action_handler("prevent_bottleneck", prevent_bottleneck)
        self.executor.register_action_handler("optimize_performance", optimize_performance)
        self.executor.register_action_handler("adapt_to_pattern", adapt_to_pattern)
    
    def register_action_handler(self, action_name: str, handler):
        """Register a custom action handler."""
        self.executor.register_action_handler(action_name, handler)
    
    def start(self):
        """Start the autonomous agent."""
        if self.running:
            logger.warning("GoalDrivenAgent already running")
            return
        
        self.running = True
        self.stats["start_time"] = datetime.now().isoformat()
        
        # Start forecasting engine
        self.forecasting_engine.start()
        
        # Start goal executor
        self.executor.start()
        
        # Start goal synchronization loop
        if self.autonomous_mode:
            self.sync_thread = Thread(target=self._autonomous_loop, daemon=True)
            self.sync_thread.start()
            logger.info("GoalDrivenAgent started in AUTONOMOUS mode")
        else:
            logger.info("GoalDrivenAgent started in MANUAL mode")
    
    def stop(self):
        """Stop the autonomous agent."""
        logger.info("Stopping GoalDrivenAgent...")
        self.running = False
        
        if self.sync_thread:
            self.sync_thread.join(timeout=10)
        
        self.executor.stop()
        self.forecasting_engine.stop()
        
        logger.info("GoalDrivenAgent stopped")
    
    def _autonomous_loop(self):
        """Main autonomous behavior loop."""
        while self.running:
            try:
                # Update uptime
                if self.stats["start_time"]:
                    start = datetime.fromisoformat(self.stats["start_time"])
                    self.stats["uptime_seconds"] = (datetime.now() - start).total_seconds()
                
                # Periodic comprehensive analysis
                if self._should_run_analysis():
                    logger.info("Running comprehensive analysis...")
                    self._run_comprehensive_analysis()
                    self.last_analysis_time = datetime.now()
                
                # Sync goals: forecasting -> executor
                self._sync_goals()
                
                # Update goal progress based on execution results
                self._update_goal_progress()
                
                # Sleep before next iteration
                time.sleep(self.goal_sync_interval)
                
            except Exception as e:
                logger.error(f"Error in autonomous loop: {e}", exc_info=True)
                time.sleep(10)  # Wait before retrying
    
    def _should_run_analysis(self) -> bool:
        """Determine if comprehensive analysis should run."""
        if self.last_analysis_time is None:
            return True
        
        time_since_last = datetime.now() - self.last_analysis_time
        return time_since_last >= timedelta(minutes=self.analysis_interval)
    
    def _run_comprehensive_analysis(self):
        """Run comprehensive predictive analysis and set goals."""
        try:
            # Get current metrics (would come from performance monitor in production)
            current_metrics = self._get_current_metrics()
            
            # Run analysis and set goals
            new_goals = self.forecasting_engine.analyze_and_set_goals(
                current_metrics=current_metrics,
                horizon_hours=24
            )
            
            with self.lock:
                self.stats["goals_created"] += len(new_goals)
                self.stats["total_predictions"] += 1
            
            logger.info(f"Comprehensive analysis complete: {len(new_goals)} new goals set")
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}", exc_info=True)
    
    def _sync_goals(self):
        """Synchronize goals from forecasting engine to executor."""
        try:
            # Get active goals from forecasting engine
            active_goals = self.forecasting_engine.get_active_goals()
            
            # Get currently scheduled goals in executor
            executor_state = self.executor.to_dict()
            scheduled_goal_ids = {
                plan["goal_id"] for plan in executor_state["scheduled_plans"]
            }
            
            # Schedule new goals
            new_goals = [
                goal for goal in active_goals
                if goal.goal_id not in scheduled_goal_ids
            ]
            
            for goal in new_goals:
                try:
                    self.executor.schedule_goal(goal)
                    with self.lock:
                        self.stats["goals_executed"] += 1
                    logger.info(f"Scheduled new goal: {goal.goal_id} - {goal.description}")
                except Exception as e:
                    logger.error(f"Error scheduling goal {goal.goal_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error syncing goals: {e}", exc_info=True)
    
    def _update_goal_progress(self):
        """Update goal progress based on execution results."""
        try:
            executor_state = self.executor.to_dict()
            
            # Process recent execution results
            for result in executor_state["recent_executions"]:
                goal_id = result["goal_id"]
                
                # Get goal from forecasting engine
                goal = self.forecasting_engine.get_goal(goal_id)
                if not goal:
                    continue
                
                # Update progress based on execution success
                if result["success"]:
                    # Calculate progress based on impact
                    impact = result.get("impact", {})
                    progress_increase = len(result["actions_completed"]) / max(len(goal.actions), 1)
                    
                    current_progress = goal.progress
                    new_progress = min(1.0, current_progress + progress_increase)
                    
                    self.forecasting_engine.update_goal_progress(
                        goal_id,
                        new_progress,
                        goal.current_value
                    )
                    
                    if new_progress >= 1.0:
                        with self.lock:
                            self.stats["goals_achieved"] += 1
                        logger.info(f"Goal achieved: {goal_id}")
                
        except Exception as e:
            logger.error(f"Error updating goal progress: {e}", exc_info=True)
    
    def _get_current_metrics(self) -> Dict[str, float]:
        """Get current system metrics."""
        # In production, this would integrate with PerformanceMonitor
        # For now, return sample metrics
        return {
            "cpu_usage": 45.0,
            "memory_usage": 60.0,
            "latency": 150.0,
            "throughput": 1000.0,
            "error_rate": 0.01,
            "cost": 100.0
        }
    
    def record_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Record a metric for forecasting."""
        self.forecasting_engine.add_metric_data(metric_name, value, timestamp)
    
    def record_event(
        self,
        event_type: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record an event for pattern recognition."""
        self.forecasting_engine.add_event(event_type, timestamp, metadata)
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        with self.lock:
            stats = self.stats.copy()
        
        # Get component statuses
        forecasting_stats = self.forecasting_engine.get_statistics()
        executor_stats = self.executor.get_statistics()
        
        # Get active goals
        active_goals = self.forecasting_engine.get_active_goals()
        
        return {
            "running": self.running,
            "autonomous_mode": self.autonomous_mode,
            "uptime_seconds": stats["uptime_seconds"],
            "statistics": stats,
            "active_goals": len(active_goals),
            "goals_by_priority": {
                priority.value: len([g for g in active_goals if g.priority == priority])
                for priority in GoalPriority
            },
            "forecasting": forecasting_stats,
            "executor": executor_stats,
            "last_analysis_time": self.last_analysis_time.isoformat() if self.last_analysis_time else None
        }
    
    def get_goal_overview(self) -> Dict[str, Any]:
        """Get overview of all goals."""
        active_goals = self.forecasting_engine.get_active_goals()
        
        return {
            "total_active_goals": len(active_goals),
            "goals_by_type": {
                gt.value: len([g for g in active_goals if g.goal_type == gt])
                for gt in GoalType
            },
            "goals_by_priority": {
                priority.value: len([g for g in active_goals if g.priority == priority])
                for priority in GoalPriority
            },
            "goals": [
                {
                    "goal_id": g.goal_id,
                    "type": g.goal_type.value,
                    "priority": g.priority.value,
                    "description": g.description,
                    "progress": g.progress,
                    "status": g.status.value,
                    "deadline": g.deadline.isoformat(),
                    "execution_status": self.executor.get_execution_status(g.goal_id)
                }
                for g in active_goals
            ]
        }
    
    def get_predictions(self, horizon_hours: int = 24) -> Dict[str, Any]:
        """Get system state predictions."""
        current_metrics = self._get_current_metrics()
        prediction = self.forecasting_engine.predict_system_state(
            current_metrics,
            horizon_hours
        )
        return prediction.to_dict()
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive report of agent activity."""
        return {
            "agent_status": self.get_agent_status(),
            "goals": self.get_goal_overview(),
            "forecasting_report": self.forecasting_engine.get_comprehensive_report(
                self._get_current_metrics()
            ),
            "executor_state": self.executor.to_dict(),
            "learning_insights": self.executor.get_learning_insights()
        }
    
    def force_analysis(self) -> Dict[str, Any]:
        """Manually trigger comprehensive analysis."""
        logger.info("Forcing comprehensive analysis...")
        self._run_comprehensive_analysis()
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": "Comprehensive analysis completed"
        }
    
    def set_autonomous_mode(self, enabled: bool):
        """Enable or disable autonomous mode."""
        was_enabled = self.autonomous_mode
        self.autonomous_mode = enabled
        
        if enabled and not was_enabled and self.running:
            # Start autonomous loop
            self.sync_thread = Thread(target=self._autonomous_loop, daemon=True)
            self.sync_thread.start()
            logger.info("Autonomous mode ENABLED")
        elif not enabled and was_enabled:
            logger.info("Autonomous mode DISABLED")
    
    def to_dict(self) -> Dict[str, Any]:
        """Export agent state."""
        return self.get_comprehensive_report()

