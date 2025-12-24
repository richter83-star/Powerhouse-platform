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
bearer_scheme = HTTPBearer(auto_error=False)
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[User]:
    """
    Get current user from JWT token.
    
    Queries the database for user details based on token claims.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    token_data = decode_access_token(token)
    
    # Fetch user from database
    from database.session import get_db
    from database.models import User as DBUser
    db = next(get_db())
    
    # Try to find user by email (username in token is typically email)
    user_db = None
    if token_data.username:
        user_db = db.query(DBUser).filter(DBUser.email == token_data.username).first()
    
    # If not found by email, try by ID if username looks like a UUID
    if not user_db and token_data.username:
        try:
            import uuid
            uuid.UUID(token_data.username)  # Check if it's a UUID
            user_db = db.query(DBUser).filter(DBUser.id == token_data.username).first()
        except (ValueError, AttributeError):
            pass
    
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Map database user to API user model
    user = User(
        username=user_db.email.split('@')[0] if user_db.email else token_data.username,
        email=user_db.email,
        tenant_id=token_data.tenant_id or "default-tenant",
        disabled=user_db.disabled if hasattr(user_db, 'disabled') else False
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
        return None
    
    api_keys = getattr(settings, "api_keys", [])
    if not api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key authentication is not configured",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key not in api_keys:
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
    
    # If API key authentication succeeded, look up or create API user
    if api_key:
        from database.session import get_db
        from database.models import User as DBUser
        db = next(get_db())
        # Try to find API user
        user_db = db.query(DBUser).filter(DBUser.email == "api@system.local").first()
        db.close()
        
        if user_db:
            return User(
                username="api_user",
                email=user_db.email,
                tenant_id="api-tenant",
                disabled=False
            )
        # If no API user exists, raise error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API user not configured"
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
    Authenticate a user by querying the database and verifying password hash.
    
    Args:
        username: User email or username
        password: Plain text password
        
    Returns:
        User object if authenticated, None otherwise
    """
    from database.session import get_db
    from database.models import User as DBUser
    from core.security.user_service import UserService
    
    db = next(get_db())
    user_service = UserService(db)
    
    # Try to find user by email
    user_db = db.query(DBUser).filter(DBUser.email == username).first()
    if not user_db:
        db.close()
        return None
    
    # Verify password
    if not user_service.verify_password(password, user_db.password_hash):
        db.close()
        return None
    
    # Map to API user model
    user = User(
        username=user_db.email.split('@')[0] if user_db.email else username,
        email=user_db.email,
        tenant_id=getattr(user_db, 'tenant_id', 'default-tenant'),
        disabled=getattr(user_db, 'disabled', False)
    )
    
    db.close()
    return user


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
            from database.session import get_db
            from database.models import User as DBUser
            db = next(get_db())
            user_db = None
            if token_data.username:
                user_db = db.query(DBUser).filter(DBUser.email == token_data.username).first()
            if not user_db and token_data.username:
                try:
                    import uuid
                    uuid.UUID(token_data.username)
                    user_db = db.query(DBUser).filter(DBUser.id == token_data.username).first()
                except (ValueError, AttributeError):
                    pass
            db.close()
            
            if user_db:
                return User(
                    username=user_db.email.split('@')[0] if user_db.email else token_data.username,
                    email=user_db.email,
                    tenant_id=token_data.tenant_id or "default-tenant",
                    disabled=getattr(user_db, 'disabled', False)
                )
        elif api_key and api_key in settings.api_keys:
            # For API key users, create a system user
            from database.session import get_db
            from database.models import User as DBUser
            db = next(get_db())
            # Try to find or create API user
            user_db = db.query(DBUser).filter(DBUser.email == "api@system.local").first()
            db.close()
            
            if user_db:
                return User(
                    username="api_user",
                    email=user_db.email,
                    tenant_id="api-tenant",
                    disabled=False
                )
            # If no API user found, return None (will be handled by caller)
            return None
    except:
        pass
    
    return None
