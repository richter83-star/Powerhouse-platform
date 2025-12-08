
"""
Secure Plugin Architecture - Base Plugin Interface
Defines the contract that all plugins must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PluginCapability(Enum):
    """Enumeration of plugin capability types"""
    DATA_PROCESSING = "data_processing"
    MODEL_INFERENCE = "model_inference"
    AGENT_SKILL = "agent_skill"
    INTEGRATION = "integration"
    VISUALIZATION = "visualization"
    MONITORING = "monitoring"
    SECURITY = "security"
    CUSTOM = "custom"


class PluginPermission(Enum):
    """Enumeration of plugin permissions"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    NETWORK_ACCESS = "network_access"
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    EXECUTE_CODE = "execute_code"
    SYSTEM_ACCESS = "system_access"
    AGENT_CONTROL = "agent_control"


class PluginMetadata:
    """Plugin metadata container"""
    
    def __init__(
        self,
        name: str,
        version: str,
        author: str,
        description: str,
        capabilities: List[PluginCapability],
        required_permissions: List[PluginPermission],
        dependencies: Optional[List[str]] = None,
        min_platform_version: Optional[str] = None,
        max_platform_version: Optional[str] = None
    ):
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.capabilities = capabilities
        self.required_permissions = required_permissions
        self.dependencies = dependencies or []
        self.min_platform_version = min_platform_version
        self.max_platform_version = max_platform_version
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "capabilities": [c.value for c in self.capabilities],
            "required_permissions": [p.value for p in self.required_permissions],
            "dependencies": self.dependencies,
            "min_platform_version": self.min_platform_version,
            "max_platform_version": self.max_platform_version
        }


class PluginInterface(ABC):
    """
    Base interface that all plugins must implement.
    This defines the contract for plugin lifecycle and execution.
    """
    
    def __init__(self):
        self._initialized = False
        self._active = False
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Return plugin metadata including name, version, capabilities, etc.
        """
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
            
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a plugin action.
        
        Args:
            action: Action name to execute
            params: Action parameters
            
        Returns:
            Dictionary containing execution results
        """
        pass
    
    @abstractmethod
    def get_available_actions(self) -> List[Dict[str, Any]]:
        """
        Return list of available actions this plugin provides.
        
        Returns:
            List of action definitions with name, description, parameters
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """
        Clean up resources and shutdown the plugin.
        
        Returns:
            True if shutdown successful, False otherwise
        """
        pass
    
    def validate(self) -> bool:
        """
        Validate plugin integrity and requirements.
        
        Returns:
            True if validation passes, False otherwise
        """
        try:
            metadata = self.get_metadata()
            if not metadata.name or not metadata.version:
                self.logger.error("Plugin metadata missing required fields")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Plugin validation failed: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on plugin.
        
        Returns:
            Dictionary with health status information
        """
        return {
            "status": "healthy" if self._active else "inactive",
            "initialized": self._initialized,
            "active": self._active
        }
    
    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized"""
        return self._initialized
    
    @property
    def is_active(self) -> bool:
        """Check if plugin is active"""
        return self._active


class PluginException(Exception):
    """Base exception for plugin-related errors"""
    pass


class PluginInitializationError(PluginException):
    """Raised when plugin initialization fails"""
    pass


class PluginExecutionError(PluginException):
    """Raised when plugin execution fails"""
    pass


class PluginSecurityError(PluginException):
    """Raised when plugin security validation fails"""
    pass


class PluginValidationError(PluginException):
    """Raised when plugin validation fails"""
    pass
