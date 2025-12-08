"""
Authentication and authorization utilities.
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import settings
from api.models import TokenData, User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
bearer_scheme = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ============================================================================
# Password Utilities
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


# ============================================================================
# JWT Token Utilities
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        TokenData object with decoded information
        
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, tenant_id=tenant_id)
        return token_data
        
    except JWTError:
        raise credentials_exception


# ============================================================================
# Authentication Dependencies
# ============================================================================

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> User:
    """
    Get current user from JWT token.
    
    This is a simplified implementation for demo purposes.
    In production, you would query the database for user details.
    """
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    # In production, fetch user from database
    # For demo, create a user object from token data
    user = User(
        username=token_data.username,
        email=f"{token_data.username}@example.com",
        tenant_id=token_data.tenant_id or "default-tenant",
        disabled=False
    )
    
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> str:
    """
    Verify API key for enterprise clients.
    
    Args:
        api_key: API key from header
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If API key is invalid
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


async def get_current_user(
    token_user: Optional[User] = Depends(get_current_user_from_token),
    api_key: Optional[str] = Depends(verify_api_key)
) -> User:
    """
    Get current user from either JWT token or API key.
    
    This allows both authentication methods.
    For API key auth, creates a default user.
    """
    # If JWT token authentication succeeded
    if token_user:
        return token_user
    
    # If API key authentication succeeded, create a default user
    if api_key:
        return User(
            username="api_user",
            email="api@example.com",
            tenant_id="api-tenant",
            disabled=False
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )


# ============================================================================
# Demo Authentication Helper
# ============================================================================

def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate a user (demo implementation).
    
    In production, this would query the database and verify password hash.
    For demo purposes, accepts any username with password "demo123".
    """
    # Demo: Accept any username with password "demo123"
    if password == "demo123":
        return User(
            username=username,
            email=f"{username}@example.com",
            tenant_id=f"tenant-{username}",
            disabled=False
        )
    
    return None


# ============================================================================
# Optional Authentication (for public endpoints)
# ============================================================================

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    
    Useful for endpoints that have different behavior for authenticated users
    but are also accessible publicly.
    """
    try:
        if credentials:
            token_data = decode_access_token(credentials.credentials)
            return User(
                username=token_data.username,
                email=f"{token_data.username}@example.com",
                tenant_id=token_data.tenant_id or "default-tenant",
                disabled=False
            )
        elif api_key and api_key in settings.api_keys:
            return User(
                username="api_user",
                email="api@example.com",
                tenant_id="api-tenant",
                disabled=False
            )
    except:
        pass
    
    return None
