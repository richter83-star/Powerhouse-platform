
"""
Secure Plugin Architecture - Plugin Registry
Manages plugin repository, versioning, and discovery.
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import logging

from .plugin_base import PluginMetadata, PluginCapability, PluginPermission
from .plugin_security import PluginSignature, PluginValidator

logger = logging.getLogger(__name__)


class PluginRegistryEntry:
    """Represents a plugin entry in the registry"""
    
    def __init__(
        self,
        metadata: PluginMetadata,
        file_path: str,
        signature: str,
        file_hash: str,
        registered_at: datetime,
        status: str = "active"
    ):
        self.metadata = metadata
        self.file_path = file_path
        self.signature = signature
        self.file_hash = file_hash
        self.registered_at = registered_at
        self.status = status
        self.download_count = 0
        self.last_updated = registered_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary"""
        return {
            'metadata': self.metadata.to_dict(),
            'file_path': self.file_path,
            'signature': self.signature,
            'file_hash': self.file_hash,
            'registered_at': self.registered_at.isoformat(),
            'status': self.status,
            'download_count': self.download_count,
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginRegistryEntry':
        """Create entry from dictionary"""
        metadata = PluginMetadata(
            name=data['metadata']['name'],
            version=data['metadata']['version'],
            author=data['metadata']['author'],
            description=data['metadata']['description'],
            capabilities=[
                PluginCapability(c) for c in data['metadata']['capabilities']
            ],
            required_permissions=[
                PluginPermission(p) for p in data['metadata']['required_permissions']
            ],
            dependencies=data['metadata'].get('dependencies'),
            min_platform_version=data['metadata'].get('min_platform_version'),
            max_platform_version=data['metadata'].get('max_platform_version')
        )
        
        entry = cls(
            metadata=metadata,
            file_path=data['file_path'],
            signature=data['signature'],
            file_hash=data['file_hash'],
            registered_at=datetime.fromisoformat(data['registered_at']),
            status=data.get('status', 'active')
        )
        
        entry.download_count = data.get('download_count', 0)
        entry.last_updated = datetime.fromisoformat(
            data.get('last_updated', data['registered_at'])
        )
        
        return entry


class PluginRegistry:
    """
    Manages plugin repository with versioning and discovery.
    Acts as a trusted source for verified plugins.
    """
    
    def __init__(
        self,
        registry_dir: Optional[str] = None,
        registry_file: str = "plugin_registry.json"
    ):
        """
        Initialize plugin registry.
        
        Args:
            registry_dir: Directory for registry storage
            registry_file: Name of registry file
        """
        self.registry_dir = Path(registry_dir or './plugin_registry')
        self.registry_file = self.registry_dir / registry_file
        self.plugins: Dict[str, Dict[str, PluginRegistryEntry]] = {}
        
        # Create registry directory
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize security components
        self.signature_handler = PluginSignature()
        self.validator = PluginValidator()
        
        # Load existing registry
        self._load_registry()
        
        logger.info(f"PluginRegistry initialized at: {self.registry_dir}")
    
    def register_plugin(
        self,
        plugin_path: str,
        metadata: PluginMetadata,
        force: bool = False
    ) -> bool:
        """
        Register a new plugin in the registry.
        
        Args:
            plugin_path: Path to plugin file
            metadata: Plugin metadata
            force: Force registration even if version exists
            
        Returns:
            True if registered successfully
        """
        try:
            # Validate plugin
            validation_result = self.validator.validate_plugin(
                plugin_path,
                metadata.to_dict()
            )
            
            if not validation_result['valid']:
                logger.error(f"Plugin validation failed: {validation_result['errors']}")
                return False
            
            # Check if plugin already registered
            if metadata.name in self.plugins:
                if metadata.version in self.plugins[metadata.name] and not force:
                    logger.warning(
                        f"Plugin {metadata.name} v{metadata.version} already registered"
                    )
                    return False
            else:
                self.plugins[metadata.name] = {}
            
            # Generate signature
            signature = self.signature_handler.sign_plugin(
                plugin_path,
                metadata.to_dict()
            )
            
            # Calculate file hash
            file_hash = self.validator.calculate_plugin_hash(plugin_path)
            
            # Copy plugin to registry directory
            plugin_filename = f"{metadata.name}_v{metadata.version}.py"
            registry_plugin_path = self.registry_dir / plugin_filename
            
            import shutil
            shutil.copy2(plugin_path, registry_plugin_path)
            
            # Create registry entry
            entry = PluginRegistryEntry(
                metadata=metadata,
                file_path=str(registry_plugin_path),
                signature=signature,
                file_hash=file_hash,
                registered_at=datetime.utcnow()
            )
            
            # Add to registry
            self.plugins[metadata.name][metadata.version] = entry
            
            # Save registry
            self._save_registry()
            
            logger.info(f"Registered plugin: {metadata.name} v{metadata.version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register plugin: {e}")
            return False
    
    def unregister_plugin(self, name: str, version: Optional[str] = None) -> bool:
        """
        Unregister a plugin from the registry.
        
        Args:
            name: Plugin name
            version: Plugin version (if None, unregister all versions)
            
        Returns:
            True if unregistered successfully
        """
        try:
            if name not in self.plugins:
                logger.warning(f"Plugin not found: {name}")
                return False
            
            if version:
                # Unregister specific version
                if version in self.plugins[name]:
                    # Mark as inactive instead of deleting
                    self.plugins[name][version].status = "inactive"
                    self._save_registry()
                    logger.info(f"Unregistered plugin: {name} v{version}")
                    return True
                else:
                    logger.warning(f"Version not found: {name} v{version}")
                    return False
            else:
                # Unregister all versions
                for v in self.plugins[name].values():
                    v.status = "inactive"
                self._save_registry()
                logger.info(f"Unregistered all versions of plugin: {name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to unregister plugin: {e}")
            return False
    
    def get_plugin(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[PluginRegistryEntry]:
        """
        Get plugin entry from registry.
        
        Args:
            name: Plugin name
            version: Plugin version (if None, returns latest active version)
            
        Returns:
            Plugin registry entry or None
        """
        if name not in self.plugins:
            return None
        
        if version:
            return self.plugins[name].get(version)
        else:
            # Return latest active version
            active_versions = [
                (v, entry) for v, entry in self.plugins[name].items()
                if entry.status == "active"
            ]
            if active_versions:
                return max(active_versions, key=lambda x: x[0])[1]
            return None
    
    def search_plugins(
        self,
        capability: Optional[PluginCapability] = None,
        author: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> List[PluginRegistryEntry]:
        """
        Search for plugins in registry.
        
        Args:
            capability: Filter by capability
            author: Filter by author
            keyword: Search in name and description
            
        Returns:
            List of matching plugin entries
        """
        results = []
        
        for plugin_name, versions in self.plugins.items():
            for version, entry in versions.items():
                # Skip inactive plugins
                if entry.status != "active":
                    continue
                
                # Apply filters
                if capability and capability not in entry.metadata.capabilities:
                    continue
                
                if author and entry.metadata.author != author:
                    continue
                
                if keyword:
                    keyword_lower = keyword.lower()
                    if (keyword_lower not in entry.metadata.name.lower() and
                        keyword_lower not in entry.metadata.description.lower()):
                        continue
                
                results.append(entry)
        
        return results
    
    def list_plugins(
        self,
        include_inactive: bool = False
    ) -> List[PluginRegistryEntry]:
        """
        List all plugins in registry.
        
        Args:
            include_inactive: Include inactive plugins
            
        Returns:
            List of plugin entries
        """
        results = []
        
        for versions in self.plugins.values():
            for entry in versions.values():
                if include_inactive or entry.status == "active":
                    results.append(entry)
        
        return results
    
    def update_plugin_metadata(
        self,
        name: str,
        version: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update plugin metadata.
        
        Args:
            name: Plugin name
            version: Plugin version
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully
        """
        try:
            entry = self.get_plugin(name, version)
            if not entry:
                logger.warning(f"Plugin not found: {name} v{version}")
                return False
            
            # Update allowed fields
            allowed_fields = ['status', 'description']
            for field, value in updates.items():
                if field in allowed_fields:
                    if hasattr(entry.metadata, field):
                        setattr(entry.metadata, field, value)
                    elif hasattr(entry, field):
                        setattr(entry, field, value)
            
            entry.last_updated = datetime.utcnow()
            self._save_registry()
            
            logger.info(f"Updated metadata for {name} v{version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update plugin metadata: {e}")
            return False
    
    def increment_download_count(self, name: str, version: str) -> None:
        """Increment download count for a plugin"""
        entry = self.get_plugin(name, version)
        if entry:
            entry.download_count += 1
            self._save_registry()
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with registry stats
        """
        active_plugins = sum(
            1 for versions in self.plugins.values()
            for entry in versions.values()
            if entry.status == "active"
        )
        
        total_downloads = sum(
            entry.download_count
            for versions in self.plugins.values()
            for entry in versions.values()
        )
        
        return {
            'total_plugins': len(self.plugins),
            'active_plugins': active_plugins,
            'total_versions': sum(len(v) for v in self.plugins.values()),
            'total_downloads': total_downloads
        }
    
    def _load_registry(self) -> None:
        """Load registry from file"""
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                
                for plugin_name, versions in data.items():
                    self.plugins[plugin_name] = {}
                    for version, entry_data in versions.items():
                        self.plugins[plugin_name][version] = \
                            PluginRegistryEntry.from_dict(entry_data)
                
                logger.info(f"Loaded {len(self.plugins)} plugins from registry")
            
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
    
    def _save_registry(self) -> None:
        """Save registry to file"""
        try:
            data = {}
            for plugin_name, versions in self.plugins.items():
                data[plugin_name] = {}
                for version, entry in versions.items():
                    data[plugin_name][version] = entry.to_dict()
            
            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Registry saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
