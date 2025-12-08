
"""
Enhanced Orchestrator with Performance Monitoring Integration.

This module extends the base orchestrator with comprehensive performance
monitoring capabilities.
"""

import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.orchestrator import Orchestrator
from core.performance_monitor import get_performance_monitor
from utils.logging import get_logger

logger = get_logger(__name__)


class MonitoredOrchestrator(Orchestrator):
    """
    Orchestrator with integrated performance monitoring.
    
    Automatically tracks all agent executions and reports metrics
    to the performance monitor.
    """
    
    def __init__(self, *args, enable_monitoring: bool = True, **kwargs):
        """
        Initialize monitored orchestrator.
        
        Args:
            *args: Arguments for base Orchestrator
            enable_monitoring: Enable performance monitoring
            **kwargs: Keyword arguments for base Orchestrator
        """
        super().__init__(*args, **kwargs)
        self.enable_monitoring = enable_monitoring
        
        if self.enable_monitoring:
            self.performance_monitor = get_performance_monitor()
            logger.info("Performance monitoring enabled for orchestrator")
    
    def run(
        self,
        task: str,
        project_id: str,
        execution_strategy: str = "sequential",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run agents with performance monitoring.
        
        Args:
            task: Task description
            project_id: Project identifier
            execution_strategy: Execution strategy
            context: Additional context
            
        Returns:
            dict: Execution results with monitoring data
        """
        run_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Execute base orchestrator run
            results = super().run(task, project_id, execution_strategy, context)
            
            # Record performance metrics if enabled
            if self.enable_monitoring:
                self._record_run_metrics(
                    run_id=run_id,
                    results=results,
                    duration_ms=(time.time() - start_time) * 1000
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Orchestrator run failed: {e}", exc_info=True)
            
            # Record failure
            if self.enable_monitoring:
                self._record_run_failure(run_id, str(e))
            
            raise
    
    def _record_run_metrics(
        self,
        run_id: str,
        results: Dict[str, Any],
        duration_ms: float
    ):
        """Record metrics for a complete run."""
        try:
            # Record metrics for each agent in the run
            for agent_output in results.get("agent_outputs", []):
                agent_name = agent_output.get("agent", "unknown")
                agent_type = agent_output.get("agent_type", "unknown")
                
                output_data = agent_output.get("output", {})
                status = output_data.get("status", "unknown")
                
                # Extract performance data
                metadata = output_data.get("metadata", {})
                
                self.performance_monitor.record_agent_run(
                    run_id=run_id,
                    agent_name=agent_name,
                    agent_type=agent_type,
                    status="success" if status == "success" else "failure",
                    duration_ms=metadata.get("execution_time_ms", duration_ms),
                    tokens_used=metadata.get("tokens_used"),
                    cost=metadata.get("cost"),
                    memory_mb=metadata.get("memory_mb"),
                    cpu_ms=metadata.get("cpu_ms"),
                    quality_score=metadata.get("quality_score"),
                    confidence=metadata.get("confidence"),
                    error_type=agent_output.get("error") if "error" in agent_output else None,
                    metadata=metadata
                )
            
            logger.debug(f"Recorded metrics for run {run_id}")
            
        except Exception as e:
            logger.error(f"Error recording run metrics: {e}", exc_info=True)
    
    def _record_run_failure(self, run_id: str, error_message: str):
        """Record metrics for a failed run."""
        try:
            self.performance_monitor.record_agent_run(
                run_id=run_id,
                agent_name="orchestrator",
                agent_type="orchestrator",
                status="failure",
                duration_ms=0,
                error_type="orchestrator_error",
                metadata={"error_message": error_message}
            )
        except Exception as e:
            logger.error(f"Error recording failure: {e}", exc_info=True)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary for this orchestrator.
        
        Returns:
            dict: Performance summary
        """
        if not self.enable_monitoring:
            return {"monitoring_enabled": False}
        
        system_metrics = self.performance_monitor.get_system_metrics()
        
        return {
            "monitoring_enabled": True,
            "total_tasks": system_metrics.total_tasks,
            "success_rate": system_metrics.success_rate,
            "avg_latency_ms": system_metrics.avg_latency_ms,
            "total_cost": system_metrics.total_cost,
            "health_score": self.performance_monitor._calculate_health_score(system_metrics)
        }
