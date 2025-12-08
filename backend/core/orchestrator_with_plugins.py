
"""
Orchestrator with Plugin Support
Integrates the plugin system with the main orchestrator.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .orchestrator import Orchestrator
from .plugin_service import PluginService

logger = logging.getLogger(__name__)


class PluginEnabledOrchestrator(Orchestrator):
    """
    Extended orchestrator with plugin support.
    Allows dynamic capability extension through plugins.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        plugin_dir: str = './plugins',
        registry_dir: str = './plugin_registry',
        enable_plugin_security: bool = True
    ):
        """
        Initialize plugin-enabled orchestrator.
        
        Args:
            config: Orchestrator configuration
            plugin_dir: Directory for plugins
            registry_dir: Directory for plugin registry
            enable_plugin_security: Enable plugin security features
        """
        super().__init__(config)
        
        # Initialize plugin service
        self.plugin_service = PluginService(
            plugin_dir=plugin_dir,
            registry_dir=registry_dir,
            enable_security=enable_plugin_security
        )
        
        # Plugin execution stats
        self.plugin_execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'plugins_used': {}
        }
        
        logger.info("PluginEnabledOrchestrator initialized with plugin support")
    
    def execute_with_plugins(
        self,
        task: Dict[str, Any],
        available_plugins: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a task with plugin support.
        
        Args:
            task: Task to execute
            available_plugins: List of plugins available for this task
            
        Returns:
            Execution result with plugin information
        """
        task_id = task.get('task_id', f"task_{datetime.utcnow().isoformat()}")
        
        logger.info(f"Executing task {task_id} with plugin support")
        
        # Check if task requires plugins
        required_capabilities = task.get('required_capabilities', [])
        
        if required_capabilities:
            # Find suitable plugins
            suitable_plugins = self._find_suitable_plugins(
                required_capabilities,
                available_plugins
            )
            
            if suitable_plugins:
                logger.info(
                    f"Found {len(suitable_plugins)} suitable plugins for task"
                )
                
                # Execute task with plugins
                result = self._execute_task_with_plugins(
                    task,
                    suitable_plugins
                )
            else:
                logger.warning("No suitable plugins found, executing without plugins")
                result = self.execute(task)
        else:
            # Execute normally
            result = self.execute(task)
        
        # Update stats
        self._update_plugin_stats(result)
        
        return result
    
    def load_plugin_for_task(
        self,
        plugin_name: str,
        version: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Load a plugin for use in tasks.
        
        Args:
            plugin_name: Name of plugin to load
            version: Plugin version (optional)
            config: Plugin configuration (optional)
            
        Returns:
            True if loaded successfully
        """
        result = self.plugin_service.load_plugin(
            plugin_name=plugin_name,
            version=version,
            config=config
        )
        
        if result['success']:
            logger.info(f"Plugin {plugin_name} loaded successfully")
            return True
        else:
            logger.error(f"Failed to load plugin {plugin_name}: {result.get('error')}")
            return False
    
    def execute_plugin_action(
        self,
        plugin_name: str,
        action: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a plugin action directly.
        
        Args:
            plugin_name: Name of plugin
            action: Action to execute
            params: Action parameters
            
        Returns:
            Execution result
        """
        result = self.plugin_service.execute_plugin_action(
            plugin_name=plugin_name,
            action=action,
            params=params
        )
        
        # Update stats
        self.plugin_execution_stats['total_executions'] += 1
        
        if result.get('success'):
            self.plugin_execution_stats['successful_executions'] += 1
            
            # Track plugin usage
            if plugin_name not in self.plugin_execution_stats['plugins_used']:
                self.plugin_execution_stats['plugins_used'][plugin_name] = 0
            self.plugin_execution_stats['plugins_used'][plugin_name] += 1
        else:
            self.plugin_execution_stats['failed_executions'] += 1
        
        return result
    
    def get_available_plugin_capabilities(self) -> Dict[str, List[str]]:
        """
        Get capabilities of all loaded plugins.
        
        Returns:
            Dictionary mapping plugin names to their capabilities
        """
        capabilities = {}
        
        loaded_plugins = self.plugin_service.list_loaded_plugins()
        for plugin in loaded_plugins:
            plugin_name = plugin['metadata']['name']
            capabilities[plugin_name] = plugin['metadata']['capabilities']
        
        return capabilities
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """
        Get plugin execution statistics.
        
        Returns:
            Plugin statistics dictionary
        """
        return {
            'execution_stats': self.plugin_execution_stats,
            'service_stats': self.plugin_service.get_service_stats(),
            'loaded_plugins': len(self.plugin_service.list_loaded_plugins()),
            'available_capabilities': self.get_available_plugin_capabilities()
        }
    
    def _find_suitable_plugins(
        self,
        required_capabilities: List[str],
        available_plugins: Optional[List[str]] = None
    ) -> List[str]:
        """
        Find plugins that match required capabilities.
        
        Args:
            required_capabilities: Required capability names
            available_plugins: Optional list to filter by
            
        Returns:
            List of suitable plugin names
        """
        suitable = []
        
        loaded_plugins = self.plugin_service.list_loaded_plugins()
        
        for plugin in loaded_plugins:
            plugin_name = plugin['metadata']['name']
            plugin_capabilities = plugin['metadata']['capabilities']
            
            # Check if plugin has required capabilities
            if any(cap in plugin_capabilities for cap in required_capabilities):
                # Check if in available list if provided
                if available_plugins is None or plugin_name in available_plugins:
                    suitable.append(plugin_name)
        
        return suitable
    
    def _execute_task_with_plugins(
        self,
        task: Dict[str, Any],
        plugin_names: List[str]
    ) -> Dict[str, Any]:
        """
        Execute a task using specified plugins.
        
        Args:
            task: Task to execute
            plugin_names: Names of plugins to use
            
        Returns:
            Execution result
        """
        result = {
            'task_id': task.get('task_id'),
            'success': False,
            'plugin_results': {},
            'final_result': None
        }
        
        try:
            # Get task data
            task_data = task.get('data', {})
            task_action = task.get('action', 'process')
            
            # Execute plugins in sequence
            current_data = task_data
            
            for plugin_name in plugin_names:
                logger.info(f"Executing plugin: {plugin_name}")
                
                plugin_result = self.execute_plugin_action(
                    plugin_name=plugin_name,
                    action=task_action,
                    params=current_data
                )
                
                result['plugin_results'][plugin_name] = plugin_result
                
                if plugin_result.get('success'):
                    # Update data for next plugin
                    if 'result' in plugin_result:
                        current_data = plugin_result['result']
                else:
                    logger.warning(
                        f"Plugin {plugin_name} execution failed: "
                        f"{plugin_result.get('error')}"
                    )
            
            result['final_result'] = current_data
            result['success'] = True
            
        except Exception as e:
            logger.error(f"Task execution with plugins failed: {e}")
            result['error'] = str(e)
        
        return result
    
    def _update_plugin_stats(self, result: Dict[str, Any]) -> None:
        """Update plugin execution statistics"""
        if 'plugin_results' in result:
            for plugin_name, plugin_result in result['plugin_results'].items():
                self.plugin_execution_stats['total_executions'] += 1
                
                if plugin_result.get('success'):
                    self.plugin_execution_stats['successful_executions'] += 1
                else:
                    self.plugin_execution_stats['failed_executions'] += 1
                
                # Track usage
                if plugin_name not in self.plugin_execution_stats['plugins_used']:
                    self.plugin_execution_stats['plugins_used'][plugin_name] = 0
                self.plugin_execution_stats['plugins_used'][plugin_name] += 1
