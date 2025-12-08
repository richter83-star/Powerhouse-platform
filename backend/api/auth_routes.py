
"""
Authentication and authorization API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta

from core.security import (
    JWTAuthManager, 
    create_access_token, 
    create_refresh_token,
    verify_token,
    rbac_manager,
    Role,
    audit_logger,
    AuditEventType
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()
auth_manager = JWTAuthManager()

# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenVerifyRequest(BaseModel):
    token: str

class RoleAssignRequest(BaseModel):
    user_id: str
    tenant_id: str
    role: str

# In production, this would query a real user database
MOCK_USERS = {
    "admin@powerhouse.ai": {
        "user_id": "user_admin",
        "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "admin123"
        "default_tenant": "default_tenant",
        "default_roles": [Role.SUPER_ADMIN]
    },
    "developer@powerhouse.ai": {
        "user_id": "user_dev",
        "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "default_tenant": "default_tenant",
        "default_roles": [Role.DEVELOPER]
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password (simplified for demo)"""
    # In production, use proper bcrypt verification
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    x_forwarded_for: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None)
):
    """
    Authenticate user and return JWT tokens.
    
    Returns access token (30 min) and refresh token (7 days).
    """
    user = MOCK_USERS.get(request.email)
    
    if not user or not verify_password(request.password, user["password_hash"]):
        # Log failed authentication
        await audit_logger.log(
            event_type=AuditEventType.AUTH_FAILED,
            user_id=request.email,
            tenant_id=request.tenant_id,
            resource_type="auth",
            resource_id=request.email,
            action="login",
            outcome="failure",
            ip_address=x_forwarded_for,
            user_agent=user_agent
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Assign default roles to user
    for role in user["default_roles"]:
        rbac_manager.assign_role(user["user_id"], request.tenant_id, role)
    
    # Generate tokens
    access_token = create_access_token(
        user_id=user["user_id"],
        tenant_id=request.tenant_id,
        roles=user["default_roles"]
    )
    
    refresh_token = create_refresh_token(
        user_id=user["user_id"],
        tenant_id=request.tenant_id
    )
    
    # Log successful authentication
    await audit_logger.log(
        event_type=AuditEventType.AUTH_LOGIN,
        user_id=user["user_id"],
        tenant_id=request.tenant_id,
        resource_type="auth",
        resource_id=user["user_id"],
        action="login",
        outcome="success",
        ip_address=x_forwarded_for,
        user_agent=user_agent
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token_endpoint(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    """
    payload = verify_token(request.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    
    # Get user's current roles
    roles = rbac_manager.get_user_roles(user_id, tenant_id)
    
    # Generate new access token
    access_token = create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=roles
    )
    
    # Log token refresh
    await audit_logger.log(
        event_type=AuditEventType.AUTH_TOKEN_REFRESH,
        user_id=user_id,
        tenant_id=tenant_id,
        resource_type="auth",
        resource_id=user_id,
        action="refresh",
        outcome="success"
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=request.refresh_token
    )

@router.post("/verify")
async def verify_token_endpoint(
    request: TokenVerifyRequest
):
    """
    Verify if a token is valid.
    """
    payload = verify_token(request.token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return {
        "valid": True,
        "user_id": payload.get("sub"),
        "tenant_id": payload.get("tenant_id"),
        "roles": payload.get("roles"),
        "expires_at": payload.get("exp")
    }

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user and revoke token.
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload:
        # Revoke the token
        auth_manager.revoke_token(token)
        
        # Log logout
        await audit_logger.log(
            event_type=AuditEventType.AUTH_LOGOUT,
            user_id=payload.get("sub"),
            tenant_id=payload.get("tenant_id"),
            resource_type="auth",
            resource_id=payload.get("sub"),
            action="logout",
            outcome="success"
        )
    
    return {"message": "Successfully logged out"}

@router.post("/assign-role")
async def assign_role(
    request: RoleAssignRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Assign a role to a user (requires admin privileges).
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Check if requester is admin
    requester_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    
    if not rbac_manager.is_tenant_admin(requester_id, tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Assign role
    try:
        role = Role(request.role)
        rbac_manager.assign_role(request.user_id, request.tenant_id, role)
        
        # Log role assignment
        await audit_logger.log(
            event_type=AuditEventType.SECURITY_POLICY_CHANGE,
            user_id=requester_id,
            tenant_id=tenant_id,
            resource_type="role",
            resource_id=request.user_id,
            action="assign",
            outcome="success",
            metadata={"role": request.role}
        )
        
        return {"message": f"Role {request.role} assigned to user {request.user_id}"}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {request.role}"
        )

@router.get("/permissions")
async def get_permissions(
    tenant_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get permissions for the authenticated user.
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    permissions = rbac_manager.get_user_permissions(user_id, tenant_id)
    
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "permissions": [p.value for p in permissions]
    }
