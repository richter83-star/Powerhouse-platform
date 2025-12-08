
"""
Secure Plugin Architecture - Plugin Loader
Handles dynamic loading and lifecycle management of plugins.
"""

import importlib.util
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from datetime import datetime

from .plugin_base import (
    PluginInterface,
    PluginMetadata,
    PluginException,
    PluginInitializationError,
    PluginExecutionError,
    PluginSecurityError
)
from .plugin_security import PluginValidator

logger = logging.getLogger(__name__)


class PluginInstance:
    """Represents a loaded plugin instance"""
    
    def __init__(
        self,
        plugin: PluginInterface,
        metadata: PluginMetadata,
        path: str,
        config: Dict[str, Any]
    ):
        self.plugin = plugin
        self.metadata = metadata
        self.path = path
        self.config = config
        self.loaded_at = datetime.utcnow()
        self.last_executed = None
        self.execution_count = 0
        self.error_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert instance to dictionary"""
        return {
            'metadata': self.metadata.to_dict(),
            'path': self.path,
            'loaded_at': self.loaded_at.isoformat(),
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'execution_count': self.execution_count,
            'error_count': self.error_count,
            'health': self.plugin.health_check()
        }


class PluginLoader:
    """
    Handles dynamic loading and lifecycle management of plugins.
    Implements secure loading with validation and sandboxing.
    """
    
    def __init__(
        self,
        plugin_dir: Optional[str] = None,
        enable_security: bool = True
    ):
        """
        Initialize plugin loader.
        
        Args:
            plugin_dir: Directory containing plugins
            enable_security: Enable security validation
        """
        self.plugin_dir = Path(plugin_dir or './plugins')
        self.enable_security = enable_security
        self.validator = PluginValidator() if enable_security else None
        self.loaded_plugins: Dict[str, PluginInstance] = {}
        
        # Create plugin directory if it doesn't exist
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"PluginLoader initialized with directory: {self.plugin_dir}")
    
    def load_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None,
        signature: Optional[str] = None,
        granted_permissions: Optional[List[str]] = None
    ) -> bool:
        """
        Load a plugin by name.
        
        Args:
            plugin_name: Name of the plugin to load
            config: Plugin configuration
            signature: Plugin signature for verification
            granted_permissions: Permissions granted to plugin
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # Check if already loaded
            if plugin_name in self.loaded_plugins:
                logger.warning(f"Plugin {plugin_name} already loaded")
                return True
            
            # Find plugin file
            plugin_path = self._find_plugin_file(plugin_name)
            if not plugin_path:
                logger.error(f"Plugin file not found: {plugin_name}")
                return False
            
            # Load and validate plugin
            plugin_instance = self._load_plugin_module(
                plugin_path,
                config or {},
                signature,
                granted_permissions
            )
            
            if plugin_instance:
                self.loaded_plugins[plugin_name] = plugin_instance
                logger.info(f"Successfully loaded plugin: {plugin_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of plugin to unload
            
        Returns:
            True if unloaded successfully, False otherwise
        """
        try:
            if plugin_name not in self.loaded_plugins:
                logger.warning(f"Plugin not loaded: {plugin_name}")
                return False
            
            plugin_instance = self.loaded_plugins[plugin_name]
            
            # Shutdown plugin
            plugin_instance.plugin.shutdown()
            
            # Remove from loaded plugins
            del self.loaded_plugins[plugin_name]
            
            logger.info(f"Successfully unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
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
            Execution results
        """
        try:
            if plugin_name not in self.loaded_plugins:
                raise PluginException(f"Plugin not loaded: {plugin_name}")
            
            plugin_instance = self.loaded_plugins[plugin_name]
            
            # Execute action
            result = plugin_instance.plugin.execute(action, params)
            
            # Update stats
            plugin_instance.last_executed = datetime.utcnow()
            plugin_instance.execution_count += 1
            
            return {
                'success': True,
                'result': result,
                'plugin': plugin_name,
                'action': action
            }
            
        except Exception as e:
            logger.error(f"Plugin execution failed: {e}")
            if plugin_name in self.loaded_plugins:
                self.loaded_plugins[plugin_name].error_count += 1
            
            return {
                'success': False,
                'error': str(e),
                'plugin': plugin_name,
                'action': action
            }
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a loaded plugin.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Plugin information dictionary or None
        """
        if plugin_name in self.loaded_plugins:
            return self.loaded_plugins[plugin_name].to_dict()
        return None
    
    def list_loaded_plugins(self) -> List[Dict[str, Any]]:
        """
        List all loaded plugins.
        
        Returns:
            List of plugin information dictionaries
        """
        return [
            instance.to_dict()
            for instance in self.loaded_plugins.values()
        ]
    
    def reload_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Reload a plugin.
        
        Args:
            plugin_name: Name of plugin to reload
            config: New configuration (optional)
            
        Returns:
            True if reloaded successfully
        """
        # Get current config if not provided
        if config is None and plugin_name in self.loaded_plugins:
            config = self.loaded_plugins[plugin_name].config
        
        # Unload and reload
        if self.unload_plugin(plugin_name):
            return self.load_plugin(plugin_name, config)
        
        return False
    
    def _find_plugin_file(self, plugin_name: str) -> Optional[Path]:
        """Find plugin file in plugin directory"""
        plugin_file = self.plugin_dir / f"{plugin_name}.py"
        if plugin_file.exists():
            return plugin_file
        
        # Also check in subdirectories
        for subdir in self.plugin_dir.iterdir():
            if subdir.is_dir():
                plugin_file = subdir / f"{plugin_name}.py"
                if plugin_file.exists():
                    return plugin_file
        
        return None
    
    def _load_plugin_module(
        self,
        plugin_path: Path,
        config: Dict[str, Any],
        signature: Optional[str],
        granted_permissions: Optional[List[str]]
    ) -> Optional[PluginInstance]:
        """Load plugin module and create instance"""
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(
                plugin_path.stem,
                plugin_path
            )
            if not spec or not spec.loader:
                logger.error("Failed to load plugin spec")
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_path.stem] = module
            spec.loader.exec_module(module)
            
            # Find plugin class
            plugin_class = None
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and 
                    issubclass(item, PluginInterface) and 
                    item is not PluginInterface):
                    plugin_class = item
                    break
            
            if not plugin_class:
                logger.error("No plugin class found in module")
                return None
            
            # Create plugin instance
            plugin = plugin_class()
            
            # Validate plugin
            if not plugin.validate():
                logger.error("Plugin validation failed")
                return None
            
            # Get metadata
            metadata = plugin.get_metadata()
            
            # Security validation
            if self.enable_security and self.validator:
                validation_result = self.validator.validate_plugin(
                    str(plugin_path),
                    metadata.to_dict(),
                    signature,
                    granted_permissions
                )
                
                if not validation_result['valid']:
                    logger.error(f"Security validation failed: {validation_result['errors']}")
                    raise PluginSecurityError(
                        f"Security validation failed: {validation_result['errors']}"
                    )
            
            # Initialize plugin
            if not plugin.initialize(config):
                logger.error("Plugin initialization failed")
                raise PluginInitializationError("Plugin initialization failed")
            
            # Create plugin instance
            return PluginInstance(
                plugin=plugin,
                metadata=metadata,
                path=str(plugin_path),
                config=config
            )
            
        except Exception as e:
            logger.error(f"Failed to load plugin module: {e}")
            return None
