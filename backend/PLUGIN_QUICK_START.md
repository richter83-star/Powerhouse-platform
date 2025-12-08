# Plugin Architecture - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Import the Plugin Service
```python
from core.plugin_service import PluginService

# Initialize
plugin_service = PluginService(
    plugin_dir='./plugins',
    registry_dir='./plugin_registry',
    enable_security=True
)
```

### Step 2: Install a Plugin
```python
# Define metadata
metadata = {
    'name': 'data_processor',
    'version': '1.0.0',
    'author': 'Powerhouse',
    'description': 'Data processing plugin',
    'capabilities': ['data_processing'],
    'required_permissions': ['file_read']
}

# Install
result = plugin_service.install_plugin(
    plugin_path='./plugins/example_data_processor.py',
    metadata=metadata,
    auto_load=True
)
```

### Step 3: Execute Plugin Action
```python
result = plugin_service.execute_plugin_action(
    plugin_name='data_processor',
    action='transform',
    params={
        'data': [1, 2, 3, 4, 5],
        'operation': 'multiply',
        'factor': 2
    }
)

print(result['result'])  # Output: [2, 4, 6, 8, 10]
```

## 🔌 Using with Orchestrator

```python
from core.orchestrator_with_plugins import PluginEnabledOrchestrator

# Initialize
orchestrator = PluginEnabledOrchestrator()

# Load plugin
orchestrator.load_plugin_for_task('data_processor')

# Execute task with plugins
task = {
    'task_id': 'task_001',
    'required_capabilities': ['data_processing'],
    'action': 'transform',
    'data': {'data': [1,2,3], 'operation': 'multiply', 'factor': 2}
}

result = orchestrator.execute_with_plugins(task)
```

## 🌐 Using REST API

### Install Plugin
```bash
curl -X POST http://localhost:5000/api/plugins/install \
  -H "Content-Type: application/json" \
  -d '{
    "plugin_path": "./plugins/example_data_processor.py",
    "metadata": {
      "name": "data_processor",
      "version": "1.0.0",
      "author": "Powerhouse",
      "description": "Data processing plugin",
      "capabilities": ["data_processing"],
      "required_permissions": ["file_read"]
    },
    "auto_load": true
  }'
```

### Execute Action
```bash
curl -X POST http://localhost:5000/api/plugins/execute/data_processor/transform \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "data": [1, 2, 3, 4, 5],
      "operation": "multiply",
      "factor": 2
    }
  }'
```

### List Plugins
```bash
curl http://localhost:5000/api/plugins/loaded
curl http://localhost:5000/api/plugins/available
```

## 📝 Creating Your Own Plugin

```python
from core.plugin_base import (
    PluginInterface, PluginMetadata,
    PluginCapability, PluginPermission
)

class MyPlugin(PluginInterface):
    def get_metadata(self):
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            author="Your Name",
            description="My custom plugin",
            capabilities=[PluginCapability.CUSTOM],
            required_permissions=[PluginPermission.FILE_READ]
        )
    
    def initialize(self, config):
        self._initialized = True
        self._active = True
        return True
    
    def execute(self, action, params):
        if action == "my_action":
            # Your logic here
            return {"success": True, "result": "..."}
        return {"success": False, "error": "Unknown action"}
    
    def get_available_actions(self):
        return [
            {
                'name': 'my_action',
                'description': 'Does something cool',
                'parameters': {'param1': 'Description'}
            }
        ]
    
    def shutdown(self):
        self._active = False
        return True
```

## 🧪 Run Examples

```bash
# Basic example
python examples/plugin_system_example.py

# Orchestrator integration
python examples/orchestrator_with_plugins_example.py
```

## 🔒 Production Configuration

```python
import os

# Set secret key (IMPORTANT!)
os.environ['PLUGIN_SECRET_KEY'] = 'your-secure-key-here'

# Initialize with security
plugin_service = PluginService(
    plugin_dir='/var/lib/plugins',
    registry_dir='/var/lib/plugin_registry',
    enable_security=True
)
```

## 📚 Full Documentation
- **Main README**: `PLUGIN_ARCHITECTURE_README.md`
- **Implementation Summary**: `SECURE_PLUGIN_ARCHITECTURE_SUMMARY.md`
- **This Guide**: `PLUGIN_QUICK_START.md`

## ⚡ Common Operations

### Load Plugin
```python
plugin_service.load_plugin('plugin_name', config={})
```

### Unload Plugin
```python
plugin_service.unload_plugin('plugin_name')
```

### Get Stats
```python
stats = plugin_service.get_service_stats()
```

### Search Plugins
```python
plugins = plugin_service.list_available_plugins(
    capability='data_processing'
)
```

## 🐛 Troubleshooting

### Plugin Won't Load
- Check signature (if security enabled)
- Verify permissions
- Check imports (no restricted modules)
- Review logs

### Execution Fails
- Check if plugin is active
- Verify action exists
- Check parameters
- Review error logs

---

**Ready to Go!** 🎉

For detailed information, see `PLUGIN_ARCHITECTURE_README.md`
