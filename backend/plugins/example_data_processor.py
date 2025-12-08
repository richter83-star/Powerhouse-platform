
"""
Example Plugin: Data Processor
Demonstrates how to create a plugin for data processing capabilities.
"""

from typing import Dict, Any, List
import logging

from core.plugin_base import (
    PluginInterface,
    PluginMetadata,
    PluginCapability,
    PluginPermission
)

logger = logging.getLogger(__name__)


class DataProcessorPlugin(PluginInterface):
    """
    Example plugin that provides data processing capabilities.
    """
    
    def __init__(self):
        super().__init__()
        self.processed_count = 0
    
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="data_processor",
            version="1.0.0",
            author="Powerhouse Platform",
            description="Processes and transforms data with various operations",
            capabilities=[
                PluginCapability.DATA_PROCESSING
            ],
            required_permissions=[
                PluginPermission.FILE_READ
            ],
            dependencies=[],
            min_platform_version="1.0.0"
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin"""
        try:
            self.config = config
            self._initialized = True
            self._active = True
            
            self.logger.info("DataProcessorPlugin initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plugin action"""
        if not self._active:
            return {
                'success': False,
                'error': 'Plugin not active'
            }
        
        try:
            if action == "transform":
                return self._transform_data(params)
            elif action == "filter":
                return self._filter_data(params)
            elif action == "aggregate":
                return self._aggregate_data(params)
            elif action == "normalize":
                return self._normalize_data(params)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
                
        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_available_actions(self) -> List[Dict[str, Any]]:
        """Return list of available actions"""
        return [
            {
                'name': 'transform',
                'description': 'Transform data using specified operation',
                'parameters': {
                    'data': 'List of values to transform',
                    'operation': 'Operation to apply (multiply, add, power)'
                }
            },
            {
                'name': 'filter',
                'description': 'Filter data based on condition',
                'parameters': {
                    'data': 'List of values to filter',
                    'condition': 'Filter condition (greater, less, equal)',
                    'threshold': 'Threshold value'
                }
            },
            {
                'name': 'aggregate',
                'description': 'Aggregate data using specified function',
                'parameters': {
                    'data': 'List of values to aggregate',
                    'function': 'Aggregation function (sum, avg, min, max)'
                }
            },
            {
                'name': 'normalize',
                'description': 'Normalize data to range [0, 1]',
                'parameters': {
                    'data': 'List of values to normalize'
                }
            }
        ]
    
    def shutdown(self) -> bool:
        """Shutdown the plugin"""
        try:
            self._active = False
            self.logger.info("DataProcessorPlugin shutdown successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to shutdown: {e}")
            return False
    
    def _transform_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data"""
        data = params.get('data', [])
        operation = params.get('operation', 'multiply')
        factor = params.get('factor', 1)
        
        if operation == 'multiply':
            result = [x * factor for x in data]
        elif operation == 'add':
            result = [x + factor for x in data]
        elif operation == 'power':
            result = [x ** factor for x in data]
        else:
            return {
                'success': False,
                'error': f'Unknown operation: {operation}'
            }
        
        self.processed_count += 1
        
        return {
            'success': True,
            'result': result,
            'operation': operation,
            'processed_count': self.processed_count
        }
    
    def _filter_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter data"""
        data = params.get('data', [])
        condition = params.get('condition', 'greater')
        threshold = params.get('threshold', 0)
        
        if condition == 'greater':
            result = [x for x in data if x > threshold]
        elif condition == 'less':
            result = [x for x in data if x < threshold]
        elif condition == 'equal':
            result = [x for x in data if x == threshold]
        else:
            return {
                'success': False,
                'error': f'Unknown condition: {condition}'
            }
        
        self.processed_count += 1
        
        return {
            'success': True,
            'result': result,
            'filtered_count': len(data) - len(result),
            'processed_count': self.processed_count
        }
    
    def _aggregate_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate data"""
        data = params.get('data', [])
        function = params.get('function', 'sum')
        
        if not data:
            return {
                'success': False,
                'error': 'No data provided'
            }
        
        if function == 'sum':
            result = sum(data)
        elif function == 'avg':
            result = sum(data) / len(data)
        elif function == 'min':
            result = min(data)
        elif function == 'max':
            result = max(data)
        else:
            return {
                'success': False,
                'error': f'Unknown function: {function}'
            }
        
        self.processed_count += 1
        
        return {
            'success': True,
            'result': result,
            'function': function,
            'processed_count': self.processed_count
        }
    
    def _normalize_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data"""
        data = params.get('data', [])
        
        if not data:
            return {
                'success': False,
                'error': 'No data provided'
            }
        
        min_val = min(data)
        max_val = max(data)
        
        if max_val == min_val:
            result = [0.5] * len(data)
        else:
            result = [
                (x - min_val) / (max_val - min_val)
                for x in data
            ]
        
        self.processed_count += 1
        
        return {
            'success': True,
            'result': result,
            'processed_count': self.processed_count
        }
