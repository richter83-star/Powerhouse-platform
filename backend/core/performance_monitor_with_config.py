
"""
Performance Monitor with Dynamic Configuration Integration

Extends the PerformanceMonitor to automatically adjust runtime parameters
based on observed metrics.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import time

from core.performance_monitor import PerformanceMonitor, PerformanceMetrics
from core.dynamic_config_manager import (
    DynamicConfigManager, get_config_manager, AdjustmentStrategy
)
from utils.logging import get_logger

logger = get_logger(__name__)


class AdaptivePerformanceMonitor(PerformanceMonitor):
    """
    Performance Monitor with dynamic self-configuration capabilities.
    
    Automatically adjusts system parameters based on performance metrics.
    """
    
    def __init__(
        self,
        enable_dynamic_config: bool = True,
        adjustment_strategy: AdjustmentStrategy = AdjustmentStrategy.BALANCED,
        adjustment_interval_seconds: int = 60,
        *args,
        **kwargs
    ):
        """
        Initialize adaptive performance monitor.
        
        Args:
            enable_dynamic_config: Enable dynamic configuration adjustments
            adjustment_strategy: Strategy for parameter adjustments
            adjustment_interval_seconds: How often to evaluate adjustments
            *args, **kwargs: Arguments for base PerformanceMonitor
        """
        super().__init__(*args, **kwargs)
        
        self.enable_dynamic_config = enable_dynamic_config
        self.adjustment_interval_seconds = adjustment_interval_seconds
        
        # Initialize configuration manager
        if self.enable_dynamic_config:
            self.config_manager = get_config_manager(strategy=adjustment_strategy)
            self.last_adjustment_time = time.time()
            logger.info("Dynamic configuration enabled for performance monitor")
        else:
            self.config_manager = None
    
    def record_agent_run(self, *args, **kwargs):
        """
        Record agent run and trigger configuration evaluation.
        
        Overrides base method to add configuration adjustment logic.
        """
        # Call base implementation
        super().record_agent_run(*args, **kwargs)
        
        # Check if it's time to evaluate configurations
        if self.enable_dynamic_config:
            current_time = time.time()
            elapsed = current_time - self.last_adjustment_time
            
            if elapsed >= self.adjustment_interval_seconds:
                self._evaluate_and_adjust_config()
                self.last_adjustment_time = current_time
    
    def _evaluate_and_adjust_config(self):
        """
        Evaluate current metrics and adjust configuration if needed.
        """
        try:
            # Get current system metrics
            metrics = self.get_system_metrics()
            
            # Evaluate and apply adjustments
            changes = self.config_manager.evaluate_and_adjust(metrics)
            
            if changes:
                logger.info(f"Applied {len(changes)} configuration adjustments:")
                for change in changes:
                    logger.info(f"  - {change.parameter_name}: "
                              f"{change.old_value} -> {change.new_value} "
                              f"(reason: {change.reason})")
                
                # Create alert for configuration changes
                self._create_config_change_alert(changes, metrics)
            
            # Check for rollbacks
            rolled_back = self.config_manager.check_and_rollback(metrics)
            if rolled_back:
                logger.warning(f"Rolled back parameters due to performance degradation: "
                             f"{', '.join(rolled_back)}")
                self._create_rollback_alert(rolled_back, metrics)
        
        except Exception as e:
            logger.error(f"Error in configuration evaluation: {e}", exc_info=True)
    
    def _create_config_change_alert(
        self,
        changes: list,
        metrics: PerformanceMetrics
    ):
        """Create alert for configuration changes."""
        
        if not changes:
            return
        
        change_details = "\n".join([
            f"  • {c.parameter_name}: {c.old_value} → {c.new_value} ({c.reason})"
            for c in changes
        ])
        
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "category": "configuration_change",
            "title": f"{len(changes)} Configuration Change(s) Applied",
            "message": f"System parameters adjusted based on performance metrics:\n{change_details}",
            "metrics_snapshot": {
                "success_rate": metrics.success_rate,
                "avg_latency_ms": metrics.avg_latency_ms,
                "error_rate": metrics.error_rate,
                "avg_memory_mb": metrics.avg_memory_mb
            },
            "changes": [
                {
                    "parameter": c.parameter_name,
                    "old_value": c.old_value,
                    "new_value": c.new_value,
                    "triggered_by": c.triggered_by_metric,
                    "metric_value": c.metric_value
                }
                for c in changes
            ]
        }
        
        # Add to alerts (if available in base class)
        if hasattr(self, '_alerts'):
            self._alerts.append(alert)
    
    def _create_rollback_alert(self, parameters: list, metrics: PerformanceMetrics):
        """Create alert for parameter rollbacks."""
        
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": "warning",
            "category": "configuration_rollback",
            "title": "Configuration Rolled Back",
            "message": f"Parameters rolled back due to performance degradation: {', '.join(parameters)}",
            "metrics_snapshot": {
                "success_rate": metrics.success_rate,
                "avg_latency_ms": metrics.avg_latency_ms,
                "error_rate": metrics.error_rate
            },
            "rolled_back_parameters": parameters
        }
        
        if hasattr(self, '_alerts'):
            self._alerts.append(alert)
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """
        Get current configuration status.
        
        Returns:
            dict: Configuration status and statistics
        """
        if not self.enable_dynamic_config:
            return {"enabled": False}
        
        snapshot = self.config_manager.get_configuration_snapshot()
        stats = self.config_manager.get_statistics()
        
        return {
            "enabled": True,
            "strategy": snapshot["strategy"],
            "current_parameters": snapshot["parameters"],
            "statistics": stats,
            "recent_changes": snapshot["recent_changes"]
        }
    
    def get_parameter(self, name: str, agent_name: Optional[str] = None) -> Any:
        """
        Get current parameter value.
        
        Args:
            name: Parameter name
            agent_name: Optional agent-specific override
            
        Returns:
            Current parameter value
        """
        if not self.enable_dynamic_config:
            return None
        
        return self.config_manager.get_parameter(name, agent_name)
    
    def set_parameter(
        self,
        name: str,
        value: Any,
        reason: str = "manual"
    ) -> bool:
        """
        Manually set a parameter value.
        
        Args:
            name: Parameter name
            value: New value
            reason: Reason for change
            
        Returns:
            bool: Success status
        """
        if not self.enable_dynamic_config:
            logger.warning("Dynamic configuration is disabled")
            return False
        
        return self.config_manager.set_parameter(name, value, reason)
    
    def force_adjustment_evaluation(self):
        """Force immediate evaluation of adjustment rules."""
        
        if not self.enable_dynamic_config:
            logger.warning("Dynamic configuration is disabled")
            return
        
        logger.info("Forcing configuration adjustment evaluation")
        self._evaluate_and_adjust_config()
    
    def get_enhanced_metrics(self) -> Dict[str, Any]:
        """
        Get metrics enhanced with configuration information.
        
        Returns:
            dict: Metrics with configuration data
        """
        base_metrics = self.get_system_metrics()
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "performance_metrics": {
                "success_rate": base_metrics.success_rate,
                "avg_latency_ms": base_metrics.avg_latency_ms,
                "error_rate": base_metrics.error_rate,
                "total_cost": base_metrics.total_cost,
                "avg_memory_mb": base_metrics.avg_memory_mb,
                "avg_quality_score": base_metrics.avg_quality_score
            }
        }
        
        if self.enable_dynamic_config:
            result["configuration"] = self.get_configuration_status()
        
        return result


# Singleton instance
_adaptive_monitor_instance: Optional[AdaptivePerformanceMonitor] = None


def get_adaptive_monitor(
    enable_dynamic_config: bool = True,
    adjustment_strategy: AdjustmentStrategy = AdjustmentStrategy.BALANCED,
    **kwargs
) -> AdaptivePerformanceMonitor:
    """
    Get or create the global adaptive performance monitor instance.
    
    Args:
        enable_dynamic_config: Enable dynamic configuration
        adjustment_strategy: Adjustment strategy
        **kwargs: Additional arguments for monitor
        
    Returns:
        AdaptivePerformanceMonitor instance
    """
    global _adaptive_monitor_instance
    
    if _adaptive_monitor_instance is None:
        _adaptive_monitor_instance = AdaptivePerformanceMonitor(
            enable_dynamic_config=enable_dynamic_config,
            adjustment_strategy=adjustment_strategy,
            **kwargs
        )
    
    return _adaptive_monitor_instance

