
"""
Dynamic Plugin Loader
Supports loading and managing third-party plugins at runtime
"""

import importlib.util
import inspect
import json
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel


class PluginMetadata(BaseModel):
    """Plugin metadata"""
    name: str
    version: str
    author: str
    description: str
    dependencies: List[str] = []
    entry_point: str
    config_schema: Dict[str, Any] = {}


class PluginStatus(BaseModel):
    """Plugin status"""
    name: str
    version: str
    enabled: bool
    loaded: bool
    error: Optional[str] = None
    loaded_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None


class Plugin(ABC):
    """Base plugin interface"""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration"""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute plugin logic"""
        pass
    
    @abstractmethod
    def shutdown(self):
        """Cleanup on shutdown"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass


class PluginLoader:
    """Manages plugin loading and lifecycle"""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, Plugin] = {}
        self.metadata: Dict[str, PluginMetadata] = {}
        self.status: Dict[str, PluginStatus] = {}
        self.configs: Dict[str, Dict[str, Any]] = {}
        
        # Create plugin directory if not exists
        self.plugin_dir.mkdir(exist_ok=True)
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins"""
        discovered = []
        
        for item in self.plugin_dir.iterdir():
            if item.is_dir() and (item / "plugin.json").exists():
                try:
                    metadata_path = item / "plugin.json"
                    with open(metadata_path) as f:
                        metadata_dict = json.load(f)
                        metadata = PluginMetadata(**metadata_dict)
                        self.metadata[metadata.name] = metadata
                        discovered.append(metadata.name)
                except Exception as e:
                    print(f"Error discovering plugin {item.name}: {e}")
        
        return discovered
    
    def load_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Load a plugin"""
        if plugin_name in self.plugins:
            return True
        
        if plugin_name not in self.metadata:
            self.status[plugin_name] = PluginStatus(
                name=plugin_name,
                version="unknown",
                enabled=False,
                loaded=False,
                error="Plugin not found"
            )
            return False
        
        metadata = self.metadata[plugin_name]
        plugin_path = self.plugin_dir / plugin_name
        
        try:
            # Check dependencies
            missing_deps = self._check_dependencies(metadata.dependencies)
            if missing_deps:
                raise Exception(f"Missing dependencies: {', '.join(missing_deps)}")
            
            # Load plugin module
            module_path = plugin_path / metadata.entry_point
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}",
                module_path
            )
            if not spec or not spec.loader:
                raise Exception("Could not load plugin module")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Find plugin class
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                raise Exception("No plugin class found")
            
            # Instantiate plugin
            plugin = plugin_class()
            
            # Initialize with config
            config = config or {}
            self.configs[plugin_name] = config
            
            if not plugin.initialize(config):
                raise Exception("Plugin initialization failed")
            
            # Register plugin
            self.plugins[plugin_name] = plugin
            self.status[plugin_name] = PluginStatus(
                name=metadata.name,
                version=metadata.version,
                enabled=True,
                loaded=True,
                loaded_at=datetime.utcnow()
            )
            
            return True
            
        except Exception as e:
            self.status[plugin_name] = PluginStatus(
                name=metadata.name,
                version=metadata.version,
                enabled=False,
                loaded=False,
                error=str(e),
                last_error_at=datetime.utcnow()
            )
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        if plugin_name not in self.plugins:
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            plugin.shutdown()
            del self.plugins[plugin_name]
            
            if plugin_name in self.status:
                self.status[plugin_name].loaded = False
                self.status[plugin_name].enabled = False
            
            return True
            
        except Exception as e:
            if plugin_name in self.status:
                self.status[plugin_name].error = f"Unload error: {str(e)}"
            return False
    
    def reload_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Reload a plugin"""
        self.unload_plugin(plugin_name)
        return self.load_plugin(plugin_name, config)
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get loaded plugin"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self, loaded_only: bool = False) -> List[str]:
        """List plugins"""
        if loaded_only:
            return list(self.plugins.keys())
        return list(self.metadata.keys())
    
    def get_status(self, plugin_name: str) -> Optional[PluginStatus]:
        """Get plugin status"""
        return self.status.get(plugin_name)
    
    def get_all_status(self) -> List[PluginStatus]:
        """Get all plugin statuses"""
        return list(self.status.values())
    
    def update_config(
        self,
        plugin_name: str,
        config: Dict[str, Any]
    ) -> bool:
        """Update plugin configuration"""
        if plugin_name not in self.plugins:
            return False
        
        self.configs[plugin_name] = config
        return self.reload_plugin(plugin_name, config)
    
    def execute_plugin(
        self,
        plugin_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute plugin logic"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin {plugin_name} not loaded")
        
        return plugin.execute(*args, **kwargs)
    
    def shutdown_all(self):
        """Shutdown all plugins"""
        for plugin_name in list(self.plugins.keys()):
            self.unload_plugin(plugin_name)
    
    @staticmethod
    def _check_dependencies(dependencies: List[str]) -> List[str]:
        """Check if dependencies are installed"""
        missing = []
        for dep in dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing.append(dep)
        return missing
    
    @staticmethod
    def _find_plugin_class(module) -> Optional[Type[Plugin]]:
        """Find plugin class in module"""
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, Plugin) and 
                obj is not Plugin):
                return obj
        return None


# Global instance
plugin_loader = PluginLoader()
