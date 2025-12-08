
"""
Example: Using the Secure Plugin Architecture
Demonstrates how to use the plugin system for dynamic capability extension.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.plugin_service import PluginService
from core.plugin_base import PluginMetadata, PluginCapability, PluginPermission
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main example function"""
    
    print("\n" + "="*80)
    print("SECURE PLUGIN ARCHITECTURE - EXAMPLE")
    print("="*80 + "\n")
    
    # Initialize plugin service
    print("1. Initializing Plugin Service...")
    plugin_service = PluginService(
        plugin_dir='./plugins',
        registry_dir='./plugin_registry',
        enable_security=True
    )
    print("✓ Plugin service initialized\n")
    
    # Get service stats
    print("2. Service Statistics:")
    stats = plugin_service.get_service_stats()
    print(f"   - Loaded plugins: {stats['loaded_plugins']}")
    print(f"   - Registry plugins: {stats['registry']['total_plugins']}")
    print(f"   - Security enabled: {stats['security_enabled']}\n")
    
    # Install example plugins
    print("3. Installing Example Plugins...")
    
    # Install data processor plugin
    data_processor_metadata = {
        'name': 'data_processor',
        'version': '1.0.0',
        'author': 'Powerhouse Platform',
        'description': 'Processes and transforms data with various operations',
        'capabilities': ['data_processing'],
        'required_permissions': ['file_read']
    }
    
    result = plugin_service.install_plugin(
        plugin_path='./plugins/example_data_processor.py',
        metadata=data_processor_metadata,
        auto_load=True
    )
    
    if result['success']:
        print(f"   ✓ Installed and loaded: {result['plugin']} v{result['version']}")
    else:
        print(f"   ✗ Failed to install: {result.get('error', 'Unknown error')}")
    
    # Install agent skill plugin
    agent_skill_metadata = {
        'name': 'agent_skill',
        'version': '1.0.0',
        'author': 'Powerhouse Platform',
        'description': 'Extends agent capabilities with new skills',
        'capabilities': ['agent_skill'],
        'required_permissions': ['agent_control']
    }
    
    result = plugin_service.install_plugin(
        plugin_path='./plugins/example_agent_skill.py',
        metadata=agent_skill_metadata,
        auto_load=True
    )
    
    if result['success']:
        print(f"   ✓ Installed and loaded: {result['plugin']} v{result['version']}\n")
    else:
        print(f"   ✗ Failed to install: {result.get('error', 'Unknown error')}\n")
    
    # List loaded plugins
    print("4. Loaded Plugins:")
    loaded_plugins = plugin_service.list_loaded_plugins()
    for plugin in loaded_plugins:
        metadata = plugin['metadata']
        print(f"   - {metadata['name']} v{metadata['version']}")
        print(f"     Author: {metadata['author']}")
        print(f"     Capabilities: {', '.join(metadata['capabilities'])}")
        print(f"     Executions: {plugin['execution_count']}\n")
    
    # Execute plugin actions
    print("5. Executing Plugin Actions...")
    
    # Data processor - Transform data
    print("   a. Data Processor - Transform:")
    result = plugin_service.execute_plugin_action(
        plugin_name='data_processor',
        action='transform',
        params={
            'data': [1, 2, 3, 4, 5],
            'operation': 'multiply',
            'factor': 2
        }
    )
    
    if result.get('success'):
        print(f"      Input: [1, 2, 3, 4, 5]")
        print(f"      Output: {result['result']['result']}")
        print(f"      Operation: {result['result']['operation']}\n")
    
    # Data processor - Aggregate data
    print("   b. Data Processor - Aggregate:")
    result = plugin_service.execute_plugin_action(
        plugin_name='data_processor',
        action='aggregate',
        params={
            'data': [10, 20, 30, 40, 50],
            'function': 'avg'
        }
    )
    
    if result.get('success'):
        print(f"      Input: [10, 20, 30, 40, 50]")
        print(f"      Average: {result['result']['result']}\n")
    
    # Agent skill - Analyze task
    print("   c. Agent Skill - Analyze Task:")
    result = plugin_service.execute_plugin_action(
        plugin_name='agent_skill',
        action='analyze_task',
        params={
            'task_description': 'Analyze and process customer data to generate insights'
        }
    )
    
    if result.get('success'):
        analysis = result['result']['analysis']
        print(f"      Task Type: {analysis['task_type']}")
        print(f"      Keywords: {', '.join(analysis['keywords'])}")
        print(f"      Word Count: {analysis['word_count']}\n")
    
    # Agent skill - Estimate complexity
    print("   d. Agent Skill - Estimate Complexity:")
    result = plugin_service.execute_plugin_action(
        plugin_name='agent_skill',
        action='estimate_complexity',
        params={
            'task_description': 'Build a comprehensive machine learning pipeline'
        }
    )
    
    if result.get('success'):
        estimate = result['result']['estimate']
        print(f"      Complexity Level: {estimate['complexity_level']}")
        print(f"      Complexity Score: {estimate['complexity_score']:.2f}")
        print(f"      Estimated Time: {estimate['estimated_time']}\n")
    
    # Search for plugins
    print("6. Search Available Plugins:")
    available = plugin_service.list_available_plugins(
        capability='data_processing'
    )
    print(f"   Found {len(available)} plugins with 'data_processing' capability")
    for plugin in available:
        print(f"   - {plugin['metadata']['name']}: {plugin['metadata']['description']}\n")
    
    # Get plugin info
    print("7. Plugin Information:")
    info = plugin_service.get_plugin_info('data_processor')
    if info:
        print(f"   Plugin: {info['metadata']['name']}")
        print(f"   Version: {info['metadata']['version']}")
        print(f"   Status: {info['health']['status']}")
        print(f"   Executions: {info['execution_count']}")
        print(f"   Errors: {info['error_count']}\n")
    
    # Final stats
    print("8. Final Statistics:")
    stats = plugin_service.get_service_stats()
    print(f"   - Total loaded plugins: {stats['loaded_plugins']}")
    print(f"   - Total registry plugins: {stats['registry']['total_plugins']}")
    print(f"   - Active plugins: {stats['registry']['active_plugins']}")
    print(f"   - Total downloads: {stats['registry']['total_downloads']}\n")
    
    print("="*80)
    print("EXAMPLE COMPLETED SUCCESSFULLY")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
