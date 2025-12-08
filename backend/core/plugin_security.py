
"""
Secure Plugin Architecture - Security and Verification
Handles plugin signing, verification, and sandboxing.
"""

import hashlib
import hmac
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import logging
import importlib.util
import sys

logger = logging.getLogger(__name__)


class PluginSignature:
    """Handles plugin signing and verification"""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize plugin signature handler.
        
        Args:
            secret_key: Secret key for HMAC signing (if None, generates one)
        """
        self.secret_key = secret_key or os.environ.get(
            'PLUGIN_SECRET_KEY',
            'default-plugin-secret-key-change-in-production'
        )
    
    def sign_plugin(self, plugin_path: str, metadata: Dict[str, Any]) -> str:
        """
        Generate signature for a plugin.
        
        Args:
            plugin_path: Path to plugin file
            metadata: Plugin metadata dictionary
            
        Returns:
            Signature string
        """
        try:
            # Read plugin file content
            with open(plugin_path, 'rb') as f:
                plugin_content = f.read()
            
            # Create signature payload
            payload = {
                'content_hash': hashlib.sha256(plugin_content).hexdigest(),
                'metadata': metadata,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Generate HMAC signature
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                self.secret_key.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as e:
            logger.error(f"Failed to sign plugin: {e}")
            raise
    
    def verify_signature(
        self,
        plugin_path: str,
        metadata: Dict[str, Any],
        signature: str,
        max_age_hours: int = 24
    ) -> bool:
        """
        Verify plugin signature.
        
        Args:
            plugin_path: Path to plugin file
            metadata: Plugin metadata dictionary
            signature: Plugin signature to verify
            max_age_hours: Maximum age of signature in hours
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Generate expected signature
            expected_signature = self.sign_plugin(plugin_path, metadata)
            
            # Compare signatures
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("Plugin signature mismatch")
                return False
            
            # Check timestamp (if present in metadata)
            if 'signed_at' in metadata:
                signed_at = datetime.fromisoformat(metadata['signed_at'])
                if datetime.utcnow() - signed_at > timedelta(hours=max_age_hours):
                    logger.warning("Plugin signature expired")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify plugin signature: {e}")
            return False


class PluginSandbox:
    """Implements sandboxing for plugin execution"""
    
    def __init__(self):
        self.restricted_modules = {
            'os',
            'sys',
            'subprocess',
            'importlib',
            '__builtin__',
            'builtins'
        }
        self.allowed_builtins = {
            'print',
            'len',
            'range',
            'enumerate',
            'zip',
            'map',
            'filter',
            'sorted',
            'sum',
            'min',
            'max',
            'abs',
            'round',
            'isinstance',
            'issubclass',
            'type',
            'str',
            'int',
            'float',
            'bool',
            'list',
            'dict',
            'set',
            'tuple'
        }
    
    def validate_plugin_imports(self, plugin_path: str) -> bool:
        """
        Validate that plugin doesn't import restricted modules.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            True if imports are safe, False otherwise
        """
        try:
            with open(plugin_path, 'r') as f:
                content = f.read()
            
            # Check for restricted imports
            for module in self.restricted_modules:
                if f"import {module}" in content or f"from {module}" in content:
                    logger.warning(f"Plugin attempts to import restricted module: {module}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate plugin imports: {e}")
            return False
    
    def create_sandbox_globals(self) -> Dict[str, Any]:
        """
        Create restricted global namespace for plugin execution.
        
        Returns:
            Dictionary of allowed global variables
        """
        return {
            '__builtins__': {
                name: __builtins__[name]
                for name in self.allowed_builtins
                if name in __builtins__
            }
        }
    
    def validate_plugin_permissions(
        self,
        required_permissions: List[str],
        granted_permissions: List[str]
    ) -> bool:
        """
        Validate that plugin has required permissions.
        
        Args:
            required_permissions: Permissions required by plugin
            granted_permissions: Permissions granted to plugin
            
        Returns:
            True if all required permissions are granted
        """
        required_set = set(required_permissions)
        granted_set = set(granted_permissions)
        
        if not required_set.issubset(granted_set):
            missing = required_set - granted_set
            logger.warning(f"Plugin missing permissions: {missing}")
            return False
        
        return True


class PluginValidator:
    """Validates plugin compliance and security"""
    
    def __init__(self):
        self.signature_handler = PluginSignature()
        self.sandbox = PluginSandbox()
    
    def validate_plugin(
        self,
        plugin_path: str,
        metadata: Dict[str, Any],
        signature: Optional[str] = None,
        granted_permissions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive plugin validation.
        
        Args:
            plugin_path: Path to plugin file
            metadata: Plugin metadata
            signature: Optional plugin signature
            granted_permissions: Optional list of granted permissions
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check file exists
        if not os.path.exists(plugin_path):
            results['valid'] = False
            results['errors'].append("Plugin file not found")
            return results
        
        # Validate signature if provided
        if signature:
            if not self.signature_handler.verify_signature(
                plugin_path, metadata, signature
            ):
                results['valid'] = False
                results['errors'].append("Invalid plugin signature")
        else:
            results['warnings'].append("Plugin not signed")
        
        # Validate imports
        if not self.sandbox.validate_plugin_imports(plugin_path):
            results['valid'] = False
            results['errors'].append("Plugin uses restricted imports")
        
        # Validate permissions
        if granted_permissions is not None:
            required_perms = metadata.get('required_permissions', [])
            if not self.sandbox.validate_plugin_permissions(
                required_perms, granted_permissions
            ):
                results['valid'] = False
                results['errors'].append("Insufficient permissions")
        
        # Validate metadata
        required_fields = ['name', 'version', 'author']
        for field in required_fields:
            if field not in metadata:
                results['valid'] = False
                results['errors'].append(f"Missing required field: {field}")
        
        return results
    
    def calculate_plugin_hash(self, plugin_path: str) -> str:
        """
        Calculate SHA-256 hash of plugin file.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            Hash string
        """
        sha256_hash = hashlib.sha256()
        with open(plugin_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
