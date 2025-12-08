
"""
Plugin System Initialization
Makes example plugins easily importable.
"""

from pathlib import Path

# Plugin directory
PLUGIN_DIR = Path(__file__).parent

# Available example plugins
EXAMPLE_PLUGINS = [
    'example_data_processor',
    'example_agent_skill'
]

__all__ = ['PLUGIN_DIR', 'EXAMPLE_PLUGINS']
