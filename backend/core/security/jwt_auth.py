
"""
JWT-based authentication with access and refresh tokens.
"""
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass
import hashlib

# In production, load from environment variables
JWT_SECRET_KEY = secrets.token_urlsafe(32)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

@dataclass
class TokenPayload:
    """JWT token payload structure"""
    user_id: str
    tenant_id: str
    roles: list
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for revocation tracking
    
class JWTAuthManager:
    """
    Manages JWT-based authentication with access and refresh tokens.
    
    Features:
    - Access token generation and validation
    - Refresh token rotation
    - Token revocation support
    - Multi-tenant claims
    """
    
    def __init__(self, secret_key: str = JWT_SECRET_KEY, algorithm: str = JWT_ALGORITHM):
        """Initialize JWT auth manager"""
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.revoked_tokens = set()  # In production, use Redis
        
    def create_access_token(
        self, 
        user_id: str, 
        tenant_id: str, 
        roles: list,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a new access token.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            roles: List of user roles
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        jti = self._generate_jti(user_id, tenant_id)
        
        to_encode = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "roles": [r.value if hasattr(r, 'value') else str(r) for r in roles],
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": jti,
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a new refresh token.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT refresh token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        jti = self._generate_jti(user_id, tenant_id, "refresh")
        
        to_encode = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": jti,
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is revoked
            if payload.get("jti") in self.revoked_tokens:
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def revoke_token(self, token: str):
        """
        Revoke a token by adding its JTI to the revoked list.
        
        Args:
            token: JWT token to revoke
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # Allow decoding expired tokens
            )
            jti = payload.get("jti")
            if jti:
                self.revoked_tokens.add(jti)
        except jwt.JWTError:
            pass
    
    def refresh_access_token(self, refresh_token: str, roles: list) -> Optional[str]:
        """
        Generate a new access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            roles: User roles for the new access token
            
        Returns:
            New access token or None if refresh token is invalid
        """
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        
        return self.create_access_token(user_id, tenant_id, roles)
    
    def _generate_jti(self, user_id: str, tenant_id: str, token_type: str = "access") -> str:
        """Generate a unique JWT ID"""
        data = f"{user_id}:{tenant_id}:{token_type}:{datetime.utcnow().isoformat()}:{secrets.token_urlsafe(16)}"
        return hashlib.sha256(data.encode()).hexdigest()

# Global auth manager instance
auth_manager = JWTAuthManager()

def create_access_token(user_id: str, tenant_id: str, roles: list) -> str:
    """Helper function to create access token"""
    return auth_manager.create_access_token(user_id, tenant_id, roles)

def create_refresh_token(user_id: str, tenant_id: str) -> str:
    """Helper function to create refresh token"""
    return auth_manager.create_refresh_token(user_id, tenant_id)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Helper function to verify token"""
    return auth_manager.verify_token(token)
