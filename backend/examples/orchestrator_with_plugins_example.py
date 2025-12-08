
"""
Example: Using Orchestrator with Plugin Support
Demonstrates integration of plugins with the orchestration system.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.orchestrator_with_plugins import PluginEnabledOrchestrator
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
    print("ORCHESTRATOR WITH PLUGIN SUPPORT - EXAMPLE")
    print("="*80 + "\n")
    
    # Initialize orchestrator with plugins
    print("1. Initializing Plugin-Enabled Orchestrator...")
    orchestrator = PluginEnabledOrchestrator(
        config={},
        plugin_dir='./plugins',
        registry_dir='./plugin_registry',
        enable_plugin_security=False  # Disable for example
    )
    print("✓ Orchestrator initialized with plugin support\n")
    
    # Load plugins
    print("2. Loading Plugins...")
    
    # Load data processor plugin
    success = orchestrator.load_plugin_for_task(
        plugin_name='data_processor',
        config={}
    )
    print(f"   {'✓' if success else '✗'} Data Processor Plugin")
    
    # Load agent skill plugin
    success = orchestrator.load_plugin_for_task(
        plugin_name='agent_skill',
        config={'max_history': 100}
    )
    print(f"   {'✓' if success else '✗'} Agent Skill Plugin\n")
    
    # Get available capabilities
    print("3. Available Plugin Capabilities:")
    capabilities = orchestrator.get_available_plugin_capabilities()
    for plugin_name, caps in capabilities.items():
        print(f"   - {plugin_name}: {', '.join(caps)}")
    print()
    
    # Execute task with plugins
    print("4. Executing Task with Data Processing Plugin...")
    
    task1 = {
        'task_id': 'task_001',
        'required_capabilities': ['data_processing'],
        'action': 'transform',
        'data': {
            'data': [1, 2, 3, 4, 5],
            'operation': 'multiply',
            'factor': 3
        }
    }
    
    result1 = orchestrator.execute_with_plugins(task1)
    
    if result1['success']:
        print(f"   ✓ Task executed successfully")
        print(f"   Input: [1, 2, 3, 4, 5]")
        if 'final_result' in result1:
            print(f"   Output: {result1['final_result']}")
    print()
    
    # Execute task with agent skill plugin
    print("5. Executing Task with Agent Skill Plugin...")
    
    task2 = {
        'task_id': 'task_002',
        'required_capabilities': ['agent_skill'],
        'action': 'analyze_task',
        'data': {
            'task_description': 'Build a comprehensive data processing pipeline'
        }
    }
    
    result2 = orchestrator.execute_with_plugins(task2)
    
    if result2['success']:
        print(f"   ✓ Task executed successfully")
        if 'final_result' in result2 and 'analysis' in result2['final_result']:
            analysis = result2['final_result']['analysis']
            print(f"   Task Type: {analysis.get('task_type', 'N/A')}")
            print(f"   Keywords: {', '.join(analysis.get('keywords', []))}")
    print()
    
    # Direct plugin execution
    print("6. Direct Plugin Action Execution...")
    
    # Aggregate data
    result = orchestrator.execute_plugin_action(
        plugin_name='data_processor',
        action='aggregate',
        params={
            'data': [10, 20, 30, 40, 50],
            'function': 'avg'
        }
    )
    
    if result['success']:
        print(f"   ✓ Aggregated [10, 20, 30, 40, 50]")
        print(f"   Average: {result['result']['result']}")
    print()
    
    # Estimate complexity
    result = orchestrator.execute_plugin_action(
        plugin_name='agent_skill',
        action='estimate_complexity',
        params={
            'task_description': 'Implement a secure authentication system with OAuth'
        }
    )
    
    if result['success']:
        estimate = result['result']['estimate']
        print(f"   ✓ Complexity Estimated")
        print(f"   Level: {estimate['complexity_level']}")
        print(f"   Score: {estimate['complexity_score']:.2f}")
        print(f"   Time: {estimate['estimated_time']}")
    print()
    
    # Get plugin statistics
    print("7. Plugin Statistics:")
    stats = orchestrator.get_plugin_stats()
    
    exec_stats = stats['execution_stats']
    print(f"   Total Executions: {exec_stats['total_executions']}")
    print(f"   Successful: {exec_stats['successful_executions']}")
    print(f"   Failed: {exec_stats['failed_executions']}")
    print(f"   Success Rate: {(exec_stats['successful_executions'] / max(exec_stats['total_executions'], 1) * 100):.1f}%")
    
    print(f"\n   Plugins Used:")
    for plugin_name, count in exec_stats['plugins_used'].items():
        print(f"   - {plugin_name}: {count} executions")
    print()
    
    print("="*80)
    print("EXAMPLE COMPLETED SUCCESSFULLY")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
