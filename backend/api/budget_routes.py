
"""
Budget and rate limiting API routes
Provides endpoints for managing spending limits and monitoring usage
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
import logging

from config.budget_config import (
    get_budget_dashboard,
    get_budget_limits,
    update_budget_limits,
    check_auto_loop_allowed,
    record_auto_loop_iteration,
    BudgetLimits
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/budget", tags=["budget"])


class UpdateBudgetRequest(BaseModel):
    """Request model for updating budget limits"""
    daily_max_dollars: Optional[float] = None
    auto_loop_max_iterations: Optional[int] = None
    auto_loop_max_concurrent: Optional[int] = None
    max_llm_calls_per_hour: Optional[int] = None
    max_llm_calls_per_day: Optional[int] = None
    warning_threshold_percent: Optional[float] = None
    emergency_stop_enabled: Optional[bool] = None


@router.get("/dashboard")
async def get_dashboard() -> Dict:
    """
    Get budget dashboard with limits, usage, and status
    
    Returns:
        Dict with budget limits, current usage, and status
    """
    try:
        dashboard = get_budget_dashboard()
        return {
            "success": True,
            "dashboard": dashboard
        }
    except Exception as e:
        logger.error(f"Error getting budget dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/limits")
async def get_limits() -> Dict:
    """
    Get current budget limits
    
    Returns:
        Current budget limit configuration
    """
    try:
        limits = get_budget_limits()
        return {
            "success": True,
            "limits": limits.model_dump()
        }
    except Exception as e:
        logger.error(f"Error getting budget limits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/limits")
async def update_limits(request: UpdateBudgetRequest) -> Dict:
    """
    Update budget limits
    
    Args:
        request: New budget limits (only provided fields will be updated)
        
    Returns:
        Updated budget limits
    """
    try:
        # Get current limits
        current_limits = get_budget_limits()
        
        # Update only provided fields
        update_data = request.model_dump(exclude_none=True)
        
        # Merge with current limits
        new_limits_data = current_limits.model_dump()
        new_limits_data.update(update_data)
        
        # Update
        update_budget_limits(new_limits_data)
        
        return {
            "success": True,
            "message": "Budget limits updated successfully",
            "limits": new_limits_data
        }
    except Exception as e:
        logger.error(f"Error updating budget limits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check/auto-loop")
async def check_auto_loop() -> Dict:
    """
    Check if auto loop agent is allowed to run
    
    Returns:
        Dict with allowed status, reason, and usage stats
    """
    try:
        result = check_auto_loop_allowed()
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Error checking auto loop status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record/auto-loop")
async def record_iteration(agent_name: str = "auto_loop") -> Dict:
    """
    Record an auto loop iteration
    
    Args:
        agent_name: Name of the agent (default: auto_loop)
        
    Returns:
        Confirmation with warning if approaching limits
    """
    try:
        result = record_auto_loop_iteration(agent_name)
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Error recording auto loop iteration: {e}")
        raise HTTPException(status_code=500, detail=str(e))
