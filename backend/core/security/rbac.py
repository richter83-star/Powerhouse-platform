
"""
Role-Based Access Control (RBAC) system for multi-tenant authorization.
"""
from enum import Enum
from typing import List, Set, Optional, Callable
from functools import wraps
from datetime import datetime
import json

class Permission(Enum):
    """System permissions"""
    # Agent Management
    AGENT_VIEW = "agent:view"
    AGENT_CREATE = "agent:create"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_EXECUTE = "agent:execute"
    
    # Workflow Management
    WORKFLOW_VIEW = "workflow:view"
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_UPDATE = "workflow:update"
    WORKFLOW_DELETE = "workflow:delete"
    WORKFLOW_EXECUTE = "workflow:execute"
    
    # Configuration Management
    CONFIG_VIEW = "config:view"
    CONFIG_UPDATE = "config:update"
    
    # System Administration
    SYSTEM_ADMIN = "system:admin"
    USER_MANAGE = "user:manage"
    TENANT_MANAGE = "tenant:manage"
    
    # Audit & Monitoring
    AUDIT_VIEW = "audit:view"
    METRICS_VIEW = "metrics:view"
    
    # Plugin Management
    PLUGIN_VIEW = "plugin:view"
    PLUGIN_INSTALL = "plugin:install"
    PLUGIN_MANAGE = "plugin:manage"

class Role(Enum):
    """Predefined system roles"""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    VIEWER = "viewer"
    API_USER = "api_user"

