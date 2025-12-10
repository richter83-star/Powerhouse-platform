"""
MFA Enforcement Service

Enforces multi-factor authentication based on subscription tier.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models import User
from core.commercial.tenant_manager import get_tenant_manager, TenantTier

logger = logging.getLogger(__name__)


class MFAEnforcementService:
    """
    MFA enforcement service.
    
    Features:
    - Tier-based MFA requirements
    - MFA status checking
    - Enforcement policies
    """
    
    # MFA requirements by tier
    TIER_MFA_REQUIREMENTS = {
        TenantTier.FREE: False,  # MFA optional
        TenantTier.STARTER: False,  # MFA optional
        TenantTier.PROFESSIONAL: True,  # MFA required
        TenantTier.ENTERPRISE: True  # MFA required
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def is_mfa_required(self, tenant_id: str) -> bool:
        """
        Check if MFA is required for tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            True if MFA is required
        """
        tenant_manager = get_tenant_manager()
        tenant = tenant_manager.get_tenant(tenant_id)
        
        if not tenant:
            return False
        
        return self.TIER_MFA_REQUIREMENTS.get(tenant.tier, False)
    
    def check_mfa_status(self, user_id: str) -> Dict[str, Any]:
        """
        Check MFA status for user.
        
        Args:
            user_id: User ID
            
        Returns:
            MFA status dict
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "mfa_enabled": False,
                "mfa_required": False,
                "mfa_compliant": False
            }
        
        tenant_id = getattr(user, 'tenant_id', None) or "default"
        mfa_required = self.is_mfa_required(tenant_id)
        
        # Check if user has MFA enabled (this would check MFA settings)
        # For now, assume MFA is not enabled unless stored in user metadata
        mfa_enabled = getattr(user, 'mfa_enabled', False) or False
        
        return {
            "mfa_enabled": mfa_enabled,
            "mfa_required": mfa_required,
            "mfa_compliant": mfa_enabled if mfa_required else True
        }
    
    def enforce_mfa(self, user_id: str) -> bool:
        """
        Check if user can proceed without MFA.
        
        Args:
            user_id: User ID
            
        Returns:
            True if user can proceed, False if MFA is required
        """
        status = self.check_mfa_status(user_id)
        
        if status["mfa_required"] and not status["mfa_enabled"]:
            return False
        
        return True

