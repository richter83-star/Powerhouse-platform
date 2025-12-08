
"""
API Routes for Dynamic Configuration Management

Provides endpoints to view and manage dynamic configuration parameters.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.dynamic_config_manager import (
    get_config_manager, AdjustmentStrategy, ConfigurationScope
)
from core.performance_monitor_with_config import get_adaptive_monitor
from utils.logging import get_logger
from api.auth import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/config", tags=["Configuration"])


# Request/Response Models

class ParameterUpdate(BaseModel):
    """Request to update a parameter."""
    parameter_name: str = Field(..., description="Parameter name")
    value: Any = Field(..., description="New parameter value")
    reason: str = Field(default="manual", description="Reason for change")


class ConfigurationSnapshot(BaseModel):
    """Configuration snapshot response."""
    timestamp: str
    strategy: str
    parameters: Dict[str, Any]
    active_rules: Dict[str, Any]
    recent_changes: List[Dict[str, Any]]


class ConfigurationStats(BaseModel):
    """Configuration statistics response."""
    total_changes: int
    changes_by_parameter: Dict[str, int]
    changes_by_rule: Dict[str, int]
    rollbacks: int
    avg_changes_per_hour: float


class HealthStatus(BaseModel):
    """System health status."""
    timestamp: str
    health_score: float
    adaptive_mode: bool
    performance_metrics: Dict[str, Any]
    configuration: Dict[str, Any]


# Endpoints

@router.get("/snapshot", response_model=Dict[str, Any])
async def get_configuration_snapshot(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get current configuration snapshot.
    
    Returns:
        Current configuration state with all parameters and recent changes
    """
    try:
        config_manager = get_config_manager()
        snapshot = config_manager.get_configuration_snapshot()
        
        return {
            "success": True,
            "data": snapshot
        }
    
    except Exception as e:
        logger.error(f"Error getting configuration snapshot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=Dict[str, Any])
async def get_configuration_statistics(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get configuration change statistics.
    
    Returns:
        Statistics about configuration changes
    """
    try:
        config_manager = get_config_manager()
        stats = config_manager.get_statistics()
        
        return {
            "success": True,
            "data": stats
        }
    
    except Exception as e:
        logger.error(f"Error getting configuration statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parameters", response_model=Dict[str, Any])
async def get_all_parameters(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get all configurable parameters with their current values and bounds.
    
    Returns:
        Dictionary of all parameters
    """
    try:
        config_manager = get_config_manager()
        
        parameters = {}
        for name, bounds in config_manager.parameter_bounds.items():
            current_value = config_manager.get_parameter(name)
            parameters[name] = {
                "current_value": current_value,
                "min_value": bounds.min_value,
                "max_value": bounds.max_value,
                "default_value": bounds.default_value,
                "step_size": bounds.step_size,
                "type": bounds.parameter_type
            }
        
        return {
            "success": True,
            "data": parameters
        }
    
    except Exception as e:
        logger.error(f"Error getting parameters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parameters/{parameter_name}", response_model=Dict[str, Any])
async def get_parameter(
    parameter_name: str,
    agent_name: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get specific parameter value.
    
    Args:
        parameter_name: Name of the parameter
        agent_name: Optional agent-specific override
        
    Returns:
        Parameter value and metadata
    """
    try:
        config_manager = get_config_manager()
        
        value = config_manager.get_parameter(parameter_name, agent_name)
        
        if value is None:
            raise HTTPException(
                status_code=404,
                detail=f"Parameter '{parameter_name}' not found"
            )
        
        bounds = config_manager.parameter_bounds.get(parameter_name)
        
        return {
            "success": True,
            "data": {
                "parameter_name": parameter_name,
                "value": value,
                "bounds": {
                    "min": bounds.min_value,
                    "max": bounds.max_value,
                    "default": bounds.default_value,
                    "type": bounds.parameter_type
                } if bounds else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parameter: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parameters/{parameter_name}", response_model=Dict[str, Any])
async def update_parameter(
    parameter_name: str,
    update: ParameterUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Manually update a parameter value.
    
    Args:
        parameter_name: Name of the parameter to update
        update: Update request with new value
        
    Returns:
        Updated parameter information
    """
    try:
        config_manager = get_config_manager()
        
        success = config_manager.set_parameter(
            name=parameter_name,
            value=update.value,
            reason=f"Manual update: {update.reason}"
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to update parameter '{parameter_name}'"
            )
        
        new_value = config_manager.get_parameter(parameter_name)
        
        return {
            "success": True,
            "message": f"Parameter '{parameter_name}' updated successfully",
            "data": {
                "parameter_name": parameter_name,
                "new_value": new_value,
                "reason": update.reason
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating parameter: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", response_model=Dict[str, Any])
async def reset_to_defaults(
    current_user: Dict = Depends(get_current_user)
):
    """
    Reset all parameters to default values.
    
    Returns:
        Confirmation of reset
    """
    try:
        config_manager = get_config_manager()
        config_manager.reset_to_defaults()
        
        return {
            "success": True,
            "message": "All parameters reset to defaults"
        }
    
    except Exception as e:
        logger.error(f"Error resetting parameters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules", response_model=Dict[str, Any])
async def get_adjustment_rules(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get all adjustment rules.
    
    Returns:
        List of adjustment rules with their configuration
    """
    try:
        config_manager = get_config_manager()
        
        rules = {}
        for name, rule in config_manager.adjustment_rules.items():
            rules[name] = {
                "name": rule.name,
                "description": rule.description,
                "enabled": rule.enabled,
                "trigger_metric": rule.trigger_metric.value,
                "trigger_threshold": rule.trigger_threshold,
                "trigger_operator": rule.trigger_operator,
                "target_parameter": rule.target_parameter,
                "adjustment_value": rule.adjustment_value,
                "adjustment_type": rule.adjustment_type,
                "scope": rule.scope.value,
                "priority": rule.priority,
                "trigger_count": rule.trigger_count,
                "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None
            }
        
        return {
            "success": True,
            "data": rules
        }
    
    except Exception as e:
        logger.error(f"Error getting adjustment rules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_name}/enable", response_model=Dict[str, Any])
async def enable_rule(
    rule_name: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Enable an adjustment rule.
    
    Args:
        rule_name: Name of the rule to enable
        
    Returns:
        Confirmation
    """
    try:
        config_manager = get_config_manager()
        
        if rule_name not in config_manager.adjustment_rules:
            raise HTTPException(
                status_code=404,
                detail=f"Rule '{rule_name}' not found"
            )
        
        config_manager.adjustment_rules[rule_name].enabled = True
        
        return {
            "success": True,
            "message": f"Rule '{rule_name}' enabled"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_name}/disable", response_model=Dict[str, Any])
async def disable_rule(
    rule_name: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Disable an adjustment rule.
    
    Args:
        rule_name: Name of the rule to disable
        
    Returns:
        Confirmation
    """
    try:
        config_manager = get_config_manager()
        
        if rule_name not in config_manager.adjustment_rules:
            raise HTTPException(
                status_code=404,
                detail=f"Rule '{rule_name}' not found"
            )
        
        config_manager.adjustment_rules[rule_name].enabled = False
        
        return {
            "success": True,
            "message": f"Rule '{rule_name}' disabled"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, Any])
async def get_system_health(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get comprehensive system health status.
    
    Returns:
        System health with performance and configuration data
    """
    try:
        monitor = get_adaptive_monitor()
        
        enhanced_metrics = monitor.get_enhanced_metrics()
        config_status = monitor.get_configuration_status()
        
        # Calculate health score
        perf = enhanced_metrics.get("performance_metrics", {})
        success_rate = perf.get("success_rate", 0.8)
        error_rate = perf.get("error_rate", 0.1)
        avg_latency = perf.get("avg_latency_ms", 1000)
        
        health_score = (
            success_rate * 50 +
            max(0, (1 - error_rate)) * 30 +
            max(0, (1 - min(1, avg_latency / 10000))) * 20
        )
        
        return {
            "success": True,
            "data": {
                "timestamp": datetime.now().isoformat(),
                "health_score": round(health_score, 2),
                "adaptive_mode": config_status.get("enabled", False),
                "performance_metrics": perf,
                "configuration": config_status,
                "status": "healthy" if health_score >= 70 else "degraded" if health_score >= 50 else "critical"
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting system health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/force-evaluation", response_model=Dict[str, Any])
async def force_configuration_evaluation(
    current_user: Dict = Depends(get_current_user)
):
    """
    Force immediate evaluation and application of adjustment rules.
    
    Returns:
        Results of the evaluation
    """
    try:
        monitor = get_adaptive_monitor()
        
        # Force evaluation
        monitor.force_adjustment_evaluation()
        
        # Get updated configuration
        config_status = monitor.get_configuration_status()
        
        return {
            "success": True,
            "message": "Configuration evaluation completed",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "recent_changes": config_status.get("recent_changes", [])
            }
        }
    
    except Exception as e:
        logger.error(f"Error forcing evaluation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

