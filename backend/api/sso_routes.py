"""
SSO/SAML API Routes

Handles SSO authentication via SAML 2.0 and OAuth providers.
Enterprise-only feature.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import User
from api.auth import get_current_user
from core.auth.saml_service import get_saml_service
from core.auth.oauth_service import get_oauth_service, OAuthProvider
from core.commercial.tenant_manager import get_tenant_manager, TenantTier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sso", tags=["SSO"])

# Request/Response Models
class SAMLConfigRequest(BaseModel):
    entity_id: str
    sso_url: str
    x509_cert: str
    attribute_mapping: Optional[Dict[str, str]] = None


class OAuthConfigRequest(BaseModel):
    provider: str = Field(..., description="OAuth provider: google, microsoft, okta, generic")
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: Optional[list] = None
    auth_base_url: Optional[str] = None  # For generic OAuth
    okta_domain: Optional[str] = None  # For Okta


@router.post("/saml/configure")
async def configure_saml(
    request: SAMLConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Configure SAML 2.0 SSO for tenant.
    
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
                detail="SAML SSO is only available for Enterprise tier"
            )
        
        saml_service = get_saml_service()
        config = saml_service.configure_saml(
            tenant_id=tenant_id,
            entity_id=request.entity_id,
            sso_url=request.sso_url,
            x509_cert=request.x509_cert,
            attribute_mapping=request.attribute_mapping
        )
        
        return {
            "message": "SAML configured successfully",
            "config": config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Configure SAML error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure SAML"
        )


@router.get("/saml/request")
async def get_saml_request(
    relay_state: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate SAML authentication request.
    """
    try:
        tenant_id = getattr(current_user, 'tenant_id', None) or "default"
        
        saml_service = get_saml_service()
        saml_request = saml_service.generate_saml_request(tenant_id, relay_state)
        
        return saml_request
    except Exception as e:
        logger.error(f"Get SAML request error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate SAML request"
        )


@router.post("/oauth/configure")
async def configure_oauth(
    request: OAuthConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Configure OAuth SSO for tenant.
    
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
                detail="OAuth SSO is only available for Enterprise tier"
            )
        
        oauth_service = get_oauth_service()
        config = oauth_service.configure_oauth(
            tenant_id=tenant_id,
            provider=request.provider,
            client_id=request.client_id,
            client_secret=request.client_secret,
            redirect_uri=request.redirect_uri,
            scopes=request.scopes
        )
        
        return {
            "message": "OAuth configured successfully",
            "config": config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Configure OAuth error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure OAuth"
        )


@router.get("/oauth/authorize")
async def get_oauth_authorization_url(
    state: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get OAuth authorization URL.
    """
    try:
        tenant_id = getattr(current_user, 'tenant_id', None) or "default"
        
        oauth_service = get_oauth_service()
        auth_data = oauth_service.get_authorization_url(tenant_id, state)
        
        return auth_data
    except Exception as e:
        logger.error(f"Get OAuth authorization URL error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get OAuth authorization URL"
        )


@router.post("/oauth/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State parameter"),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback and create/update user.
    """
    try:
        # Extract tenant_id from state (in production, encode it in state)
        tenant_id = "default"  # This should be extracted from state
        
        oauth_service = get_oauth_service()
        token_data = await oauth_service.exchange_code_for_token(tenant_id, code, state)
        user_info = await oauth_service.get_user_info(tenant_id, token_data["access_token"])
        
        # Create or update user (just-in-time provisioning)
        from core.security.user_service import UserService
        user_service = UserService(db)
        
        user = user_service.get_user_by_email(user_info["email"])
        if not user:
            # Create new user
            user = user_service.create_user(
                email=user_info["email"],
                password="",  # No password for SSO users
                full_name=user_info.get("name")
            )
        
        # Generate JWT token
        from core.security.jwt_auth import create_access_token
        token = create_access_token(
            user_id=user.id,
            tenant_id=tenant_id,
            roles=[]
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name
            }
        }
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process OAuth callback"
        )

