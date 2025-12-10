
"""
Security module for enterprise authentication, authorization, and encryption.
"""
from .rbac import RBACManager, require_permission, Role, Permission
from .jwt_auth import JWTAuthManager, create_access_token, verify_token
from .encryption import EncryptionService
from .audit_log import AuditLogger, AuditEventType, AuditSeverity

# Import rbac_manager if available
try:
    from .rbac import rbac_manager
except ImportError:
    rbac_manager = None

# Import create_refresh_token if available
try:
    from .jwt_auth import create_refresh_token
except ImportError:
    create_refresh_token = None

# Import audit_logger instance if available
try:
    from .audit_log import audit_logger
except ImportError:
    audit_logger = None

__all__ = [
    'RBACManager',
    'require_permission',
    'Role',
    'Permission',
    'JWTAuthManager',
    'create_access_token',
    'create_refresh_token',
    'verify_token',
    'EncryptionService',
    'AuditLogger',
    'audit_logger',
    'AuditEventType',
    'AuditSeverity',
    'rbac_manager'
]