class RBACManager:
    """
    Manages role-based access control with multi-tenant isolation.
    
    Features:
    - Role hierarchy and inheritance
    - Permission checking
    - Multi-tenant isolation
    - Dynamic role assignment
    """
    
    def __init__(self):
        """Initialize RBAC manager with role-permission mappings"""
        self.role_permissions = {
            Role.SUPER_ADMIN: self._get_all_permissions(),
            Role.TENANT_ADMIN: {
                Permission.AGENT_VIEW, Permission.AGENT_CREATE, Permission.AGENT_UPDATE,
                Permission.AGENT_DELETE, Permission.AGENT_EXECUTE,
                Permission.WORKFLOW_VIEW, Permission.WORKFLOW_CREATE, Permission.WORKFLOW_UPDATE,
                Permission.WORKFLOW_DELETE, Permission.WORKFLOW_EXECUTE,
                Permission.CONFIG_VIEW, Permission.CONFIG_UPDATE,
                Permission.USER_MANAGE,
                Permission.AUDIT_VIEW, Permission.METRICS_VIEW,
                Permission.PLUGIN_VIEW, Permission.PLUGIN_INSTALL, Permission.PLUGIN_MANAGE
            },
            Role.DEVELOPER: {
                Permission.AGENT_VIEW, Permission.AGENT_CREATE, Permission.AGENT_UPDATE,
                Permission.AGENT_EXECUTE,
                Permission.WORKFLOW_VIEW, Permission.WORKFLOW_CREATE, Permission.WORKFLOW_UPDATE,
                Permission.WORKFLOW_EXECUTE,
                Permission.CONFIG_VIEW,
                Permission.METRICS_VIEW,
                Permission.PLUGIN_VIEW, Permission.PLUGIN_INSTALL
            },
            Role.OPERATOR: {
                Permission.AGENT_VIEW, Permission.AGENT_EXECUTE,
                Permission.WORKFLOW_VIEW, Permission.WORKFLOW_EXECUTE,
                Permission.CONFIG_VIEW,
                Permission.METRICS_VIEW,
                Permission.PLUGIN_VIEW
            },
            Role.VIEWER: {
                Permission.AGENT_VIEW,
                Permission.WORKFLOW_VIEW,
                Permission.CONFIG_VIEW,
                Permission.METRICS_VIEW,
                Permission.AUDIT_VIEW
            },
            Role.API_USER: {
                Permission.AGENT_VIEW, Permission.AGENT_EXECUTE,
                Permission.WORKFLOW_VIEW, Permission.WORKFLOW_EXECUTE
            }
        }
        
        # User-role-tenant mappings (in production, this would be in a database)
        self.user_roles = {}  # {user_id: {tenant_id: [roles]}}
        
    def _get_all_permissions(self) -> Set[Permission]:
        """Get all available permissions"""
        return set(Permission)
    
    def assign_role(self, user_id: str, tenant_id: str, role: Role):
        """Assign a role to a user within a tenant"""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = {}
        if tenant_id not in self.user_roles[user_id]:
            self.user_roles[user_id][tenant_id] = []
        
        if role not in self.user_roles[user_id][tenant_id]:
            self.user_roles[user_id][tenant_id].append(role)
    
    def remove_role(self, user_id: str, tenant_id: str, role: Role):
        """Remove a role from a user within a tenant"""
        if (user_id in self.user_roles and 
            tenant_id in self.user_roles[user_id] and 
            role in self.user_roles[user_id][tenant_id]):
            self.user_roles[user_id][tenant_id].remove(role)
    
    def get_user_roles(self, user_id: str, tenant_id: str) -> List[Role]:
        """Get all roles for a user in a specific tenant"""
        if user_id in self.user_roles and tenant_id in self.user_roles[user_id]:
            return self.user_roles[user_id][tenant_id]
        return []
    
    def get_user_permissions(self, user_id: str, tenant_id: str) -> Set[Permission]:
        """Get all permissions for a user in a specific tenant"""
        roles = self.get_user_roles(user_id, tenant_id)
        permissions = set()
        for role in roles:
            permissions.update(self.role_permissions.get(role, set()))
        return permissions
    
    def has_permission(self, user_id: str, tenant_id: str, permission: Permission) -> bool:
        """Check if a user has a specific permission in a tenant"""
        user_permissions = self.get_user_permissions(user_id, tenant_id)
        return permission in user_permissions
    
    def has_any_permission(self, user_id: str, tenant_id: str, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        user_permissions = self.get_user_permissions(user_id, tenant_id)
        return any(perm in user_permissions for perm in permissions)
    
    def has_all_permissions(self, user_id: str, tenant_id: str, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions"""
        user_permissions = self.get_user_permissions(user_id, tenant_id)
        return all(perm in user_permissions for perm in permissions)
    
    def is_tenant_admin(self, user_id: str, tenant_id: str) -> bool:
        """Check if user is an admin for a specific tenant"""
        roles = self.get_user_roles(user_id, tenant_id)
        return Role.SUPER_ADMIN in roles or Role.TENANT_ADMIN in roles
    
    def get_accessible_tenants(self, user_id: str) -> List[str]:
        """Get all tenants a user has access to"""
        if user_id in self.user_roles:
            return list(self.user_roles[user_id].keys())
        return []

# Global RBAC manager instance
rbac_manager = RBACManager()

def require_permission(permission: Permission, tenant_id_param: str = "tenant_id"):
    """
    Decorator to require a specific permission for an endpoint.
    
    Args:
        permission: Required permission
        tenant_id_param: Name of the parameter containing tenant_id
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id and tenant_id from request context
            # In production, these would come from JWT token
            user_id = kwargs.get('user_id') or getattr(args[0] if args else None, 'user_id', 'default_user')
            tenant_id = kwargs.get(tenant_id_param, 'default_tenant')
            
            if not rbac_manager.has_permission(user_id, tenant_id, permission):
                raise PermissionError(
                    f"User {user_id} lacks permission {permission.value} in tenant {tenant_id}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_any_permission(*permissions: Permission, tenant_id_param: str = "tenant_id"):
    """Decorator to require any of the specified permissions"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id') or getattr(args[0] if args else None, 'user_id', 'default_user')
            tenant_id = kwargs.get(tenant_id_param, 'default_tenant')
            
            if not rbac_manager.has_any_permission(user_id, tenant_id, list(permissions)):
                raise PermissionError(
                    f"User {user_id} lacks required permissions in tenant {tenant_id}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role: Role, tenant_id_param: str = "tenant_id"):
    """Decorator to require a specific role"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id') or getattr(args[0] if args else None, 'user_id', 'default_user')
            tenant_id = kwargs.get(tenant_id_param, 'default_tenant')
            
            roles = rbac_manager.get_user_roles(user_id, tenant_id)
            if role not in roles:
                raise PermissionError(
                    f"User {user_id} lacks required role {role.value} in tenant {tenant_id}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
