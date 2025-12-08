"""
Metrics and monitoring API routes.
"""
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from core.monitoring.metrics import get_metrics, get_metrics_content_type
from core.monitoring.health_metrics import get_health_metrics

router = APIRouter(prefix="/metrics", tags=["monitoring"])


@router.get(
    "/prometheus",
    summary="Prometheus Metrics",
    description="Prometheus metrics endpoint in OpenMetrics format"
)
async def prometheus_metrics():
    """
    Get Prometheus metrics.
    
    This endpoint exposes metrics in OpenMetrics format for Prometheus scraping.
    """
    metrics = get_metrics()
    return Response(
        content=metrics,
        media_type=get_metrics_content_type()
    )


@router.get(
    "/health",
    summary="Health Metrics",
    description="Get comprehensive health and system metrics"
)
async def health_metrics():
    """
    Get health metrics including system resources.
    
    Returns CPU, memory, and disk usage metrics.
    """
    return get_health_metrics()

