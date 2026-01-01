"""
User service for database-backed authentication.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid
import secrets
import hashlib
from passlib.context import CryptContext

from database.models import User, RefreshToken, LoginAttempt, UserTenant, EmailVerification, PasswordReset
from core.security.rbac import Role
from core.security.jwt_auth import create_refresh_token as create_refresh_jwt, auth_manager, REFRESH_TOKEN_EXPIRE_DAYS
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Account lockout configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class UserService:
    """Service for user management and authentication."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        company_name: Optional[str] = None,
        job_title: Optional[str] = None
    ) -> User:
        """
        Create a new user.
        
        Args:
            email: User email address
            password: Plain text password (will be hashed)
            full_name: User's full name
            company_name: Company name
            job_title: Job title
            
        Returns:
            User: Created user object
        """
        # Check if user already exists
        existing = self.get_user_by_email(email)
        if existing:
            raise ValueError(f"User with email {email} already exists")
        
        # Hash password
        password_hash = pwd_context.hash(password)
        
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=email.lower().strip(),
            password_hash=password_hash,
            full_name=full_name,
            company_name=company_name,
            job_title=job_title,
            is_active=1,
            is_verified=0,  # Email verification required
            is_locked=0,
            failed_login_attempts=0
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Created user: {user.email} ({user.id})")
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return self.db.query(User).filter(
            User.email == email.lower().strip()
        ).first()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def authenticate_user(
        self,
        email: str,
        password: str,
        tenant_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[User]:
        """
        Authenticate a user.
        
        Returns:
            User if authentication successful, None otherwise
        """
        user = self.get_user_by_email(email)
        
        # Record login attempt
        attempt = LoginAttempt(
            id=str(uuid.uuid4()),
            user_id=user.id if user else None,
            email=email.lower().strip(),
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=0,
            failure_reason=None
        )
        
        # Check if user exists
        if not user:
            attempt.failure_reason = "user_not_found"
            self.db.add(attempt)
            self.db.commit()
            return None
        
        # Check if account is locked
        if user.is_locked == 1:
            if user.locked_until and user.locked_until > datetime.utcnow():
                attempt.failure_reason = "account_locked"
                self.db.add(attempt)
                self.db.commit()
                return None
            else:
                # Lock expired, unlock account
                user.is_locked = 0
                user.locked_until = None
                user.failed_login_attempts = 0
        
        # Check if account is active
        if user.is_active == 0:
            attempt.failure_reason = "account_inactive"
            self.db.add(attempt)
            self.db.commit()
            return None
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            user.last_failed_login = datetime.utcnow()
            
            # Lock account if too many failures
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.is_locked = 1
                user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                attempt.failure_reason = "account_locked_after_failures"
                logger.warning(f"Account locked due to {user.failed_login_attempts} failed attempts: {user.email}")
            else:
                attempt.failure_reason = "invalid_password"
            
            self.db.add(attempt)
            self.db.commit()
            return None
        
        # Authentication successful
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        user.is_locked = 0
        user.locked_until = None
        
        attempt.success = 1
        attempt.user_id = user.id
        
        self.db.add(attempt)
        self.db.commit()
        
        logger.info(f"Successful login: {user.email}")
        return user
    
    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Create a new refresh token."""
        token = create_refresh_jwt(user_id, tenant_id)
        self.store_refresh_token(
            token=token,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return token

    def store_refresh_token(
        self,
        token: str,
        user_id: str,
        tenant_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RefreshToken:
        """Persist a refresh token hash without storing the raw token."""
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        payload = auth_manager.verify_token(token)
        expires_at = datetime.utcfromtimestamp(payload["exp"]) if payload and payload.get("exp") else (
            datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )

        refresh_token = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            tenant_id=tenant_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            is_revoked=0,
        )

        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)

        return refresh_token
    
    def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token by token string."""
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return self.db.query(RefreshToken).filter(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == 0,
                RefreshToken.expires_at > datetime.utcnow()
            )
        ).first()
    
    def revoke_refresh_token(self, token: str) -> bool:
        """Revoke a refresh token."""
        refresh_token = self.get_refresh_token(token)
        if refresh_token:
            refresh_token.is_revoked = 1
            refresh_token.revoked_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all refresh tokens for a user."""
        count = self.db.query(RefreshToken).filter(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == 0
            )
        ).update({
            RefreshToken.is_revoked: 1,
            RefreshToken.revoked_at: datetime.utcnow()
        })
        self.db.commit()
        return count
    
    def get_user_roles(self, user_id: str, tenant_id: str) -> List[Role]:
        """Get user roles for a specific tenant."""
        user_tenant = self.db.query(UserTenant).filter(
            and_(
                UserTenant.user_id == user_id,
                UserTenant.tenant_id == tenant_id
            )
        ).first()
        
        if not user_tenant:
            return []
        
        # Convert role strings to Role enums
        roles = []
        for role_str in user_tenant.roles:
            try:
                roles.append(Role(role_str))
            except ValueError:
                logger.warning(f"Invalid role: {role_str}")
        
        return roles
    
    def assign_user_role(
        self,
        user_id: str,
        tenant_id: str,
        role: Role
    ) -> UserTenant:
        """Assign a role to a user in a tenant."""
        user_tenant = self.db.query(UserTenant).filter(
            and_(
                UserTenant.user_id == user_id,
                UserTenant.tenant_id == tenant_id
            )
        ).first()
        
        if user_tenant:
            # Add role if not already present
            role_str = role.value
            if role_str not in user_tenant.roles:
                user_tenant.roles.append(role_str)
                user_tenant.updated_at = datetime.utcnow()
        else:
            # Create new user-tenant relationship
            user_tenant = UserTenant(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                roles=[role.value]
            )
            self.db.add(user_tenant)
        
        self.db.commit()
        self.db.refresh(user_tenant)
        return user_tenant
    
    def create_email_verification_token(self, user_id: str, email: str) -> EmailVerification:
        """Create an email verification token."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=1)
        
        verification = EmailVerification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token=token,
            email=email,
            is_used=0,
            expires_at=expires_at
        )
        
        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)
        
        return verification
    
    def verify_email(self, token: str) -> Optional[User]:
        """Verify email using verification token."""
        verification = self.db.query(EmailVerification).filter(
            and_(
                EmailVerification.token == token,
                EmailVerification.is_used == 0,
                EmailVerification.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not verification:
            return None
        
        # Mark as used
        verification.is_used = 1
        verification.used_at = datetime.utcnow()
        
        # Verify user email
        user = self.get_user_by_id(verification.user_id)
        if user:
            user.is_verified = 1
            user.email_verified_at = datetime.utcnow()
        
        self.db.commit()
        return user
    
    def create_password_reset_token(self, user_id: str) -> PasswordReset:
        """Create a password reset token."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        reset = PasswordReset(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token=token,
            is_used=0,
            expires_at=expires_at
        )
        
        self.db.add(reset)
        self.db.commit()
        self.db.refresh(reset)
        
        return reset
    
    def reset_password(self, token: str, new_password: str) -> Optional[User]:
        """Reset password using reset token."""
        reset = self.db.query(PasswordReset).filter(
            and_(
                PasswordReset.token == token,
                PasswordReset.is_used == 0,
                PasswordReset.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not reset:
            return None
        
        # Mark as used
        reset.is_used = 1
        reset.used_at = datetime.utcnow()
        
        # Update password
        user = self.get_user_by_id(reset.user_id)
        if user:
            user.password_hash = pwd_context.hash(new_password)
            user.failed_login_attempts = 0
            user.is_locked = 0
            user.locked_until = None
        
        self.db.commit()
        return user

