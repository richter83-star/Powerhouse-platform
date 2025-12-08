
"""
Secure Plugin Architecture - Plugin Service
Main service orchestrating plugin management, loading, and execution.
"""

import os
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from .plugin_base import PluginCapability, PluginPermission, PluginMetadata
from .plugin_loader import PluginLoader
from .plugin_registry import PluginRegistry
from .plugin_security import PluginValidator

logger = logging.getLogger(__name__)


class PluginService:
    """
    Main plugin service that orchestrates plugin management.
    Provides high-level API for plugin operations.
    """
    
    def __init__(
        self,
        plugin_dir: Optional[str] = None,
        registry_dir: Optional[str] = None,
        enable_security: bool = True
    ):
        """
        Initialize plugin service.
        
        Args:
            plugin_dir: Directory for plugin storage
            registry_dir: Directory for registry storage
            enable_security: Enable security features
        """
        self.plugin_dir = plugin_dir or './plugins'
        self.registry_dir = registry_dir or './plugin_registry'
        self.enable_security = enable_security
        
        # Initialize components
        self.registry = PluginRegistry(registry_dir=self.registry_dir)
        self.loader = PluginLoader(
            plugin_dir=self.plugin_dir,
            enable_security=enable_security
        )
        self.validator = PluginValidator()
        
        # Service state
        self.service_started = datetime.utcnow()
        
        logger.info("PluginService initialized")
    
    def install_plugin(
        self,
        plugin_path: str,
        metadata: Dict[str, Any],
        auto_load: bool = True
    ) -> Dict[str, Any]:
        """
        Install a plugin into the registry.
        
        Args:
            plugin_path: Path to plugin file
            metadata: Plugin metadata dictionary
            auto_load: Automatically load plugin after installation
            
        Returns:
            Installation result dictionary
        """
        try:
            # Convert metadata dict to PluginMetadata object
            plugin_metadata = PluginMetadata(
                name=metadata['name'],
                version=metadata['version'],
                author=metadata['author'],
                description=metadata['description'],
                capabilities=[
                    PluginCapability(c) for c in metadata['capabilities']
                ],
                required_permissions=[
                    PluginPermission(p) for p in metadata['required_permissions']
                ],
                dependencies=metadata.get('dependencies'),
                min_platform_version=metadata.get('min_platform_version'),
                max_platform_version=metadata.get('max_platform_version')
            )
            
            # Register plugin
            success = self.registry.register_plugin(
                plugin_path,
                plugin_metadata
            )
            
            if not success:
                return {
                    'success': False,
                    'error': 'Failed to register plugin'
                }
            
            # Auto-load if requested
            if auto_load:
                load_success = self.loader.load_plugin(
                    plugin_metadata.name,
                    config=metadata.get('config', {})
                )
                
                return {
                    'success': True,
                    'plugin': plugin_metadata.name,
                    'version': plugin_metadata.version,
                    'loaded': load_success
                }
            
            return {
                'success': True,
                'plugin': plugin_metadata.name,
                'version': plugin_metadata.version,
                'loaded': False
            }
            
        except Exception as e:
            logger.error(f"Failed to install plugin: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def uninstall_plugin(
        self,
        plugin_name: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Uninstall a plugin from the registry.
        
        Args:
            plugin_name: Name of plugin
            version: Plugin version (None for all versions)
            
        Returns:
            Uninstallation result dictionary
        """
        try:
            # Unload plugin if loaded
            if plugin_name in self.loader.loaded_plugins:
                self.loader.unload_plugin(plugin_name)
            
            # Unregister from registry
            success = self.registry.unregister_plugin(plugin_name, version)
            
            return {
                'success': success,
                'plugin': plugin_name,
                'version': version
            }
            
        except Exception as e:
            logger.error(f"Failed to uninstall plugin: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def load_plugin(
        self,
        plugin_name: str,
        version: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load a plugin from the registry.
        
        Args:
            plugin_name: Name of plugin
            version: Plugin version (None for latest)
            config: Plugin configuration
            
        Returns:
            Load result dictionary
        """
        try:
            # Get plugin from registry
            entry = self.registry.get_plugin(plugin_name, version)
            if not entry:
                return {
                    'success': False,
                    'error': 'Plugin not found in registry'
                }
            
            # Load plugin
            success = self.loader.load_plugin(
                plugin_name,
                config=config or {},
                signature=entry.signature,
                granted_permissions=[
                    p.value for p in entry.metadata.required_permissions
                ]
            )
            
            if success:
                self.registry.increment_download_count(
                    plugin_name,
                    entry.metadata.version
                )
            
            return {
                'success': success,
                'plugin': plugin_name,
                'version': entry.metadata.version
            }
            
        except Exception as e:
            logger.error(f"Failed to load plugin: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def unload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Unload result dictionary
        """
        try:
            success = self.loader.unload_plugin(plugin_name)
            
            return {
                'success': success,
                'plugin': plugin_name
            }
            
        except Exception as e:
            logger.error(f"Failed to unload plugin: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_plugin_action(
        self,
        plugin_name: str,
        action: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a plugin action.
        
        Args:
            plugin_name: Name of plugin
            action: Action to execute
            params: Action parameters
            
        Returns:
            Execution result dictionary
        """
        return self.loader.execute_plugin_action(plugin_name, action, params)
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a loaded plugin.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Plugin information or None
        """
        return self.loader.get_plugin_info(plugin_name)
    
    def list_loaded_plugins(self) -> List[Dict[str, Any]]:
        """
        List all loaded plugins.
        
        Returns:
            List of loaded plugin information
        """
        return self.loader.list_loaded_plugins()
    
    def list_available_plugins(
        self,
        capability: Optional[str] = None,
        author: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List available plugins in registry.
        
        Args:
            capability: Filter by capability
            author: Filter by author
            keyword: Search keyword
            
        Returns:
            List of available plugin information
        """
        capability_enum = PluginCapability(capability) if capability else None
        entries = self.registry.search_plugins(
            capability=capability_enum,
            author=author,
            keyword=keyword
        )
        
        return [entry.to_dict() for entry in entries]
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.
        
        Returns:
            Service statistics dictionary
        """
        registry_stats = self.registry.get_registry_stats()
        
        return {
            'service_started': self.service_started.isoformat(),
            'loaded_plugins': len(self.loader.loaded_plugins),
            'registry': registry_stats,
            'security_enabled': self.enable_security
        }
    
    def validate_plugin(
        self,
        plugin_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a plugin without installing.
        
        Args:
            plugin_path: Path to plugin file
            metadata: Plugin metadata
            
        Returns:
            Validation result dictionary
        """
        return self.validator.validate_plugin(plugin_path, metadata)
