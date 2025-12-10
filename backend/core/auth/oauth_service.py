"""
OAuth Authentication Service

Provides OAuth-based SSO with Google, Microsoft, and other providers.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import secrets

logger = logging.getLogger(__name__)

# Try to import authlib
try:
    from authlib.integrations.httpx_client import AsyncOAuth2Client
    import httpx
    HAS_AUTHLIB = True
except ImportError:
    HAS_AUTHLIB = False
    logger.warning(
        "authlib not installed. OAuth authentication will not work. "
        "Install with: pip install authlib httpx"
    )


class OAuthProvider:
    """OAuth provider types"""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    OKTA = "okta"
    GENERIC = "generic"


class OAuthService:
    """
    OAuth authentication service.
    
    Features:
    - Google OAuth
    - Microsoft Azure AD OAuth
    - Okta OAuth
    - Generic OAuth 2.0
    - Just-in-time user provisioning
    """
    
    def __init__(self):
        self._oauth_configs: Dict[str, Dict[str, Any]] = {}
    
    def configure_oauth(
        self,
        tenant_id: str,
        provider: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Configure OAuth for a tenant.
        
        Args:
            tenant_id: Tenant ID
            provider: OAuth provider (google, microsoft, okta, generic)
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            scopes: OAuth scopes
            
        Returns:
            Configuration dict
        """
        config = {
            "tenant_id": tenant_id,
            "provider": provider,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "scopes": scopes or ["openid", "email", "profile"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        self._oauth_configs[tenant_id] = config
        logger.info(f"OAuth configured for tenant {tenant_id} with provider {provider}")
        
        return config
    
    def get_authorization_url(
        self,
        tenant_id: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get OAuth authorization URL.
        
        Args:
            tenant_id: Tenant ID
            state: Optional state parameter
            
        Returns:
            Authorization URL and state
        """
        config = self._oauth_configs.get(tenant_id)
        if not config:
            raise ValueError(f"OAuth not configured for tenant {tenant_id}")
        
        # Generate state if not provided
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Get provider-specific authorization URL
        provider = config["provider"]
        
        if provider == OAuthProvider.GOOGLE:
            auth_url = (
                "https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={config['client_id']}&"
                f"redirect_uri={config['redirect_uri']}&"
                f"response_type=code&"
                f"scope={'+'.join(config['scopes'])}&"
                f"state={state}"
            )
        elif provider == OAuthProvider.MICROSOFT:
            auth_url = (
                "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
                f"client_id={config['client_id']}&"
                f"redirect_uri={config['redirect_uri']}&"
                f"response_type=code&"
                f"scope={'+'.join(config['scopes'])}&"
                f"state={state}"
            )
        elif provider == OAuthProvider.OKTA:
            # Okta uses tenant-specific domain
            okta_domain = config.get("okta_domain", "okta.com")
            auth_url = (
                f"https://{okta_domain}/oauth2/v1/authorize?"
                f"client_id={config['client_id']}&"
                f"redirect_uri={config['redirect_uri']}&"
                f"response_type=code&"
                f"scope={'+'.join(config['scopes'])}&"
                f"state={state}"
            )
        else:
            # Generic OAuth
            auth_base_url = config.get("auth_base_url", "")
            auth_url = (
                f"{auth_base_url}?"
                f"client_id={config['client_id']}&"
                f"redirect_uri={config['redirect_uri']}&"
                f"response_type=code&"
                f"scope={'+'.join(config['scopes'])}&"
                f"state={state}"
            )
        
        return {
            "authorization_url": auth_url,
            "state": state
        }
    
    async def exchange_code_for_token(
        self,
        tenant_id: str,
        code: str,
        state: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            tenant_id: Tenant ID
            code: Authorization code
            state: State parameter (for verification)
            
        Returns:
            Token information with access_token, refresh_token, expires_in, etc.
        """
        if not HAS_AUTHLIB:
            raise NotImplementedError(
                "OAuth authentication requires authlib library. "
                "Install with: pip install authlib httpx"
            )
        
        config = self._oauth_configs.get(tenant_id)
        if not config:
            raise ValueError(f"OAuth not configured for tenant {tenant_id}")
        
        provider = config["provider"]
        
        # Get token endpoint URL
        token_url = self._get_token_endpoint(provider, config)
        
        try:
            # Create OAuth2 client
            client = AsyncOAuth2Client(
                client_id=config["client_id"],
                client_secret=config["client_secret"]
            )
            
            # Exchange code for token
            async with httpx.AsyncClient() as http_client:
                token_data = await client.fetch_token(
                    token_url,
                    code=code,
                    redirect_uri=config["redirect_uri"],
                    client=http_client
                )
            
            logger.info(f"OAuth token exchange successful for tenant {tenant_id}, provider {provider}")
            
            return {
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": token_data.get("expires_in"),
                "scope": token_data.get("scope"),
                "id_token": token_data.get("id_token"),  # For OpenID Connect
            }
            
        except Exception as e:
            logger.error(f"OAuth token exchange failed: {e}", exc_info=True)
            raise ValueError(f"Failed to exchange authorization code: {str(e)}")
    
    def _get_token_endpoint(self, provider: str, config: Dict[str, Any]) -> str:
        """Get token endpoint URL for the provider."""
        if provider == OAuthProvider.GOOGLE:
            return "https://oauth2.googleapis.com/token"
        elif provider == OAuthProvider.MICROSOFT:
            return "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        elif provider == OAuthProvider.OKTA:
            okta_domain = config.get("okta_domain", "okta.com")
            return f"https://{okta_domain}/oauth2/v1/token"
        else:
            # Generic OAuth - use configured endpoint
            return config.get("token_endpoint", "")
    
    async def get_user_info(
        self,
        tenant_id: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Get user information from OAuth provider.
        
        Args:
            tenant_id: Tenant ID
            access_token: OAuth access token
            
        Returns:
            User information dict with email, name, and other profile data
        """
        if not HAS_AUTHLIB:
            raise NotImplementedError(
                "OAuth authentication requires authlib library. "
                "Install with: pip install authlib httpx"
            )
        
        config = self._oauth_configs.get(tenant_id)
        if not config:
            raise ValueError(f"OAuth not configured for tenant {tenant_id}")
        
        provider = config["provider"]
        
        # Get userinfo endpoint URL
        userinfo_url = self._get_userinfo_endpoint(provider, config)
        
        try:
            # Make request to userinfo endpoint
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(userinfo_url, headers=headers)
                response.raise_for_status()
                user_info = response.json()
            
            # Normalize user info across providers
            normalized_info = self._normalize_user_info(user_info, provider)
            
            logger.info(f"Retrieved user info for tenant {tenant_id}, provider {provider}")
            
            return normalized_info
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error retrieving user info: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Failed to retrieve user info: HTTP {e.response.status_code}")
        except Exception as e:
            logger.error(f"Failed to retrieve user info: {e}", exc_info=True)
            raise ValueError(f"Failed to retrieve user info: {str(e)}")
    
    def _get_userinfo_endpoint(self, provider: str, config: Dict[str, Any]) -> str:
        """Get userinfo endpoint URL for the provider."""
        if provider == OAuthProvider.GOOGLE:
            return "https://www.googleapis.com/oauth2/v2/userinfo"
        elif provider == OAuthProvider.MICROSOFT:
            return "https://graph.microsoft.com/v1.0/me"
        elif provider == OAuthProvider.OKTA:
            okta_domain = config.get("okta_domain", "okta.com")
            return f"https://{okta_domain}/oauth2/v1/userinfo"
        else:
            # Generic OAuth - use configured endpoint
            return config.get("userinfo_endpoint", "")
    
    def _normalize_user_info(self, user_info: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Normalize user info from different providers to a common format."""
        normalized = {}
        
        if provider == OAuthProvider.GOOGLE:
            normalized = {
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "given_name": user_info.get("given_name"),
                "family_name": user_info.get("family_name"),
                "picture": user_info.get("picture"),
                "locale": user_info.get("locale"),
                "sub": user_info.get("sub"),  # Subject/User ID
            }
        elif provider == OAuthProvider.MICROSOFT:
            normalized = {
                "email": user_info.get("mail") or user_info.get("userPrincipalName"),
                "name": user_info.get("displayName"),
                "given_name": user_info.get("givenName"),
                "family_name": user_info.get("surname"),
                "picture": None,  # Microsoft requires separate API call for profile picture
                "locale": None,
                "sub": user_info.get("id"),
            }
        elif provider == OAuthProvider.OKTA:
            normalized = {
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "given_name": user_info.get("given_name"),
                "family_name": user_info.get("family_name"),
                "picture": None,
                "locale": user_info.get("locale"),
                "sub": user_info.get("sub"),
            }
        else:
            # Generic - try common fields
            normalized = {
                "email": user_info.get("email") or user_info.get("mail"),
                "name": user_info.get("name") or user_info.get("displayName"),
                "given_name": user_info.get("given_name") or user_info.get("givenName"),
                "family_name": user_info.get("family_name") or user_info.get("surname"),
                "picture": user_info.get("picture") or user_info.get("avatar_url"),
                "locale": user_info.get("locale"),
                "sub": user_info.get("sub") or user_info.get("id"),
            }
        
        # Ensure required fields
        if not normalized.get("email"):
            raise ValueError("User info missing required email field")
        if not normalized.get("name"):
            normalized["name"] = normalized.get("email", "").split("@")[0]
        
        return normalized


# Global OAuth service instance
_oauth_service: Optional[OAuthService] = None


def get_oauth_service() -> OAuthService:
    """Get the global OAuth service instance."""
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = OAuthService()
    return _oauth_service

