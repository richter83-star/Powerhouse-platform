
"""
API routes for deployment features (health checks, backups)
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Optional, Any
from pydantic import BaseModel

from backend.core.deployment.health_checks import get_health_check
from backend.core.deployment.backup_manager import get_backup_manager

router = APIRouter(prefix="/api/deployment", tags=["Deployment"])

# Health Check Endpoints
@router.get("/health")
async def health_check():
    """Comprehensive health check"""
    health = get_health_check()
    return await health.run_checks()

@router.get("/health/ready")
async def readiness_check():
    """Readiness probe for k8s"""
    health = get_health_check()
    result = await health.get_readiness()
    if not result["ready"]:
        raise HTTPException(status_code=503, detail="Service not ready")
    return result

@router.get("/health/live")
async def liveness_check():
    """Liveness probe for k8s"""
    health = get_health_check()
    return await health.get_liveness()

# Backup Management Endpoints
class CreateBackupRequest(BaseModel):
    backup_type: str = "full"
    data: Optional[Dict[str, Any]] = None
    retention_days: int = 7

@router.post("/backups")
async def create_backup(request: CreateBackupRequest):
    """Create a new backup"""
    backup_manager = get_backup_manager()
    metadata = backup_manager.create_backup(
        backup_type=request.backup_type,
        data=request.data,
        retention_days=request.retention_days
    )
    return {
        "backup_id": metadata.backup_id,
        "created_at": metadata.created_at.isoformat(),
        "backup_type": metadata.backup_type,
        "size_bytes": metadata.size_bytes,
        "status": metadata.status
    }

@router.get("/backups")
async def list_backups(backup_type: Optional[str] = None):
    """List all backups"""
    backup_manager = get_backup_manager()
    backups = backup_manager.list_backups(backup_type)
    return [
        {
            "backup_id": b.backup_id,
            "created_at": b.created_at.isoformat(),
            "backup_type": b.backup_type,
            "size_bytes": b.size_bytes,
            "status": b.status,
            "retention_days": b.retention_days
        }
        for b in backups
    ]

@router.get("/backups/status")
async def get_backup_status():
    """Get overall backup status"""
    backup_manager = get_backup_manager()
    return backup_manager.get_backup_status()

@router.post("/backups/{backup_id}/restore")
async def restore_backup(backup_id: str):
    """Restore from a backup"""
    try:
        backup_manager = get_backup_manager()
        data = backup_manager.restore_backup(backup_id)
        return {"status": "restored", "backup_id": backup_id, "data": data}
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/backups/cleanup")
async def cleanup_old_backups():
    """Remove old backups based on retention policy"""
    backup_manager = get_backup_manager()
    removed = backup_manager.cleanup_old_backups()
    return {"removed_count": len(removed), "removed_backups": removed}
