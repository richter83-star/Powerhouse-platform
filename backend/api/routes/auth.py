"""
Authentication API routes.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from api.models import Token
from api.auth import authenticate_user, create_access_token
from config.settings import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/token",
    response_model=Token,
    summary="Get Access Token",
    description="Authenticate and get a JWT access token"
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return JWT access token.
    
    For demo purposes, accepts any username with password "demo123".
    In production, this would verify against a user database.
    
    **Demo Credentials:**
    - Username: any username
    - Password: demo123
    """
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "tenant_id": user.tenant_id},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")
