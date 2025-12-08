
"""
Multi-Tenancy Manager
Provides tenant isolation, resource allocation, and tenant-specific configurations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import asyncio
from dataclasses import dataclass, field
import json

class TenantTier(str, Enum):
    """Subscription tiers for tenants"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

@dataclass
class TenantConfig:
    """Configuration for a single tenant"""
    tenant_id: str
    name: str
    tier: TenantTier
    created_at: datetime
    max_agents: int
    max_workflows: int
    max_api_calls_per_hour: int
    storage_limit_gb: int
    features: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

class TenantManager:
    """Manages multi-tenant operations and isolation"""
    
    def __init__(self):
        self._tenants: Dict[str, TenantConfig] = {}
        self._tier_configs = {
            TenantTier.FREE: {
                "max_agents": 3,
                "max_workflows": 5,
                "max_api_calls_per_hour": 100,
                "storage_limit_gb": 1,
                "features": ["basic_agents", "simple_workflows"]
            },
            TenantTier.STARTER: {
                "max_agents": 10,
                "max_workflows": 20,
                "max_api_calls_per_hour": 1000,
                "storage_limit_gb": 10,
                "features": ["basic_agents", "simple_workflows", "integrations", "basic_analytics"]
            },
            TenantTier.PROFESSIONAL: {
                "max_agents": 50,
                "max_workflows": 100,
                "max_api_calls_per_hour": 10000,
                "storage_limit_gb": 100,
                "features": ["all_agents", "advanced_workflows", "integrations", "analytics", "custom_plugins"]
            },
            TenantTier.ENTERPRISE: {
                "max_agents": -1,  # unlimited
                "max_workflows": -1,
                "max_api_calls_per_hour": -1,
                "storage_limit_gb": -1,
                "features": ["all_agents", "advanced_workflows", "integrations", "analytics", "custom_plugins", "white_label", "sso", "dedicated_support"]
            }
        }
    
    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        tier: TenantTier = TenantTier.FREE,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TenantConfig:
        """Create a new tenant"""
        if tenant_id in self._tenants:
            raise ValueError(f"Tenant {tenant_id} already exists")
        
        tier_config = self._tier_configs[tier]
        tenant = TenantConfig(
            tenant_id=tenant_id,
            name=name,
            tier=tier,
            created_at=datetime.utcnow(),
            max_agents=tier_config["max_agents"],
            max_workflows=tier_config["max_workflows"],
            max_api_calls_per_hour=tier_config["max_api_calls_per_hour"],
            storage_limit_gb=tier_config["storage_limit_gb"],
            features=tier_config["features"].copy(),
            metadata=metadata or {},
            is_active=True
        )
        
        self._tenants[tenant_id] = tenant
        return tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant configuration"""
        return self._tenants.get(tenant_id)
    
    def update_tenant_tier(self, tenant_id: str, new_tier: TenantTier) -> TenantConfig:
        """Upgrade or downgrade tenant tier"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        tier_config = self._tier_configs[new_tier]
        tenant.tier = new_tier
        tenant.max_agents = tier_config["max_agents"]
        tenant.max_workflows = tier_config["max_workflows"]
        tenant.max_api_calls_per_hour = tier_config["max_api_calls_per_hour"]
        tenant.storage_limit_gb = tier_config["storage_limit_gb"]
        tenant.features = tier_config["features"].copy()
        
        return tenant
    
    def check_feature_access(self, tenant_id: str, feature: str) -> bool:
        """Check if tenant has access to a specific feature"""
        tenant = self.get_tenant(tenant_id)
        if not tenant or not tenant.is_active:
            return False
        return feature in tenant.features
    
    def check_resource_limit(
        self,
        tenant_id: str,
        resource_type: str,
        current_count: int
    ) -> bool:
        """Check if tenant is within resource limits"""
        tenant = self.get_tenant(tenant_id)
        if not tenant or not tenant.is_active:
            return False
        
        limits = {
            "agents": tenant.max_agents,
            "workflows": tenant.max_workflows,
            "api_calls": tenant.max_api_calls_per_hour,
            "storage_gb": tenant.storage_limit_gb
        }
        
        limit = limits.get(resource_type, 0)
        if limit == -1:  # unlimited
            return True
        return current_count < limit
    
    def list_tenants(self, active_only: bool = True) -> List[TenantConfig]:
        """List all tenants"""
        tenants = list(self._tenants.values())
        if active_only:
            tenants = [t for t in tenants if t.is_active]
        return tenants
    
    def deactivate_tenant(self, tenant_id: str) -> None:
        """Deactivate a tenant (soft delete)"""
        tenant = self.get_tenant(tenant_id)
        if tenant:
            tenant.is_active = False
    
    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant statistics"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return {}
        
        return {
            "tenant_id": tenant.tenant_id,
            "name": tenant.name,
            "tier": tenant.tier.value,
            "created_at": tenant.created_at.isoformat(),
            "is_active": tenant.is_active,
            "limits": {
                "max_agents": tenant.max_agents,
                "max_workflows": tenant.max_workflows,
                "max_api_calls_per_hour": tenant.max_api_calls_per_hour,
                "storage_limit_gb": tenant.storage_limit_gb
            },
            "features": tenant.features,
            "metadata": tenant.metadata
        }

# Singleton instance
_tenant_manager = TenantManager()

def get_tenant_manager() -> TenantManager:
    """Get the global tenant manager instance"""
    return _tenant_manager
