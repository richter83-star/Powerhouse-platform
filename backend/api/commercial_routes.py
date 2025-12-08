
"""
API routes for commercial features (multi-tenancy, billing, usage tracking)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

from backend.core.commercial.tenant_manager import get_tenant_manager, TenantTier
from backend.core.commercial.usage_tracker import get_usage_tracker

router = APIRouter(prefix="/api/commercial", tags=["Commercial"])

# Request/Response Models
class CreateTenantRequest(BaseModel):
    tenant_id: str
    name: str
    tier: str = "free"
    metadata: Optional[Dict[str, Any]] = None

class UpdateTierRequest(BaseModel):
    new_tier: str

class RecordUsageRequest(BaseModel):
    tenant_id: str
    resource_type: str
    quantity: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

# Tenant Management Endpoints
@router.post("/tenants")
async def create_tenant(request: CreateTenantRequest):
    """Create a new tenant"""
    try:
        tenant_manager = get_tenant_manager()
        tier = TenantTier(request.tier.lower())
        tenant = tenant_manager.create_tenant(
            tenant_id=request.tenant_id,
            name=request.name,
            tier=tier,
            metadata=request.metadata
        )
        return tenant_manager.get_tenant_stats(tenant.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tenants")
async def list_tenants(active_only: bool = True):
    """List all tenants"""
    tenant_manager = get_tenant_manager()
    tenants = tenant_manager.list_tenants(active_only=active_only)
    return [tenant_manager.get_tenant_stats(t.tenant_id) for t in tenants]

@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str):
    """Get tenant details"""
    tenant_manager = get_tenant_manager()
    stats = tenant_manager.get_tenant_stats(tenant_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return stats

@router.put("/tenants/{tenant_id}/tier")
async def update_tenant_tier(tenant_id: str, request: UpdateTierRequest):
    """Update tenant subscription tier"""
    try:
        tenant_manager = get_tenant_manager()
        new_tier = TenantTier(request.new_tier.lower())
        tenant = tenant_manager.update_tenant_tier(tenant_id, new_tier)
        return tenant_manager.get_tenant_stats(tenant.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/tenants/{tenant_id}")
async def deactivate_tenant(tenant_id: str):
    """Deactivate a tenant"""
    tenant_manager = get_tenant_manager()
    tenant_manager.deactivate_tenant(tenant_id)
    return {"status": "deactivated", "tenant_id": tenant_id}

@router.get("/tenants/{tenant_id}/features/{feature}")
async def check_feature_access(tenant_id: str, feature: str):
    """Check if tenant has access to a feature"""
    tenant_manager = get_tenant_manager()
    has_access = tenant_manager.check_feature_access(tenant_id, feature)
    return {"tenant_id": tenant_id, "feature": feature, "has_access": has_access}

# Usage Tracking Endpoints
@router.post("/usage")
async def record_usage(request: RecordUsageRequest):
    """Record a usage event"""
    tracker = get_usage_tracker()
    record = tracker.record_usage(
        tenant_id=request.tenant_id,
        resource_type=request.resource_type,
        quantity=request.quantity,
        metadata=request.metadata
    )
    return {
        "tenant_id": record.tenant_id,
        "resource_type": record.resource_type,
        "quantity": record.quantity,
        "timestamp": record.timestamp.isoformat()
    }

@router.get("/usage/{tenant_id}/summary")
async def get_usage_summary(
    tenant_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get usage summary for a tenant"""
    tracker = get_usage_tracker()
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    summary = tracker.get_usage_summary(tenant_id, start, end)
    return {
        "tenant_id": summary.tenant_id,
        "start_date": summary.start_date.isoformat(),
        "end_date": summary.end_date.isoformat(),
        "api_calls": summary.api_calls,
        "agent_executions": summary.agent_executions,
        "workflow_runs": summary.workflow_runs,
        "storage_gb": summary.storage_gb,
        "compute_hours": summary.compute_hours,
        "total_cost": summary.total_cost,
        "breakdown": summary.breakdown
    }

@router.get("/usage/{tenant_id}/current-month")
async def get_current_month_usage(tenant_id: str):
    """Get current month usage for a tenant"""
    tracker = get_usage_tracker()
    summary = tracker.get_current_month_usage(tenant_id)
    return {
        "tenant_id": summary.tenant_id,
        "start_date": summary.start_date.isoformat(),
        "end_date": summary.end_date.isoformat(),
        "api_calls": summary.api_calls,
        "agent_executions": summary.agent_executions,
        "workflow_runs": summary.workflow_runs,
        "storage_gb": summary.storage_gb,
        "compute_hours": summary.compute_hours,
        "total_cost": summary.total_cost,
        "breakdown": summary.breakdown
    }

@router.get("/usage/{tenant_id}/trends")
async def get_usage_trends(tenant_id: str, months: int = 6):
    """Get usage trends over multiple months"""
    tracker = get_usage_tracker()
    trends = tracker.get_usage_trends(tenant_id, months)
    return [
        {
            "month": f"{t.start_date.year}-{t.start_date.month:02d}",
            "api_calls": t.api_calls,
            "agent_executions": t.agent_executions,
            "workflow_runs": t.workflow_runs,
            "total_cost": t.total_cost
        }
        for t in trends
    ]

@router.get("/billing/{tenant_id}/estimate")
async def estimate_monthly_bill(tenant_id: str):
    """Estimate monthly bill based on current usage"""
    tracker = get_usage_tracker()
    return tracker.estimate_monthly_bill(tenant_id)
