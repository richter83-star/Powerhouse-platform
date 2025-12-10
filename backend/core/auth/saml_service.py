"""
SAML 2.0 Authentication Service

Provides SAML-based SSO for enterprise customers.
"""

import logging
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os

logger = logging.getLogger(__name__)

# Try to import SAML library
try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    from onelogin.saml2.utils import OneLogin_Saml2_Utils
    HAS_SAML_LIB = True
except ImportError:
    HAS_SAML_LIB = False
    logger.warning(
        "python3-saml not installed. SAML authentication will not work. "
        "Install with: pip install python3-saml"
    )


class SAMLService:
    """
    SAML 2.0 authentication service.
    
    Features:
    - SAML 2.0 support
    - Just-in-time user provisioning
    - Enterprise-only feature
    """
    
    def __init__(self):
        self._saml_configs: Dict[str, Dict[str, Any]] = {}
    
    def configure_saml(
        self,
        tenant_id: str,
        entity_id: str,
        sso_url: str,
        x509_cert: str,
        attribute_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Configure SAML for a tenant.
        
        Args:
            tenant_id: Tenant ID
            entity_id: SAML entity ID
            sso_url: SSO URL
            x509_cert: X.509 certificate
            attribute_mapping: Map SAML attributes to user fields
            
        Returns:
            Configuration dict
        """
        config = {
            "tenant_id": tenant_id,
            "entity_id": entity_id,
            "sso_url": sso_url,
            "x509_cert": x509_cert,
            "attribute_mapping": attribute_mapping or {
                "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
                "name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
                "groups": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/groups"
            },
            "created_at": datetime.utcnow().isoformat()
        }
        
        self._saml_configs[tenant_id] = config
        logger.info(f"SAML configured for tenant {tenant_id}")
        
        return config
    
    def generate_saml_request(self, tenant_id: str, relay_state: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate SAML authentication request.
        
        Args:
            tenant_id: Tenant ID
            relay_state: Optional relay state
            
        Returns:
            SAML request data
        """
        config = self._saml_configs.get(tenant_id)
        if not config:
            raise ValueError(f"SAML not configured for tenant {tenant_id}")
        
        # Generate SAML AuthnRequest
        request_id = str(uuid.uuid4())
        issue_instant = datetime.utcnow().isoformat()
        
        # In production, use a proper SAML library (python3-saml, pysaml2)
        saml_request = {
            "request_id": request_id,
            "entity_id": config["entity_id"],
            "sso_url": config["sso_url"],
            "relay_state": relay_state,
            "issue_instant": issue_instant
        }
        
        return saml_request
    
    def process_saml_response(
        self,
        tenant_id: str,
        saml_response: str,
        request_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process SAML response and extract user attributes.
        
        Args:
            tenant_id: Tenant ID
            saml_response: Base64-encoded SAML response or raw SAMLResponse parameter
            request_data: Request data dict for OneLogin_Saml2_Auth
            
        Returns:
            User attributes dict with email, name, and groups
        """
        if not HAS_SAML_LIB:
            raise NotImplementedError(
                "SAML authentication requires python3-saml library. "
                "Install with: pip install python3-saml"
            )
        
        config = self._saml_configs.get(tenant_id)
        if not config:
            raise ValueError(f"SAML not configured for tenant {tenant_id}")
        
        try:
            # Prepare SAML settings
            saml_settings = self._prepare_saml_settings(config)
            
            # Prepare request data if not provided
            if request_data is None:
                request_data = self._prepare_request_data(saml_response)
            
            # Create SAML auth instance
            auth = OneLogin_Saml2_Auth(request_data, saml_settings)
            
            # Process the SAML response
            auth.process_response()
            
            # Check for errors
            errors = auth.get_errors()
            if errors:
                error_msg = f"SAML processing errors: {', '.join(errors)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Get user attributes
            attributes = auth.get_attributes()
            name_id = auth.get_nameid()
            
            # Map SAML attributes to user fields
            attribute_mapping = config.get("attribute_mapping", {})
            
            user_attrs = {
                "email": self._extract_attribute(
                    attributes, 
                    attribute_mapping.get("email", "email")
                ) or name_id,
                "name": self._extract_attribute(
                    attributes,
                    attribute_mapping.get("name", "name")
                ) or name_id.split("@")[0] if "@" in name_id else name_id,
                "groups": self._extract_attribute(
                    attributes,
                    attribute_mapping.get("groups", "groups")
                ) or [],
                "saml_name_id": name_id,
                "saml_session_index": auth.get_session_index(),
            }
            
            logger.info(f"SAML authentication successful for user: {user_attrs['email']}")
            return user_attrs
            
        except NotImplementedError:
            raise
        except Exception as e:
            logger.error(f"Failed to process SAML response: {e}", exc_info=True)
            raise ValueError(f"Invalid SAML response: {str(e)}")
    
    def _prepare_saml_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare SAML settings dict for OneLogin_Saml2_Settings."""
        return {
            "strict": True,
            "debug": os.getenv("DEBUG", "False").lower() == "true",
            "sp": {
                "entityId": config.get("sp_entity_id", f"powerhouse-{config['tenant_id']}"),
                "assertionConsumerService": {
                    "url": config.get("acs_url", f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/api/auth/saml/acs"),
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                },
                "x509cert": config.get("sp_x509_cert", ""),
                "privateKey": config.get("sp_private_key", ""),
            },
            "idp": {
                "entityId": config["entity_id"],
                "singleSignOnService": {
                    "url": config["sso_url"],
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "x509cert": config["x509_cert"],
            },
            "security": {
                "authnRequestsSigned": True,
                "wantAssertionsSigned": True,
                "wantAssertionsEncrypted": False,
                "signMetadata": False,
                "wantNameIdEncrypted": False,
                "requestedAuthnContext": False,
            }
        }
    
    def _prepare_request_data(self, saml_response: str) -> Dict[str, Any]:
        """Prepare request data dict for OneLogin_Saml2_Auth."""
        # Parse SAML response from POST data or query parameters
        if isinstance(saml_response, str):
            # Assume it's the SAMLResponse parameter
            return {
                "https": "on" if os.getenv("HTTPS", "off") == "on" else "off",
                "http_host": os.getenv("HTTP_HOST", "localhost"),
                "script_name": "/api/auth/saml/acs",
                "server_name": os.getenv("SERVER_NAME", "localhost"),
                "server_port": os.getenv("SERVER_PORT", "8001"),
                "request_uri": "/api/auth/saml/acs",
                "query_string": "",
                "post_data": {
                    "SAMLResponse": saml_response
                }
            }
        return {}
    
    def _extract_attribute(self, attributes: Dict[str, Any], attr_name: str) -> Any:
        """Extract attribute value from SAML attributes."""
        if not attributes or not attr_name:
            return None
        
        # Try exact match first
        if attr_name in attributes:
            value = attributes[attr_name]
            # Return first value if it's a list
            if isinstance(value, list) and len(value) > 0:
                return value[0]
            return value
        
        # Try case-insensitive match
        attr_name_lower = attr_name.lower()
        for key, value in attributes.items():
            if key.lower() == attr_name_lower:
                if isinstance(value, list) and len(value) > 0:
                    return value[0]
                return value
        
        return None
    
    def generate_saml_request(self, tenant_id: str, relay_state: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate SAML authentication request.
        
        Args:
            tenant_id: Tenant ID
            relay_state: Optional relay state
            
        Returns:
            SAML request data with redirect URL
        """
        if not HAS_SAML_LIB:
            raise NotImplementedError(
                "SAML authentication requires python3-saml library. "
                "Install with: pip install python3-saml"
            )
        
        config = self._saml_configs.get(tenant_id)
        if not config:
            raise ValueError(f"SAML not configured for tenant {tenant_id}")
        
        try:
            saml_settings = self._prepare_saml_settings(config)
            settings = OneLogin_Saml2_Settings(saml_settings)
            
            # Generate AuthnRequest
            authn_request = OneLogin_Saml2_Utils.build_authn_request(
                settings,
                False,  # force_authn
                False,  # is_passive
                False,  # set_nameid_policy
                None,   # name_id_value_req
                None,   # provider_name
                None,   # requested_authn_context
                relay_state
            )
            
            # Build redirect URL
            sso_url = config["sso_url"]
            parameters = {"SAMLRequest": authn_request}
            if relay_state:
                parameters["RelayState"] = relay_state
            
            redirect_url = OneLogin_Saml2_Utils.redirect(
                sso_url,
                parameters,
                settings
            )
            
            return {
                "redirect_url": redirect_url,
                "relay_state": relay_state,
                "request_id": OneLogin_Saml2_Utils.decode_authn_request(authn_request).get("ID")
            }
            
        except Exception as e:
            logger.error(f"Failed to generate SAML request: {e}", exc_info=True)
            raise ValueError(f"Failed to generate SAML request: {str(e)}")


# Global SAML service instance
_saml_service: Optional[SAMLService] = None


def get_saml_service() -> SAMLService:
    """Get the global SAML service instance."""
    global _saml_service
    if _saml_service is None:
        _saml_service = SAMLService()
    return _saml_service

