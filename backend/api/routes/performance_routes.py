
"""
API routes for Performance Monitoring.

Provides REST endpoints to access real-time performance metrics,
alerts, and reports for the agent system.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from core.performance_monitor import (
    get_performance_monitor,
    PerformanceMetrics,
    AgentPerformance,
    PerformanceAlert,
    AlertLevel,
    MetricType
)
from utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/performance", tags=["performance"])


# ==================== Request/Response Models ====================

class RecordAccuracyRequest(BaseModel):
    """Request to record accuracy measurement."""
    agent_name: str
    task_id: str
    predicted_outcome: dict
    actual_outcome: dict
    feedback_source: str = "user"
    metadata: Optional[dict] = None


class MetricsResponse(BaseModel):
    """Response containing performance metrics."""
    metrics: dict
    generated_at: str


class ReportResponse(BaseModel):
    """Response containing full performance report."""
    report: dict


class AlertsResponse(BaseModel):
    """Response containing alerts."""
    alerts: list
    total_count: int


# ==================== Endpoints ====================

@router.get("/health", summary="Get system health status")
async def get_health():
    """Get current system health status."""
    try:
        monitor = get_performance_monitor()
        metrics = monitor.get_system_metrics()
        health_score = monitor._calculate_health_score(metrics)
        
        return {
            "status": "healthy" if health_score >= 70 else "degraded" if health_score >= 50 else "unhealthy",
            "health_score": health_score,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting health status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/system", response_model=MetricsResponse, summary="Get system-wide metrics")
async def get_system_metrics(
    time_window_minutes: Optional[int] = Query(None, description="Time window in minutes")
):
    """
    Get system-wide performance metrics.
    
    Args:
        time_window_minutes: Time window to analyze (default: configured window)
        
    Returns:
        MetricsResponse: System metrics
    """
    try:
        monitor = get_performance_monitor()
        metrics = monitor.get_system_metrics(time_window_minutes)
        
        return MetricsResponse(
            metrics=metrics.__dict__,
            generated_at=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/agent/{agent_name}", summary="Get agent-specific metrics")
async def get_agent_metrics(
    agent_name: str,
    time_window_minutes: Optional[int] = Query(None, description="Time window in minutes")
):
    """
    Get performance metrics for a specific agent.
    
    Args:
        agent_name: Agent name
        time_window_minutes: Time window to analyze
        
    Returns:
        AgentPerformance: Agent metrics
    """
    try:
        monitor = get_performance_monitor()
        performance = monitor.get_agent_metrics(agent_name, time_window_minutes)
        
        return {
            "agent_name": performance.agent_name,
            "agent_type": performance.agent_type,
            "status": performance.status,
            "last_run": performance.last_run,
            "metrics": performance.metrics.__dict__,
            "scores": {
                "specialization": performance.specialization_score,
                "reliability": performance.reliability_score,
                "efficiency": performance.efficiency_score
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting agent metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/agents", summary="Get metrics for all agents")
async def get_all_agent_metrics(
    time_window_minutes: Optional[int] = Query(None, description="Time window in minutes")
):
    """Get performance metrics for all agents."""
    try:
        monitor = get_performance_monitor()
        
        # Get all tracked agents
        with monitor._lock:
            agent_names = list(monitor._agent_metrics.keys())
        
        agent_metrics = {}
        for agent_name in agent_names:
            performance = monitor.get_agent_metrics(agent_name, time_window_minutes)
            agent_metrics[agent_name] = {
                "agent_type": performance.agent_type,
                "status": performance.status,
                "last_run": performance.last_run,
                "metrics": performance.metrics.__dict__,
                "scores": {
                    "specialization": performance.specialization_score,
                    "reliability": performance.reliability_score,
                    "efficiency": performance.efficiency_score
                }
            }
        
        return {
            "agents": agent_metrics,
            "total_agents": len(agent_names),
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting all agent metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=AlertsResponse, summary="Get performance alerts")
async def get_alerts(
    level: Optional[str] = Query(None, description="Filter by alert level"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    limit: int = Query(50, description="Maximum alerts to return")
):
    """
    Get recent performance alerts.
    
    Args:
        level: Filter by alert level (info, warning, critical)
        agent_name: Filter by agent name
        limit: Maximum alerts to return
        
    Returns:
        AlertsResponse: List of alerts
    """
    try:
        monitor = get_performance_monitor()
        
        alert_level = AlertLevel(level) if level else None
        alerts = monitor.get_alerts(alert_level, agent_name, limit)
        
        return AlertsResponse(
            alerts=[alert.__dict__ for alert in alerts],
            total_count=len(alerts)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid alert level: {level}")
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report", response_model=ReportResponse, summary="Generate performance report")
async def generate_report(
    include_agents: bool = Query(True, description="Include per-agent metrics"),
    time_window_minutes: Optional[int] = Query(None, description="Time window in minutes")
):
    """
    Generate comprehensive performance report.
    
    Args:
        include_agents: Include per-agent breakdowns
        time_window_minutes: Time window to analyze
        
    Returns:
        ReportResponse: Complete performance report
    """
    try:
        monitor = get_performance_monitor()
        report = monitor.generate_report(include_agents, time_window_minutes)
        
        return ReportResponse(report=report)
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accuracy", summary="Record accuracy measurement")
async def record_accuracy(request: RecordAccuracyRequest):
    """
    Record accuracy measurement against real-world outcome.
    
    This endpoint allows users or automated systems to provide feedback
    on agent predictions compared to actual outcomes.
    """
    try:
        monitor = get_performance_monitor()
        
        monitor.record_accuracy(
            agent_name=request.agent_name,
            task_id=request.task_id,
            predicted_outcome=request.predicted_outcome,
            actual_outcome=request.actual_outcome,
            feedback_source=request.feedback_source,
            metadata=request.metadata
        )
        
        return {
            "status": "success",
            "message": "Accuracy measurement recorded",
            "agent_name": request.agent_name,
            "task_id": request.task_id
        }
    except Exception as e:
        logger.error(f"Error recording accuracy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync", summary="Sync metrics from database")
async def sync_metrics(lookback_hours: int = Query(24, description="Hours to look back")):
    """
    Sync performance metrics from database.
    
    Loads historical agent runs from the database to build complete metrics.
    """
    try:
        monitor = get_performance_monitor()
        monitor.sync_with_database(lookback_hours)
        
        return {
            "status": "success",
            "message": f"Synced metrics from last {lookback_hours} hours",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error syncing metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="Get monitor statistics")
async def get_stats():
    """Get internal statistics about the performance monitor."""
    try:
        monitor = get_performance_monitor()
        stats = monitor.get_stats()
        
        return {
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends", summary="Get performance trends")
async def get_trends():
    """Get performance trend indicators."""
    try:
        monitor = get_performance_monitor()
        
        with monitor._lock:
            trends = monitor._running_stats.get("trends", {})
        
        return {
            "trends": trends,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class TriggerRetrainingRequest(BaseModel):
    """Request to trigger model retraining."""
    reason: Optional[str] = "Manual trigger via API"
    force_full_retrain: bool = False


@router.post("/trigger-retraining", summary="Trigger model retraining")
async def trigger_retraining(request: TriggerRetrainingRequest = None):
    """
    Manually trigger model retraining.
    
    This endpoint allows operators to manually trigger model retraining
    when they notice performance issues or want to force a model update.
    
    Normally, retraining is triggered automatically when the PerformanceMonitor
    detects accuracy degradation below thresholds.
    
    **Parameters:**
    - `reason`: Description of why retraining is being triggered
    - `force_full_retrain`: If true, performs full retrain; otherwise incremental
    
    **Returns:**
    - Success status, events processed, and retraining details
    """
    try:
        monitor = get_performance_monitor()
        
        if request is None:
            request = TriggerRetrainingRequest()
        
        result = monitor.trigger_retraining(
            reason=request.reason,
            force_full_retrain=request.force_full_retrain
        )
        
        if result.get('success'):
            return {
                "status": "success",
                "message": "Retraining completed successfully",
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "failed",
                "message": "Retraining failed",
                "error": result.get('error'),
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error triggering retraining: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
