"""
Usage Tracking API Routes

Provides endpoints for viewing usage statistics, limits, and projections.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database.session import get_db
from database.models import User
from api.auth import get_current_user
from core.commercial.usage_tracker import get_usage_tracker, LimitStatus
from core.commercial.tenant_manager import get_tenant_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/usage", tags=["Usage"])

# Request/Response Models
class UsageSummaryResponse(BaseModel):
    tenant_id: str
    start_date: str
    end_date: str
    api_calls: int
    agent_executions: int
    workflow_runs: int
    storage_gb: float
    compute_hours: float
    total_cost: float
    breakdown: Dict[str, float]


class UsageStatusResponse(BaseModel):
    resource_type: str
    current: float
    limit: float
    percentage: float
    allowed: bool
    message: str
    limit_type: str


class UsageProjectionResponse(BaseModel):
    projected_api_calls: int
    projected_agent_executions: int
    projected_workflow_runs: int
    projected_storage_gb: float
    projected_cost: float
    current_daily_average: Dict[str, float]


@router.get("/current-month", response_model=UsageSummaryResponse)
async def get_current_month_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current month usage summary for authenticated user's tenant.
    """
    try:
        tenant_id = getattr(current_user, 'tenant_id', None) or "default"
        usage_tracker = get_usage_tracker()
        
        summary = usage_tracker.get_current_month_usage(tenant_id)
        
        return UsageSummaryResponse(
            tenant_id=summary.tenant_id,
            start_date=summary.start_date.isoformat(),
            end_date=summary.end_date.isoformat(),
            api_calls=summary.api_calls,
            agent_executions=summary.agent_executions,
            workflow_runs=summary.workflow_runs,
            storage_gb=summary.storage_gb,
            compute_hours=summary.compute_hours,
            total_cost=summary.total_cost,
            breakdown=summary.breakdown
        )
    except Exception as e:
        logger.error(f"Get current month usage error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage summary"
        )


@router.get("/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get usage summary for a date range.
    """
    try:
        tenant_id = getattr(current_user, 'tenant_id', None) or "default"
        usage_tracker = get_usage_tracker()
        
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        summary = usage_tracker.get_usage_summary(tenant_id, start, end)
        
        return UsageSummaryResponse(
            tenant_id=summary.tenant_id,
            start_date=summary.start_date.isoformat(),
            end_date=summary.end_date.isoformat(),
            api_calls=summary.api_calls,
            agent_executions=summary.agent_executions,
            workflow_runs=summary.workflow_runs,
            storage_gb=summary.storage_gb,
            compute_hours=summary.compute_hours,
            total_cost=summary.total_cost,
            breakdown=summary.breakdown
        )
    except Exception as e:
        logger.error(f"Get usage summary error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage summary"
        )


@router.get("/trends", response_model=List[UsageSummaryResponse])
async def get_usage_trends(
    months: int = Query(6, ge=1, le=12, description="Number of months to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get usage trends over multiple months.
    """
    try:
        tenant_id = getattr(current_user, 'tenant_id', None) or "default"
        usage_tracker = get_usage_tracker()
        
        trends = usage_tracker.get_usage_trends(tenant_id, months)
        
        return [
            UsageSummaryResponse(
                tenant_id=t.tenant_id,
                start_date=t.start_date.isoformat(),
                end_date=t.end_date.isoformat(),
                api_calls=t.api_calls,
                agent_executions=t.agent_executions,
                workflow_runs=t.workflow_runs,
                storage_gb=t.storage_gb,
                compute_hours=t.compute_hours,
                total_cost=t.total_cost,
                breakdown=t.breakdown
            )
            for t in trends
        ]
    except Exception as e:
        logger.error(f"Get usage trends error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage trends"
        )


@router.get("/status", response_model=List[UsageStatusResponse])
async def get_usage_status(
    resource_types: Optional[str] = Query(None, description="Comma-separated resource types"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current usage status for all resource types.
    Shows current usage, limits, and warnings.
    """
    try:
        tenant_id = getattr(current_user, 'tenant_id', None) or "default"
        usage_tracker = get_usage_tracker()
        
        types_list = resource_types.split(",") if resource_types else None
        
        statuses = usage_tracker.get_current_usage_status(tenant_id, types_list)
        
        return [
            UsageStatusResponse(
                resource_type=resource_type,
                current=status.current,
                limit=status.limit,
                percentage=status.percentage,
                allowed=status.allowed,
                message=status.message,
                limit_type=status.limit_type.value
            )
            for resource_type, status in statuses.items()
        ]
    except Exception as e:
        logger.error(f"Get usage status error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage status"
        )


@router.get("/projections", response_model=UsageProjectionResponse)
async def get_usage_projections(
    days_ahead: int = Query(30, ge=1, le=90, description="Number of days to project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get usage projections based on current trends.
    """
    try:
        tenant_id = getattr(current_user, 'tenant_id', None) or "default"
        usage_tracker = get_usage_tracker()
        
        projections = usage_tracker.get_usage_projections(tenant_id, days_ahead)
        
        return UsageProjectionResponse(**projections)
    except Exception as e:
        logger.error(f"Get usage projections error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage projections"
        )


@router.get("/estimate-bill", response_model=Dict[str, Any])
async def estimate_monthly_bill(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Estimate monthly bill based on current usage.
    """
    try:
        tenant_id = getattr(current_user, 'tenant_id', None) or "default"
        usage_tracker = get_usage_tracker()
        
        estimate = usage_tracker.estimate_monthly_bill(tenant_id)
        
        return estimate
    except Exception as e:
        logger.error(f"Estimate monthly bill error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to estimate monthly bill"
        )
