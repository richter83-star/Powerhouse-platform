"""
SLA Monitoring API Routes

Provides endpoints for viewing SLA metrics, uptime, and compliance reports.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database.session import get_db
from database.models import User
from api.auth import get_current_user
from core.monitoring.sla_tracker import get_sla_tracker, SLAMetrics, SLAStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sla", tags=["SLA"])

# Request/Response Models
class SLAMetricsResponse(BaseModel):
    period_start: str
    period_end: str
    uptime_percentage: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float
    sla_target: float
    sla_status: str


class ServiceHealthResponse(BaseModel):
    overall_health: str
    is_up: bool
    healthy_services: int
    total_services: int
    health_percentage: float
    last_check: str
    downtime_periods: int


@router.get("/metrics", response_model=SLAMetricsResponse)
async def get_sla_metrics(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get SLA metrics for a time period.
    
    Requires admin authentication (you should add admin check).
    """
    try:
        sla_tracker = get_sla_tracker()
        
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        metrics = sla_tracker.get_sla_metrics(start, end)
        
        return SLAMetricsResponse(
            period_start=metrics.period_start.isoformat(),
            period_end=metrics.period_end.isoformat(),
            uptime_percentage=metrics.uptime_percentage,
            total_requests=metrics.total_requests,
            successful_requests=metrics.successful_requests,
            failed_requests=metrics.failed_requests,
            average_response_time_ms=metrics.average_response_time_ms,
            p95_response_time_ms=metrics.p95_response_time_ms,
            p99_response_time_ms=metrics.p99_response_time_ms,
            error_rate=metrics.error_rate,
            sla_target=metrics.sla_target,
            sla_status=metrics.sla_status.value
        )
    except Exception as e:
        logger.error(f"Get SLA metrics error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get SLA metrics"
        )


@router.get("/uptime", response_model=Dict[str, Any])
async def get_uptime(
    days: int = Query(30, ge=1, le=365, description="Number of days to calculate uptime"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get uptime percentage for the last N days.
    """
    try:
        sla_tracker = get_sla_tracker()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        uptime = sla_tracker.calculate_uptime(start_date, end_date)
        sla_target = sla_tracker.sla_target
        
        return {
            "uptime_percentage": uptime,
            "sla_target": sla_target,
            "compliant": uptime >= sla_target,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    except Exception as e:
        logger.error(f"Get uptime error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get uptime"
        )


@router.get("/health", response_model=ServiceHealthResponse)
async def get_service_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current service health summary.
    """
    try:
        sla_tracker = get_sla_tracker()
        health = sla_tracker.get_service_health_summary()
        
        return ServiceHealthResponse(**health)
    except Exception as e:
        logger.error(f"Get service health error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get service health"
        )


@router.get("/breach-check", response_model=Dict[str, Any])
async def check_sla_breach(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if SLA is currently breached.
    """
    try:
        sla_tracker = get_sla_tracker()
        breach = sla_tracker.check_sla_breach()
        
        if breach:
            return breach
        
        return {
            "breached": False,
            "message": "SLA is compliant"
        }
    except Exception as e:
        logger.error(f"Check SLA breach error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check SLA breach"
        )


@router.get("/response-times", response_model=Dict[str, float])
async def get_response_time_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get response time metrics (avg, p95, p99).
    """
    try:
        sla_tracker = get_sla_tracker()
        metrics = sla_tracker.calculate_response_time_metrics()
        
        return metrics
    except Exception as e:
        logger.error(f"Get response times error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get response time metrics"
        )


@router.get("/error-rate", response_model=Dict[str, Any])
async def get_error_rate(
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get error rate for the last N days.
    """
    try:
        sla_tracker = get_sla_tracker()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        error_rate = sla_tracker.calculate_error_rate(start_date, end_date)
        
        return {
            "error_rate_percentage": error_rate,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    except Exception as e:
        logger.error(f"Get error rate error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get error rate"
        )

