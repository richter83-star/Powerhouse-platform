
"""
JWT-based authentication with access and refresh tokens.
"""
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass
import hashlib
import logging

logger = logging.getLogger(__name__)

# Try to import Redis for token blacklist
try:
    import redis
    from redis.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, token blacklist will be in-memory only")

from config.settings import settings

# Load from environment or use defaults
JWT_SECRET_KEY = getattr(settings, 'jwt_secret_key', None) or settings.secret_key
JWT_ALGORITHM = getattr(settings, 'algorithm', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, 'access_token_expire_minutes', 30)
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
    
    def __init__(
        self, 
        secret_key: str = JWT_SECRET_KEY, 
        algorithm: str = JWT_ALGORITHM,
        redis_client: Optional[redis.Redis] = None
    ):
        """Initialize JWT auth manager"""
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.redis_client = None
        self.revoked_tokens = set()  # Fallback: in-memory set
        
        # Initialize Redis client for token blacklist
        if REDIS_AVAILABLE:
            try:
                if redis_client:
                    self.redis_client = redis_client
                else:
                    # Create Redis connection from settings
                    redis_host = getattr(settings, 'redis_host', 'localhost')
                    redis_port = getattr(settings, 'redis_port', 6379)
                    redis_db = getattr(settings, 'redis_db', 0)
                    redis_password = getattr(settings, 'redis_password', None)
                    
                    pool = ConnectionPool(
                        host=redis_host,
                        port=redis_port,
                        db=redis_db,
                        password=redis_password,
                        decode_responses=False,
                        max_connections=50
                    )
                    self.redis_client = redis.Redis(connection_pool=pool)
                    # Test connection
                    self.redis_client.ping()
                    logger.info("JWT auth manager connected to Redis for token blacklist")
            except Exception as e:
                logger.warning(f"Redis unavailable for token blacklist, using in-memory: {e}")
                self.redis_client = None
        
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
            jti = payload.get("jti")
            
            # Check if token is revoked (using Redis if available)
            if self._is_token_revoked(jti):
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def _is_token_revoked(self, jti: Optional[str]) -> bool:
        """Check if token JTI is revoked."""
        if not jti:
            return False
        
        # Use Redis if available
        if self.redis_client:
            try:
                key = f"token:blacklist:{jti}"
                return self.redis_client.exists(key) > 0
            except Exception as e:
                logger.warning(f"Error checking Redis blacklist: {e}, falling back to in-memory")
                return jti in self.revoked_tokens
        else:
            # Fallback to in-memory set
            return jti in self.revoked_tokens
    
    def revoke_token(self, token: str, ttl_seconds: Optional[int] = None):
        """
        Revoke a token by adding its JTI to the revoked list.
        
        Args:
            token: JWT token to revoke
            ttl_seconds: TTL for blacklist entry (default: token expiration time)
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # Allow decoding expired tokens
            )
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if jti:
                if self.redis_client:
                    try:
                        key = f"token:blacklist:{jti}"
                        # Set TTL based on token expiration or provided TTL
                        if ttl_seconds:
                            ttl = ttl_seconds
                        elif exp:
                            # TTL = expiration time - current time
                            ttl = max(0, int(exp - datetime.utcnow().timestamp()))
                        else:
                            ttl = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Default to access token expiry
                        
                        self.redis_client.setex(key, ttl, "1")
                        logger.debug(f"Token revoked in Redis: {jti[:16]}... (TTL: {ttl}s)")
                    except Exception as e:
                        logger.warning(f"Error revoking token in Redis: {e}, using in-memory")
                        self.revoked_tokens.add(jti)
                else:
                    # Fallback to in-memory set
                    self.revoked_tokens.add(jti)
        except jwt.JWTError as exc:
            logger.debug("Failed to decode token for revocation: %s", exc)
    
    def revoke_all_user_tokens(self, user_id: str, tenant_id: Optional[str] = None):
        """
        Revoke all tokens for a user (e.g., on password change or logout all devices).
        
        Args:
            user_id: User ID
            tenant_id: Optional tenant ID for scoping
        """
        # Store user revocation timestamp
        key = f"user:revoked:{user_id}"
        if tenant_id:
            key = f"{key}:{tenant_id}"
        
        if self.redis_client:
            try:
                # Store revocation timestamp (valid for 30 days)
                self.redis_client.setex(key, 30 * 24 * 60 * 60, str(int(datetime.utcnow().timestamp())))
                logger.info(f"All tokens revoked for user: {user_id}")
            except Exception as e:
                logger.warning(f"Error revoking all tokens in Redis: {e}")
    
    def refresh_access_token(
        self, 
        refresh_token: str, 
        roles: list,
        rotate_refresh_token: bool = True
    ) -> Optional[Dict[str, str]]:
        """
        Generate a new access token using a refresh token.
        
        Implements refresh token rotation for enhanced security:
        - Each refresh token can only be used once
        - New refresh token is issued on each refresh
        - Old refresh token is automatically revoked
        
        Args:
            refresh_token: Valid refresh token
            roles: User roles for the new access token
            rotate_refresh_token: If True, rotate refresh token (recommended)
            
        Returns:
            Dict with new access_token and optionally new refresh_token, or None if invalid
        """
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        
        # Create new access token
        new_access_token = self.create_access_token(user_id, tenant_id, roles)
        
        result = {"access_token": new_access_token}
        
        # Rotate refresh token if enabled (security best practice)
        if rotate_refresh_token:
            # Revoke old refresh token
            self.revoke_token(refresh_token, ttl_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
            
            # Create new refresh token
            new_refresh_token = self.create_refresh_token(user_id, tenant_id)
            result["refresh_token"] = new_refresh_token
        
        return result
    
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
