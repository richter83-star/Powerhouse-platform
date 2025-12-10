"""
White-Label API Routes

Handles white-label branding configuration for enterprise customers.
Enterprise-only feature.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import User
from api.auth import get_current_user
from core.commercial.white_label_service import WhiteLabelService
from core.commercial.tenant_manager import get_tenant_manager, TenantTier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/whitelabel", tags=["White-Label"])

# Request/Response Models
class WhiteLabelConfigRequest(BaseModel):
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    secondary_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    accent_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    custom_domain: Optional[str] = None
    custom_subdomain: Optional[str] = None
    company_name: Optional[str] = None
    product_name: Optional[str] = None
    tagline: Optional[str] = None
    email_from_name: Optional[str] = None
    email_from_address: Optional[str] = None
    hide_powered_by: bool = False
    custom_css: Optional[str] = None
    custom_footer: Optional[str] = None
    is_active: bool = True


class WhiteLabelConfigResponse(BaseModel):
    id: str
    tenant_id: str
    logo_url: Optional[str]
    favicon_url: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    accent_color: Optional[str]
    custom_domain: Optional[str]
    custom_subdomain: Optional[str]
    company_name: Optional[str]
    product_name: Optional[str]
    tagline: Optional[str]
    email_from_name: Optional[str]
    email_from_address: Optional[str]
    hide_powered_by: bool
    is_active: bool
    created_at: str
    updated_at: str


@router.get("/config", response_model=Dict[str, Any])
async def get_branding(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get branding configuration for current tenant.
    
    Returns default branding if white-label not configured.
    """
    try:
        tenant_id = getattr(current_user, 'tenant_id', None) or "default"
        white_label_service = WhiteLabelService(db)
        
        branding = white_label_service.get_branding_for_tenant(tenant_id)
        
        return branding
    except Exception as e:
        logger.error(f"Get branding error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get branding"
        )


@router.get("/config/admin", response_model=WhiteLabelConfigResponse)
async def get_whitelabel_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get white-label configuration (admin only).
    
    Requires Enterprise tier.
    """
    try:
        tenant_id = getattr(current_user, 'tenant_id', None) or "default"
        
        # Check if tenant is Enterprise tier
        tenant_manager = get_tenant_manager()
        tenant = tenant_manager.get_tenant(tenant_id)
        
        if not tenant or tenant.tier != TenantTier.ENTERPRISE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="White-label is only available for Enterprise tier"
            )
        
        white_label_service = WhiteLabelService(db)
        config = white_label_service.get_config(tenant_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="White-label configuration not found"
            )
        
        return WhiteLabelConfigResponse(
            id=config.id,
            tenant_id=config.tenant_id,
            logo_url=config.logo_url,
            favicon_url=config.favicon_url,
            primary_color=config.primary_color,
            secondary_color=config.secondary_color,
            accent_color=config.accent_color,
            custom_domain=config.custom_domain,
            custom_subdomain=config.custom_subdomain,
            company_name=config.company_name,
            product_name=config.product_name,
            tagline=config.tagline,
            email_from_name=config.email_from_name,
            email_from_address=config.email_from_address,
            hide_powered_by=config.hide_powered_by,
            is_active=config.is_active,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get white-label config error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get white-label configuration"
        )


@router.post("/config", response_model=WhiteLabelConfigResponse)
async def update_whitelabel_config(
    request: WhiteLabelConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create or update white-label configuration.
    
    Requires Enterprise tier.
    """
    try:
        tenant_id = getattr(current_user, 'tenant_id', None) or "default"
        
        # Check if tenant is Enterprise tier
        tenant_manager = get_tenant_manager()
        tenant = tenant_manager.get_tenant(tenant_id)
        
        if not tenant or tenant.tier != TenantTier.ENTERPRISE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="White-label is only available for Enterprise tier"
            )
        
        white_label_service = WhiteLabelService(db)
        config = white_label_service.create_or_update_config(
            tenant_id=tenant_id,
            logo_url=request.logo_url,
            favicon_url=request.favicon_url,
            primary_color=request.primary_color,
            secondary_color=request.secondary_color,
            accent_color=request.accent_color,
            custom_domain=request.custom_domain,
            custom_subdomain=request.custom_subdomain,
            company_name=request.company_name,
            product_name=request.product_name,
            tagline=request.tagline,
            email_from_name=request.email_from_name,
            email_from_address=request.email_from_address,
            hide_powered_by=request.hide_powered_by,
            custom_css=request.custom_css,
            custom_footer=request.custom_footer,
            is_active=request.is_active
        )
        
        return WhiteLabelConfigResponse(
            id=config.id,
            tenant_id=config.tenant_id,
            logo_url=config.logo_url,
            favicon_url=config.favicon_url,
            primary_color=config.primary_color,
            secondary_color=config.secondary_color,
            accent_color=config.accent_color,
            custom_domain=config.custom_domain,
            custom_subdomain=config.custom_subdomain,
            company_name=config.company_name,
            product_name=config.product_name,
            tagline=config.tagline,
            email_from_name=config.email_from_name,
            email_from_address=config.email_from_address,
            hide_powered_by=config.hide_powered_by,
            is_active=config.is_active,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update white-label config error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update white-label configuration"
        )

