
"""
Orchestrator with Autonomous Goal-Driven Agent

Integrates the autonomous agent into the main orchestrator.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from utils.logging import get_logger
from core.orchestrator_with_forecasting import OrchestratorWithForecasting
from core.goal_driven_agent import GoalDrivenAgent

logger = get_logger(__name__)


class OrchestratorWithAutonomousAgent(OrchestratorWithForecasting):
    """
    Enhanced orchestrator with fully autonomous goal-driven behavior.
    
    Features:
    - All forecasting capabilities
    - Autonomous goal setting
    - Autonomous goal execution
    - Continuous learning and adaptation
    """
    
    def __init__(
        self,
        performance_monitor_config: Optional[Dict[str, Any]] = None,
        config_manager_config: Optional[Dict[str, Any]] = None,
        forecasting_config: Optional[Dict[str, Any]] = None,
        executor_config: Optional[Dict[str, Any]] = None,
        agent_config: Optional[Dict[str, Any]] = None
    ):
        # Initialize parent (includes forecasting)
        super().__init__(
            performance_monitor_config,
            config_manager_config,
            forecasting_config
        )
        
        # Initialize autonomous agent
        # Reuse the forecasting engine from parent
        self.autonomous_agent = GoalDrivenAgent(
            forecasting_config=None,  # Will use existing engine
            executor_config=executor_config,
            agent_config=agent_config
        )
        
        # Replace agent's forecasting engine with ours (shared instance)
        self.autonomous_agent.forecasting_engine = self.forecasting_engine
        
        # Start autonomous agent
        self.autonomous_agent.start()
        
        logger.info("OrchestratorWithAutonomousAgent initialized and started")
    
    async def execute_with_autonomous_behavior(
        self,
        agent_name: str,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute agent task with full autonomous behavior tracking.
        
        Args:
            agent_name: Name of agent to execute
            task_description: Task description
            context: Additional context
        
        Returns:
            Execution result with autonomous agent metrics
        """
        # Record the execution event
        self.autonomous_agent.record_event(
            f"agent_execution_{agent_name}",
            metadata={"task": task_description}
        )
        
        # Execute with forecasting (from parent class)
        result = await self.execute_with_forecasting(
            agent_name,
            task_description,
            context
        )
        
        # Record metrics for the autonomous agent
        if "metrics" in result:
            for metric_name, value in result["metrics"].items():
                self.autonomous_agent.record_metric(metric_name, value)
        
        # Add autonomous agent status to result
        agent_status = self.autonomous_agent.get_agent_status()
        result["autonomous_agent"] = {
            "running": agent_status["running"],
            "active_goals": agent_status["active_goals"],
            "uptime_seconds": agent_status["uptime_seconds"]
        }
        
        return result
    
    def get_autonomous_report(self) -> Dict[str, Any]:
        """Get comprehensive autonomous agent report."""
        return self.autonomous_agent.get_comprehensive_report()
    
    def get_goal_overview(self) -> Dict[str, Any]:
        """Get goal overview."""
        return self.autonomous_agent.get_goal_overview()
    
    def force_autonomous_analysis(self) -> Dict[str, Any]:
        """Manually trigger autonomous analysis."""
        return self.autonomous_agent.force_analysis()
    
    def set_autonomous_mode(self, enabled: bool):
        """Enable/disable autonomous mode."""
        self.autonomous_agent.set_autonomous_mode(enabled)
    
    def shutdown(self):
        """Shutdown orchestrator and all components."""
        logger.info("Shutting down orchestrator with autonomous agent...")
        
        if self.autonomous_agent:
            self.autonomous_agent.stop()
        
        # Call parent shutdown
        super().shutdown()
        
        logger.info("Orchestrator shutdown complete")

