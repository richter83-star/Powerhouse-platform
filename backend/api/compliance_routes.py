"""
Compliance API Routes

Handles GDPR compliance features: data export, deletion, and consent management.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from database.session import get_db
from database.models import User
from api.auth import get_current_user
from core.compliance.gdpr_service import GDPRService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/compliance", tags=["Compliance"])

# Request/Response Models
class ConsentRequest(BaseModel):
    consent_type: str = Field(..., description="Type of consent (marketing, analytics, necessary)")
    version: str = Field(..., description="Version of privacy policy/terms")
    consented: bool = Field(..., description="Whether user consents")


class ConsentResponse(BaseModel):
    id: str
    consent_type: str
    version: str
    consented: bool
    created_at: str
    revoked_at: Optional[str] = None


class DataExportRequestResponse(BaseModel):
    id: str
    status: str
    format: str
    requested_at: str
    completed_at: Optional[str] = None
    expires_at: Optional[str] = None
    file_path: Optional[str] = None


class DataDeletionRequestResponse(BaseModel):
    id: str
    status: str
    deletion_type: str
    requested_at: str
    verified: bool
    completed_at: Optional[str] = None


@router.post("/consent", response_model=ConsentResponse)
async def record_consent(
    request: ConsentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    http_request: Request = None
):
    """
    Record user consent for GDPR compliance.
    """
    try:
        gdpr_service = GDPRService(db)
        tenant_id = getattr(current_user, 'tenant_id', None)
        
        ip_address = None
        user_agent = None
        if http_request:
            ip_address = http_request.client.host if http_request.client else None
            user_agent = http_request.headers.get("user-agent")
        
        consent = gdpr_service.record_consent(
            user_id=current_user.id,
            consent_type=request.consent_type,
            version=request.version,
            consented=request.consented,
            tenant_id=tenant_id,
            consent_method="web",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return ConsentResponse(
            id=consent.id,
            consent_type=consent.consent_type,
            version=consent.version,
            consented=consent.consented,
            created_at=consent.created_at.isoformat(),
            revoked_at=consent.revoked_at.isoformat() if consent.revoked_at else None
        )
    except Exception as e:
        logger.error(f"Record consent error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record consent"
        )


@router.get("/consent", response_model=List[ConsentResponse])
async def get_consents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all consent records for current user.
    """
    try:
        gdpr_service = GDPRService(db)
        consents = gdpr_service.get_consents(current_user.id)
        
        return [
            ConsentResponse(
                id=c.id,
                consent_type=c.consent_type,
                version=c.version,
                consented=c.consented,
                created_at=c.created_at.isoformat(),
                revoked_at=c.revoked_at.isoformat() if c.revoked_at else None
            )
            for c in consents
        ]
    except Exception as e:
        logger.error(f"Get consents error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get consents"
        )


@router.post("/consent/revoke/{consent_type}")
async def revoke_consent(
    consent_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Revoke a specific consent.
    """
    try:
        gdpr_service = GDPRService(db)
        success = gdpr_service.revoke_consent(current_user.id, consent_type)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consent not found"
            )
        
        return {"message": "Consent revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke consent error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke consent"
        )


@router.post("/export/request", response_model=DataExportRequestResponse)
async def request_data_export(
    format: str = Query("json", description="Export format: json, csv, xml"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Request data export (GDPR right to data portability).
    """
    try:
        gdpr_service = GDPRService(db)
        tenant_id = getattr(current_user, 'tenant_id', None)
        
        export_request = gdpr_service.request_data_export(
            user_id=current_user.id,
            format=format,
            tenant_id=tenant_id
        )
        
        return DataExportRequestResponse(
            id=export_request.id,
            status=export_request.status,
            format=export_request.format,
            requested_at=export_request.requested_at.isoformat(),
            completed_at=export_request.completed_at.isoformat() if export_request.completed_at else None,
            expires_at=export_request.expires_at.isoformat() if export_request.expires_at else None,
            file_path=export_request.file_path
        )
    except Exception as e:
        logger.error(f"Request data export error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request data export"
        )


@router.get("/export/{request_id}")
async def get_data_export(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get exported user data.
    """
    try:
        from core.compliance.gdpr_service import DataExportRequest
        export_request = db.query(DataExportRequest).filter(
            DataExportRequest.id == request_id,
            DataExportRequest.user_id == current_user.id
        ).first()
        
        if not export_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export request not found"
            )
        
        if export_request.status != "completed":
            return {
                "status": export_request.status,
                "message": "Export is still processing" if export_request.status == "processing" else "Export pending"
            }
        
        # Export data
        gdpr_service = GDPRService(db)
        export_data = gdpr_service.export_user_data(current_user.id, export_request.format)
        
        return export_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get data export error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data export"
        )


@router.post("/deletion/request", response_model=DataDeletionRequestResponse)
async def request_data_deletion(
    deletion_type: str = Query("full", description="Deletion type: full or partial"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Request data deletion (GDPR right to be forgotten).
    
    Requires verification before deletion.
    """
    try:
        gdpr_service = GDPRService(db)
        tenant_id = getattr(current_user, 'tenant_id', None)
        
        deletion_request = gdpr_service.request_data_deletion(
            user_id=current_user.id,
            deletion_type=deletion_type,
            tenant_id=tenant_id
        )
        
        return DataDeletionRequestResponse(
            id=deletion_request.id,
            status=deletion_request.status,
            deletion_type=deletion_request.deletion_type,
            requested_at=deletion_request.requested_at.isoformat(),
            verified=deletion_request.verified_at is not None,
            completed_at=deletion_request.completed_at.isoformat() if deletion_request.completed_at else None
        )
    except Exception as e:
        logger.error(f"Request data deletion error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request data deletion"
        )


@router.post("/deletion/verify/{request_id}")
async def verify_deletion_request(
    request_id: str,
    verification_token: str = Query(..., description="Verification token"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify deletion request with token.
    """
    try:
        gdpr_service = GDPRService(db)
        success = gdpr_service.verify_deletion_request(request_id, verification_token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        return {"message": "Deletion request verified", "verified": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verify deletion request error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify deletion request"
        )


@router.post("/deletion/execute/{request_id}")
async def execute_data_deletion(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute verified data deletion.
    
    WARNING: This permanently deletes user data. Use with caution.
    """
    try:
        from core.compliance.gdpr_service import DataDeletionRequest
        deletion_request = db.query(DataDeletionRequest).filter(
            DataDeletionRequest.id == request_id,
            DataDeletionRequest.user_id == current_user.id,
            DataDeletionRequest.verified_at.isnot(None),
            DataDeletionRequest.status == "pending"
        ).first()
        
        if not deletion_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verified deletion request not found"
            )
        
        gdpr_service = GDPRService(db)
        deletion_summary = gdpr_service.delete_user_data(
            current_user.id,
            deletion_request.deletion_type
        )
        
        deletion_request.status = "completed"
        deletion_request.completed_at = datetime.utcnow()
        db.commit()
        
        return {
            "message": "Data deletion completed",
            "summary": deletion_summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute data deletion error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute data deletion"
        )

