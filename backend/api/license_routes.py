"""
License Management API Routes

Handles license key activation, validation, and management.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from database.session import get_db
from database.models import License, LicenseType, LicenseStatus, User, Tenant
from core.commercial.license_manager import LicenseManager, LicenseValidationResult
from api.auth import get_current_user
from api.models import User as UserModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/license", tags=["License"])

# Initialize license manager
license_manager = LicenseManager()


# Request/Response Models
class ActivateLicenseRequest(BaseModel):
    license_key: str = Field(..., description="License key to activate")
    device_name: Optional[str] = Field(None, description="Optional device name")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device information")


class ValidateLicenseRequest(BaseModel):
    license_key: str = Field(..., description="License key to validate")


class GenerateLicenseRequest(BaseModel):
    license_type: str = Field(default="standard", description="License type: trial, standard, enterprise, perpetual")
    seats: int = Field(default=1, ge=1, description="Number of user seats")
    max_devices: int = Field(default=1, ge=1, description="Maximum number of devices")
    trial_days: Optional[int] = Field(None, ge=1, le=90, description="Trial period in days (for trial licenses)")
    expiration_days: Optional[int] = Field(None, ge=1, description="Expiration in days (None for perpetual)")
    features: Optional[List[str]] = Field(default_factory=list, description="Enabled features")
    tenant_id: Optional[str] = Field(None, description="Associated tenant ID")
    user_id: Optional[str] = Field(None, description="Associated user ID")


class LicenseInfoResponse(BaseModel):
    license_key: str
    type: str
    status: str
    seats: int
    max_devices: int
    device_count: int
    features: List[str]
    issued_at: Optional[str]
    activated_at: Optional[str]
    expires_at: Optional[str]
    trial_ends_at: Optional[str]
    validation: Dict[str, Any]
    activations: List[Dict[str, Any]]


class LicenseValidationResponse(BaseModel):
    valid: bool
    status: str
    message: str
    days_remaining: Optional[int] = None
    grace_period_days: Optional[int] = None


@router.post("/activate", response_model=Dict[str, Any])
async def activate_license(
    request: ActivateLicenseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    http_request: Request = None
):
    """
    Activate a license key on the current device.
    
    Requires authentication. Binds license to hardware fingerprint.
    """
    try:
        # Get hardware fingerprint
        hw = license_manager.get_hardware_fingerprint()
        
        # Get IP and user agent
        ip_address = None
        user_agent = None
        if http_request:
            ip_address = http_request.client.host if http_request.client else None
            user_agent = http_request.headers.get("user-agent")
        
        # Activate license
        license_obj, activation = license_manager.activate_license(
            db=db,
            license_key=request.license_key,
            hardware_fingerprint=hw.fingerprint,
            device_name=request.device_name,
            device_info=request.device_info or {
                "machine_id": hw.machine_id,
                "processor": hw.processor,
                "platform": hw.platform,
                "architecture": hw.architecture
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Associate with user/tenant if not already
        if not license_obj.user_id and current_user:
            license_obj.user_id = current_user.id
        if not license_obj.tenant_id and hasattr(current_user, 'tenant_id'):
            # Try to get tenant from user
            # This would need to be implemented based on your user-tenant relationship
            pass
        
        db.commit()
        
        return {
            "success": True,
            "message": "License activated successfully",
            "license": {
                "key": license_obj.license_key,
                "type": license_obj.license_type.value,
                "status": license_obj.status.value,
                "seats": license_obj.seats,
                "max_devices": license_obj.max_devices,
                "device_count": license_obj.device_count
            },
            "activation": {
                "id": activation.id,
                "device_name": activation.device_name,
                "activated_at": activation.activated_at.isoformat()
            }
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"License activation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate license"
        )


@router.post("/validate", response_model=LicenseValidationResponse)
async def validate_license(
    request: ValidateLicenseRequest,
    db: Session = Depends(get_db)
):
    """
    Validate a license key.
    
    Returns validation status without requiring authentication.
    """
    try:
        # Get hardware fingerprint if available
        hw = license_manager.get_hardware_fingerprint()
        
        validation = license_manager.validate_license(
            db=db,
            license_key=request.license_key,
            hardware_fingerprint=hw.fingerprint
        )
        
        return LicenseValidationResponse(
            valid=validation.valid,
            status=validation.status.value,
            message=validation.message,
            days_remaining=validation.days_remaining,
            grace_period_days=validation.grace_period_days
        )
    
    except Exception as e:
        logger.error(f"License validation error: {e}", exc_info=True)
        return LicenseValidationResponse(
            valid=False,
            status="error",
            message=f"Validation error: {str(e)}"
        )


@router.get("/info/{license_key}", response_model=LicenseInfoResponse)
async def get_license_info(
    license_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed license information.
    
    Requires authentication. Only returns info for licenses associated with current user.
    """
    try:
        info = license_manager.get_license_info(db=db, license_key=license_key)
        
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="License not found"
            )
        
        # Check if user has access to this license
        license_obj = db.query(License).filter(License.license_key == license_key).first()
        if license_obj and license_obj.user_id != current_user.id:
            # Check if user is admin (you may want to add admin check)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return LicenseInfoResponse(**info)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get license info error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get license information"
        )


