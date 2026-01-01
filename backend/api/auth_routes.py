
"""
Authentication and authorization API routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta

from core.security import (
    JWTAuthManager, 
    create_access_token, 
    verify_token,
    rbac_manager,
    Role,
    audit_logger,
    AuditEventType
)
from core.security.user_service import UserService
from database.session import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()
auth_manager = JWTAuthManager()
logger = logging.getLogger(__name__)

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

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    tenant_id: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class EmailVerificationRequest(BaseModel):
    token: str

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    x_forwarded_for: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None)
):
    """
    Authenticate user and return JWT tokens.
    
    Returns access token (30 min) and refresh token (7 days).
    """
    user_service = UserService(db)
    
    # Authenticate user
    user = user_service.authenticate_user(
        email=request.email,
        password=request.password,
        tenant_id=request.tenant_id,
        ip_address=x_forwarded_for,
        user_agent=user_agent
    )
    
    if not user:
        # Log failed authentication (already logged in authenticate_user)
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
            detail="Invalid credentials or account locked"
        )
    
    # Get user roles for tenant
    roles = user_service.get_user_roles(user.id, request.tenant_id)
    
    # If no roles assigned, assign default role
    if not roles:
        default_role = Role.VIEWER
        user_service.assign_user_role(user.id, request.tenant_id, default_role)
        roles = [default_role]
    
    # Generate tokens
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=request.tenant_id,
        roles=roles
    )
    
    # Create refresh token in database
    refresh_token = user_service.create_refresh_token(
        user_id=user.id,
        tenant_id=request.tenant_id,
        ip_address=x_forwarded_for,
        user_agent=user_agent
    )
    
    # Log successful authentication
    await audit_logger.log(
        event_type=AuditEventType.AUTH_LOGIN,
        user_id=user.id,
        tenant_id=request.tenant_id,
        resource_type="auth",
        resource_id=user.id,
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
async def refresh_token_endpoint(
    request: RefreshRequest,
    db: Session = Depends(get_db),
    x_forwarded_for: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None)
):
    """
    Refresh access token using refresh token.
    
    Implements refresh token rotation for security:
    - Old refresh token is revoked
    - New refresh token is issued
    - Prevents token reuse attacks
    """
    from core.security.jwt_auth import auth_manager
    
    user_service = UserService(db)
    
    # Get refresh token from database
    refresh_token_obj = user_service.get_refresh_token(request.refresh_token)
    
    if not refresh_token_obj or refresh_token_obj.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = refresh_token_obj.user_id
    tenant_id = refresh_token_obj.tenant_id
    
    # Verify token using JWT auth manager
    payload = auth_manager.verify_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user's current roles
    roles = user_service.get_user_roles(user_id, tenant_id)
    
    # Generate new tokens with refresh token rotation
    token_result = auth_manager.refresh_access_token(
        refresh_token=request.refresh_token,
        roles=roles,
        rotate_refresh_token=True  # Enable rotation for security
    )
    
    if not token_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token"
        )
    
    # Revoke old refresh token in database
    user_service.revoke_refresh_token(request.refresh_token)
    
    new_refresh_token = token_result.get("refresh_token")
    if new_refresh_token:
        user_service.store_refresh_token(
            token=new_refresh_token,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=x_forwarded_for,
            user_agent=user_agent,
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
        access_token=token_result["access_token"],
        refresh_token=new_refresh_token or user_service.create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=x_forwarded_for,
            user_agent=user_agent,
        )
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
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    logout_all_devices: bool = False
):
    """
    Logout user and revoke tokens.
    
    Args:
        logout_all_devices: If True, revoke all tokens for user (logout from all devices)
                          If False, revoke only the current access token
    """
    from core.security.jwt_auth import auth_manager
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload:
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        
        # Revoke the current access token
        auth_manager.revoke_token(token)
        
        user_service = UserService(db)
        
        if logout_all_devices:
            # Revoke all refresh tokens for this user (logout from all devices)
            user_service.revoke_all_user_tokens(user_id)
            auth_manager.revoke_all_user_tokens(user_id, tenant_id)
        else:
            # Just revoke the current access token (already done above)
            # Optionally, can also revoke the refresh token if provided
            pass
        
        # Log logout
        await audit_logger.log(
            event_type=AuditEventType.AUTH_LOGOUT,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="auth",
            resource_id=user_id,
            action="logout",
            outcome="success",
            metadata={"logout_all_devices": logout_all_devices}
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


@router.post("/signup")
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    Creates user account and sends email verification.
    """
    user_service = UserService(db)
    
    try:
        # Create user
        user = user_service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            company_name=request.company_name,
            job_title=request.job_title
        )
        
        # Assign default role (VIEWER) to tenant
        user_service.assign_user_role(user.id, request.tenant_id, Role.VIEWER)
        
        # Create email verification token
        verification = user_service.create_email_verification_token(
            user_id=user.id,
            email=user.email
        )
        
        # Send verification email
        try:
            from core.services.email_service import get_email_service
            from core.services.email_templates import EmailTemplates
            from config.settings import settings
            
            email_service = get_email_service()
            verification_url = f"{settings.frontend_url}/verify-email?token={verification.token}"
            template = EmailTemplates.verification_email(
                verification_url=verification_url,
                user_name=user.full_name or user.email
            )
            
            await email_service.send_email(
                to_email=user.email,
                subject=template["subject"],
                html_content=template["html"],
                text_content=template["text"]
            )
            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}", exc_info=True)
            # Don't fail signup if email fails, but log it
        
        # Log signup
        await audit_logger.log(
            event_type=AuditEventType.AUTH_SIGNUP,
            user_id=user.id,
            tenant_id=request.tenant_id,
            resource_type="auth",
            resource_id=user.id,
            action="signup",
            outcome="success"
        )
        
        return {
            "message": "User created successfully. Please check your email to verify your account.",
            "user_id": user.id
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/verify-email")
async def verify_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify user email address using verification token.
    """
    user_service = UserService(db)
    
    user = user_service.verify_email(request.token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Log email verification
    await audit_logger.log(
        event_type=AuditEventType.SECURITY_POLICY_CHANGE,
        user_id=user.id,
        tenant_id="system",
        resource_type="user",
        resource_id=user.id,
        action="email_verified",
        outcome="success"
    )
    
    return {
        "message": "Email verified successfully",
        "user_id": user.id
    }


@router.post("/reset-password-request")
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset. Sends reset token to user's email.
    """
    user_service = UserService(db)
    
    user = user_service.get_user_by_email(request.email)
    
    if user:
        # Create password reset token
        reset = user_service.create_password_reset_token(user.id)
        
        # Send password reset email
        try:
            from core.services.email_service import get_email_service
            from core.services.email_templates import EmailTemplates
            from config.settings import settings
            
            email_service = get_email_service()
            reset_url = f"{settings.frontend_url}/reset-password?token={reset.token}"
            template = EmailTemplates.password_reset_email(
                reset_url=reset_url,
                user_name=user.full_name or user.email
            )
            
            await email_service.send_email(
                to_email=user.email,
                subject=template["subject"],
                html_content=template["html"],
                text_content=template["text"]
            )
            logger.info(f"Password reset email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}", exc_info=True)
        
        # Log password reset request
        await audit_logger.log(
            event_type=AuditEventType.SECURITY_POLICY_CHANGE,
            user_id=user.id,
            tenant_id="system",
            resource_type="auth",
            resource_id=user.id,
            action="password_reset_requested",
            outcome="success"
        )
    
    # Always return success to prevent email enumeration
    return {
        "message": "If the email exists, a password reset link has been sent."
    }


@router.post("/reset-password")
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token.
    """
    user_service = UserService(db)
    
    user = user_service.reset_password(request.token, request.new_password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Revoke all existing refresh tokens (force re-login)
    user_service.revoke_all_user_tokens(user.id)
    
    # Log password reset
    await audit_logger.log(
        event_type=AuditEventType.SECURITY_POLICY_CHANGE,
        user_id=user.id,
        tenant_id="system",
        resource_type="auth",
        resource_id=user.id,
        action="password_reset",
        outcome="success"
    )
    
    return {
        "message": "Password reset successfully. Please login with your new password.",
        "user_id": user.id
    }
