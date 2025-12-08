
"""
API routes for observability, telemetry, and monitoring.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ..core.observability import telemetry
from ..core.resilience import (
    checkpoint_manager,
    circuit_breaker_registry,
    rate_limit_store
)

router = APIRouter(prefix="/api/observability", tags=["observability"])


# ============================================================================
# TELEMETRY & TRACING
# ============================================================================

@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str) -> Dict[str, Any]:
    """
    Get detailed trace information by trace ID.
    
    Args:
        trace_id: Trace identifier
        
    Returns:
        Trace summary with all spans
    """
    trace_summary = telemetry.get_trace_summary(trace_id)
    
    if "error" in trace_summary:
        raise HTTPException(status_code=404, detail=trace_summary["error"])
    
    return trace_summary


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get current system metrics including counters, gauges, and histograms.
    
    Returns:
        Dictionary of all metrics
    """
    return telemetry.get_system_metrics()


@router.post("/metrics/reset")
async def reset_metrics() -> Dict[str, str]:
    """
    Reset all metrics to zero.
    
    Returns:
        Success message
    """
    telemetry.metrics.reset()
    return {"status": "success", "message": "Metrics reset successfully"}


# ============================================================================
# CHECKPOINTS
# ============================================================================

@router.get("/checkpoints")
async def list_checkpoints(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID")
) -> Dict[str, Any]:
    """
    List available checkpoints with optional filtering.
    
    Args:
        agent_id: Optional agent ID filter
        workflow_id: Optional workflow ID filter
        
    Returns:
        List of checkpoint metadata
    """
    checkpoints = checkpoint_manager.list_checkpoints(
        agent_id=agent_id,
        workflow_id=workflow_id
    )
    
    return {
        "count": len(checkpoints),
        "checkpoints": [
            {
                "checkpoint_id": c.checkpoint_id,
                "timestamp": c.timestamp,
                "agent_id": c.agent_id,
                "workflow_id": c.workflow_id,
                "size_bytes": c.size_bytes,
                "compressed": c.compressed
            }
            for c in checkpoints
        ]
    }


@router.get("/checkpoints/{checkpoint_id}")
async def get_checkpoint_metadata(checkpoint_id: str) -> Dict[str, Any]:
    """
    Get metadata for a specific checkpoint.
    
    Args:
        checkpoint_id: Checkpoint identifier
        
    Returns:
        Checkpoint metadata
    """
    if checkpoint_id not in checkpoint_manager.metadata_store:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    
    metadata = checkpoint_manager.metadata_store[checkpoint_id]
    
    return {
        "checkpoint_id": metadata.checkpoint_id,
        "timestamp": metadata.timestamp,
        "agent_id": metadata.agent_id,
        "workflow_id": metadata.workflow_id,
        "state_hash": metadata.state_hash,
        "size_bytes": metadata.size_bytes,
        "compressed": metadata.compressed,
        "version": metadata.version
    }


@router.delete("/checkpoints/{checkpoint_id}")
async def delete_checkpoint(checkpoint_id: str) -> Dict[str, str]:
    """
    Delete a checkpoint.
    
    Args:
        checkpoint_id: Checkpoint identifier
        
    Returns:
        Success message
    """
    success = checkpoint_manager.delete_checkpoint(checkpoint_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Checkpoint not found or deletion failed")
    
    return {"status": "success", "message": f"Checkpoint {checkpoint_id} deleted"}


class CleanupRequest(BaseModel):
    agent_id: str
    workflow_id: str
    keep_count: int = 5


@router.post("/checkpoints/cleanup")
async def cleanup_checkpoints(request: CleanupRequest) -> Dict[str, Any]:
    """
    Clean up old checkpoints, keeping only the N most recent.
    
    Args:
        request: Cleanup parameters
        
    Returns:
        Number of checkpoints deleted
    """
    deleted_count = checkpoint_manager.cleanup_old_checkpoints(
        agent_id=request.agent_id,
        workflow_id=request.workflow_id,
        keep_count=request.keep_count
    )
    
    return {
        "status": "success",
        "deleted_count": deleted_count,
        "message": f"Cleaned up {deleted_count} old checkpoints"
    }


# ============================================================================
# CIRCUIT BREAKERS
# ============================================================================

@router.get("/circuit-breakers")
async def get_circuit_breakers() -> Dict[str, Any]:
    """
    Get status of all circuit breakers.
    
    Returns:
        Dictionary of circuit breaker states
    """
    return circuit_breaker_registry.get_all_states()


@router.get("/circuit-breakers/{name}")
async def get_circuit_breaker(name: str) -> Dict[str, Any]:
    """
    Get status of a specific circuit breaker.
    
    Args:
        name: Circuit breaker name
        
    Returns:
        Circuit breaker state
    """
    breakers = circuit_breaker_registry.get_all_states()
    
    if name not in breakers:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")
    
    return breakers[name]


@router.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(name: str) -> Dict[str, str]:
    """
    Manually reset a circuit breaker to closed state.
    
    Args:
        name: Circuit breaker name
        
    Returns:
        Success message
    """
    if name not in circuit_breaker_registry.breakers:
        raise HTTPException(status_code=404, detail="Circuit breaker not found")
    
    breaker = circuit_breaker_registry.breakers[name]
    breaker.reset()
    
    return {
        "status": "success",
        "message": f"Circuit breaker {name} reset to closed state"
    }


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.
    
    Returns:
        System health status
    """
    circuit_breakers = circuit_breaker_registry.get_all_states()
    
    # Count open circuit breakers
    open_circuits = sum(
        1 for state in circuit_breakers.values()
        if state["state"] == "open"
    )
    
    # Get checkpoint count
    all_checkpoints = checkpoint_manager.list_checkpoints()
    
    # Get metrics summary
    metrics = telemetry.get_system_metrics()
    
    return {
        "status": "healthy" if open_circuits == 0 else "degraded",
        "timestamp": telemetry.tracer.service_name,
        "circuit_breakers": {
            "total": len(circuit_breakers),
            "open": open_circuits,
            "degraded": open_circuits > 0
        },
        "checkpoints": {
            "total": len(all_checkpoints)
        },
        "metrics": {
            "counters": len(metrics.get("counters", {})),
            "gauges": len(metrics.get("gauges", {})),
            "histograms": len(metrics.get("histograms", {}))
        }
    }