@router.get("/my-licenses", response_model=List[Dict[str, Any]])
async def get_my_licenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all licenses associated with the current user.
    
    Requires authentication.
    """
    try:
        licenses = db.query(License).filter(License.user_id == current_user.id).all()
        
        result = []
        for license_obj in licenses:
            validation = license_manager.validate_license(db=db, license_key=license_obj.license_key)
            
            result.append({
                "license_key": license_obj.license_key,
                "type": license_obj.license_type.value,
                "status": license_obj.status.value,
                "seats": license_obj.seats,
                "max_devices": license_obj.max_devices,
                "device_count": license_obj.device_count,
                "activated_at": license_obj.activated_at.isoformat() if license_obj.activated_at else None,
                "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else None,
                "trial_ends_at": license_obj.trial_ends_at.isoformat() if license_obj.trial_ends_at else None,
                "valid": validation.valid,
                "message": validation.message,
                "days_remaining": validation.days_remaining
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Get my licenses error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get licenses"
        )


@router.post("/deactivate", response_model=Dict[str, str])
async def deactivate_device(
    license_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deactivate license on current device.
    
    Requires authentication.
    """
    try:
        hw = license_manager.get_hardware_fingerprint()
        
        success = license_manager.deactivate_device(
            db=db,
            license_key=license_key,
            hardware_fingerprint=hw.fingerprint
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="License activation not found on this device"
            )
        
        return {"message": "Device deactivated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate device error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate device"
        )


@router.post("/generate", response_model=Dict[str, Any])
async def generate_license(
    request: GenerateLicenseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a new license key.
    
    Requires admin authentication (you should add admin check).
    """
    try:
        # Map license type string to enum
        license_type_map = {
            "trial": LicenseType.TRIAL,
            "standard": LicenseType.STANDARD,
            "enterprise": LicenseType.ENTERPRISE,
            "perpetual": LicenseType.PERPETUAL
        }
        
        license_type = license_type_map.get(request.license_type.lower(), LicenseType.STANDARD)
        
        # Generate license key
        license_key = license_manager.generate_license_key(
            license_type=license_type,
            seats=request.seats,
            max_devices=request.max_devices,
            trial_days=request.trial_days,
            expiration_days=request.expiration_days,
            features=request.features,
            metadata={}
        )
        
        # Create license record
        license_obj = license_manager.create_license(
            db=db,
            license_key=license_key,
            license_type=license_type,
            tenant_id=request.tenant_id,
            user_id=request.user_id or current_user.id,
            seats=request.seats,
            max_devices=request.max_devices,
            trial_days=request.trial_days,
            expiration_days=request.expiration_days,
            features=request.features,
            metadata={}
        )
        
        return {
            "success": True,
            "license_key": license_key,
            "license_id": license_obj.id,
            "type": license_type.value,
            "seats": request.seats,
            "max_devices": request.max_devices
        }
    
    except Exception as e:
        logger.error(f"Generate license error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate license"
        )


@router.post("/revoke/{license_key}", response_model=Dict[str, str])
async def revoke_license(
    license_key: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Revoke a license.
    
    Requires admin authentication (you should add admin check).
    """
    try:
        license_obj = license_manager.revoke_license(
            db=db,
            license_key=license_key,
            reason=reason
        )
        
        return {
            "message": "License revoked successfully",
            "license_key": license_key,
            "revoked_at": license_obj.revoked_at.isoformat() if license_obj.revoked_at else None
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Revoke license error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke license"
        )


@router.get("/hardware-fingerprint", response_model=Dict[str, str])
async def get_hardware_fingerprint():
    """
    Get hardware fingerprint for current device.
    
    Used for device binding during activation.
    """
    try:
        hw = license_manager.get_hardware_fingerprint()
        return {
            "fingerprint": hw.fingerprint,
            "machine_id": hw.machine_id,
            "processor": hw.processor,
            "platform": hw.platform,
            "architecture": hw.architecture
        }
    except Exception as e:
        logger.error(f"Get hardware fingerprint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get hardware fingerprint"
        )

