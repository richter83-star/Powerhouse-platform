
"""
Adaptive Orchestrator with Dynamic Self-Configuration

An orchestrator that can autonomously adjust its runtime parameters
based on performance feedback from the PerformanceMonitor.
"""

from typing import Dict, Any, Optional, List
import time
from datetime import datetime

from core.orchestrator import Orchestrator
from core.performance_monitor_with_config import get_adaptive_monitor
from core.dynamic_config_manager import get_config_manager
from utils.logging import get_logger

logger = get_logger(__name__)


class AdaptiveOrchestrator(Orchestrator):
    """
    Self-configuring orchestrator that adjusts its behavior based on
    performance metrics.
    
    Features:
    - Automatic parameter tuning based on latency, success rate, etc.
    - Dynamic agent selection and routing
    - Resource-aware execution
    - Performance-driven optimization
    """
    
    def __init__(
        self,
        agent_names: List[str],
        max_agents: int = 19,
        enable_adaptation: bool = True
    ):
        """
        Initialize adaptive orchestrator.
        
        Args:
            agent_names: List of agent names to load
            max_agents: Maximum number of agents
            enable_adaptation: Enable dynamic configuration
        """
        super().__init__(agent_names, max_agents)
        
        self.enable_adaptation = enable_adaptation
        
        if self.enable_adaptation:
            # Get adaptive monitor and config manager
            self.monitor = get_adaptive_monitor(enable_dynamic_config=True)
            self.config_manager = get_config_manager()
            
            logger.info("Adaptive orchestrator initialized with dynamic configuration")
        else:
            self.monitor = None
            self.config_manager = None
    
    def run(
        self,
        task: str,
        config: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run agents with adaptive configuration.
        
        Args:
            task: Task description
            config: Optional configuration overrides
            project_id: Project identifier
            
        Returns:
            dict: Execution results
        """
        start_time = time.time()
        
        # Get current configuration parameters
        if self.enable_adaptation:
            runtime_config = self._get_runtime_config()
        else:
            runtime_config = {}
        
        # Build context with runtime config
        context = {
            "task": task,
            "outputs": [],
            "state": {},
            "runtime_config": runtime_config,
            "start_time": start_time
        }
        
        if config:
            context.update(config)
        
        try:
            # Run with base orchestrator logic
            result = super().run(task, context)
            
            # Record metrics if monitoring enabled
            if self.enable_adaptation and self.monitor:
                duration_ms = (time.time() - start_time) * 1000
                self._record_run_metrics(result, duration_ms, project_id)
            
            # Add configuration info to result
            result["runtime_config"] = runtime_config
            result["execution_time_ms"] = (time.time() - start_time) * 1000
            
            return result
        
        except Exception as e:
            logger.error(f"Adaptive orchestrator error: {e}", exc_info=True)
            
            if self.enable_adaptation:
                # Record failure
                self._record_failure(task, str(e), project_id)
            
            raise
    
    def _get_runtime_config(self) -> Dict[str, Any]:
        """
        Get current runtime configuration from the config manager.
        
        Returns:
            dict: Current configuration parameters
        """
        if not self.enable_adaptation or not self.config_manager:
            return {}
        
        # Get all configured parameters
        config = {}
        
        param_names = [
            "planner_search_depth",
            "max_retries",
            "timeout_seconds",
            "batch_size",
            "memory_cache_size_mb",
            "quality_threshold"
        ]
        
        for param_name in param_names:
            value = self.config_manager.get_parameter(param_name)
            if value is not None:
                config[param_name] = value
        
        return config
    
    def _record_run_metrics(
        self,
        result: Dict[str, Any],
        duration_ms: float,
        project_id: Optional[str]
    ):
        """Record metrics for the orchestrator run."""
        
        try:
            # Determine success status
            status = "success"
            if "error" in result:
                status = "failure"
            elif result.get("outputs"):
                # Check if any agent failed
                for output in result["outputs"]:
                    if isinstance(output, dict) and "error" in output:
                        status = "partial"
                        break
            
            # Record metrics
            self.monitor.record_agent_run(
                run_id=result.get("run_id", f"run_{int(time.time())}"),
                agent_name="orchestrator",
                agent_type="orchestrator",
                status=status,
                duration_ms=duration_ms,
                metadata={
                    "task": result.get("task"),
                    "num_agents": len(self.agents),
                    "num_outputs": len(result.get("outputs", [])),
                    "has_evaluation": "evaluation" in result
                }
            )
        
        except Exception as e:
            logger.error(f"Error recording run metrics: {e}", exc_info=True)
    
    def _record_failure(self, task: str, error: str, project_id: Optional[str]):
        """Record a failed run."""
        
        try:
            self.monitor.record_agent_run(
                run_id=f"failed_{int(time.time())}",
                agent_name="orchestrator",
                agent_type="orchestrator",
                status="failure",
                duration_ms=0,
                error_type="orchestrator_error",
                metadata={
                    "task": task,
                    "error": error
                }
            )
        except Exception as e:
            logger.error(f"Error recording failure: {e}", exc_info=True)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance and configuration summary.
        
        Returns:
            dict: Comprehensive status
        """
        if not self.enable_adaptation or not self.monitor:
            return {"adaptive_mode": False}
        
        # Get metrics from monitor
        metrics = self.monitor.get_enhanced_metrics()
        
        # Get configuration status
        config_status = self.monitor.get_configuration_status()
        
        return {
            "adaptive_mode": True,
            "timestamp": datetime.now().isoformat(),
            "agent_count": len(self.agents),
            "agents": [a.__class__.__name__ for a in self.agents],
            "performance": metrics.get("performance_metrics", {}),
            "configuration": config_status,
            "health_score": self._calculate_health_score(metrics)
        }
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall system health score (0-100)."""
        
        perf = metrics.get("performance_metrics", {})
        
        success_weight = 0.4
        latency_weight = 0.3
        error_weight = 0.2
        quality_weight = 0.1
        
        # Success rate score (0-100)
        success_score = perf.get("success_rate", 0.8) * 100
        
        # Latency score (inverse, 0-100)
        latency_ms = perf.get("avg_latency_ms", 1000)
        latency_score = max(0, 100 - (latency_ms / 50))  # 5s = 0 points
        
        # Error rate score (inverse, 0-100)
        error_rate = perf.get("error_rate", 0.1)
        error_score = max(0, 100 - (error_rate * 500))
        
        # Quality score (0-100)
        quality_score = perf.get("avg_quality_score", 0.7) * 100
        
        # Weighted average
        health = (
            success_score * success_weight +
            latency_score * latency_weight +
            error_score * error_weight +
            quality_score * quality_weight
        )
        
        return round(health, 2)
    
    def force_configuration_update(self):
        """Force immediate configuration evaluation and update."""
        
        if not self.enable_adaptation or not self.monitor:
            logger.warning("Adaptive mode is disabled")
            return
        
        logger.info("Forcing configuration update")
        self.monitor.force_adjustment_evaluation()
    
    def get_current_parameter(self, param_name: str) -> Any:
        """
        Get current value of a parameter.
        
        Args:
            param_name: Parameter name
            
        Returns:
            Current parameter value or None
        """
        if not self.enable_adaptation or not self.config_manager:
            return None
        
        return self.config_manager.get_parameter(param_name)
    
    def set_parameter(self, param_name: str, value: Any, reason: str = "manual") -> bool:
        """
        Manually set a parameter value.
        
        Args:
            param_name: Parameter name
            value: New value
            reason: Reason for change
            
        Returns:
            bool: Success status
        """
        if not self.enable_adaptation or not self.config_manager:
            logger.warning("Adaptive mode is disabled")
            return False
        
        return self.config_manager.set_parameter(param_name, value, reason)
    
    def reset_configuration(self):
        """Reset all parameters to defaults."""
        
        if not self.enable_adaptation or not self.config_manager:
            logger.warning("Adaptive mode is disabled")
            return
        
        logger.info("Resetting configuration to defaults")
        self.config_manager.reset_to_defaults()

