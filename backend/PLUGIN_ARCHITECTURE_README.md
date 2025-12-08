
# Secure Plugin Architecture

## Overview

The Secure Plugin Architecture enables dynamic capability extension for the agent platform through a sandboxed, verified plugin system. This allows agents to gain new skills and capabilities without requiring full system redeployment.

## 🎯 Key Features

### Security & Verification
- **Cryptographic Signing**: All plugins are signed using HMAC-SHA256
- **Signature Verification**: Automatic validation of plugin signatures
- **Sandboxed Execution**: Restricted execution environment
- **Permission System**: Fine-grained permission control
- **Import Validation**: Prevents malicious imports

### Plugin Management
- **Dynamic Loading**: Load/unload plugins at runtime
- **Version Control**: Support for multiple plugin versions
- **Registry System**: Centralized plugin repository
- **Dependency Management**: Handle plugin dependencies
- **Lifecycle Management**: Complete plugin lifecycle control

### Capabilities
- **Data Processing**: Transform and analyze data
- **Model Inference**: Run custom models
- **Agent Skills**: Extend agent capabilities
- **Integrations**: Connect to external services
- **Visualization**: Custom data visualization
- **Monitoring**: Custom monitoring capabilities

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Plugin Service                            │
│  (Orchestrates plugin management and execution)              │
└──────────┬──────────────────────────────────┬───────────────┘
           │                                   │
    ┌──────▼──────┐                    ┌──────▼──────────┐
    │   Plugin    │                    │     Plugin      │
    │   Loader    │                    │    Registry     │
    │  (Runtime)  │                    │  (Repository)   │
    └──────┬──────┘                    └──────┬──────────┘
           │                                   │
    ┌──────▼──────┐                    ┌──────▼──────────┐
    │   Plugin    │                    │     Plugin      │
    │  Security   │                    │   Validator     │
    │  (Sandbox)  │                    │  (Verification) │
    └─────────────┘                    └─────────────────┘
```

## 📦 Components

### 1. Plugin Base (`plugin_base.py`)
- `PluginInterface`: Base class for all plugins
- `PluginMetadata`: Plugin information container
- `PluginCapability`: Enumeration of capabilities
- `PluginPermission`: Permission types

### 2. Plugin Security (`plugin_security.py`)
- `PluginSignature`: Handles signing and verification
- `PluginSandbox`: Implements execution sandboxing
- `PluginValidator`: Validates plugin compliance

### 3. Plugin Loader (`plugin_loader.py`)
- `PluginLoader`: Manages plugin loading and execution
- `PluginInstance`: Represents loaded plugin instance
- Dynamic module loading
- Lifecycle management

### 4. Plugin Registry (`plugin_registry.py`)
- `PluginRegistry`: Manages plugin repository
- `PluginRegistryEntry`: Registry entry representation
- Version management
- Plugin discovery and search

### 5. Plugin Service (`plugin_service.py`)
- `PluginService`: High-level plugin API
- Installation and uninstallation
- Loading and execution
- Statistics and monitoring

## 🚀 Getting Started

### Installation

```python
from core.plugin_service import PluginService

# Initialize plugin service
plugin_service = PluginService(
    plugin_dir='./plugins',
    registry_dir='./plugin_registry',
    enable_security=True
)
```

### Creating a Plugin

```python
from core.plugin_base import (
    PluginInterface,
    PluginMetadata,
    PluginCapability,
    PluginPermission
)

class MyPlugin(PluginInterface):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            author="Your Name",
            description="My custom plugin",
            capabilities=[PluginCapability.DATA_PROCESSING],
            required_permissions=[PluginPermission.FILE_READ]
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        # Initialize plugin
        return True
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Execute plugin action
        return {"success": True, "result": "..."}
    
    def get_available_actions(self) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'process',
                'description': 'Process data',
                'parameters': {'data': 'Input data'}
            }
        ]
    
    def shutdown(self) -> bool:
        # Cleanup
        return True
```

### Installing a Plugin

```python
# Define plugin metadata
metadata = {
    'name': 'my_plugin',
    'version': '1.0.0',
    'author': 'Your Name',
    'description': 'My custom plugin',
    'capabilities': ['data_processing'],
    'required_permissions': ['file_read']
}

# Install plugin
result = plugin_service.install_plugin(
    plugin_path='./my_plugin.py',
    metadata=metadata,
    auto_load=True
)

if result['success']:
    print(f"Plugin installed: {result['plugin']}")
```

### Executing Plugin Actions

```python
# Execute plugin action
result = plugin_service.execute_plugin_action(
    plugin_name='my_plugin',
    action='process',
    params={'data': [1, 2, 3, 4, 5]}
)

if result['success']:
    print(f"Result: {result['result']}")
```

## 🔌 REST API

### Install Plugin
```bash
POST /api/plugins/install
Content-Type: application/json

{
  "plugin_path": "/path/to/plugin.py",
  "metadata": {
    "name": "plugin_name",
    "version": "1.0.0",
    "author": "Author Name",
    "description": "Plugin description",
    "capabilities": ["data_processing"],
    "required_permissions": ["file_read"]
  },
  "auto_load": true
}
```

### Load Plugin
```bash
POST /api/plugins/load/{plugin_name}
Content-Type: application/json

{
  "version": "1.0.0",
  "config": {}
}
```

### Execute Action
```bash
POST /api/plugins/execute/{plugin_name}/{action}
Content-Type: application/json

{
  "params": {
    "data": [1, 2, 3, 4, 5]
  }
}
```

### List Plugins
```bash
GET /api/plugins/loaded
GET /api/plugins/available?capability=data_processing
```

### Get Plugin Info
```bash
GET /api/plugins/info/{plugin_name}
```

### Unload Plugin
```bash
POST /api/plugins/unload/{plugin_name}
```

### Uninstall Plugin
```bash
DELETE /api/plugins/uninstall/{plugin_name}?version=1.0.0
```

## 📊 Example Plugins

### 1. Data Processor Plugin
Located at: `plugins/example_data_processor.py`

**Capabilities:**
- Transform data (multiply, add, power)
- Filter data (greater, less, equal)
- Aggregate data (sum, avg, min, max)
- Normalize data

**Usage:**
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
# Result: [2, 4, 6, 8, 10]
```

### 2. Agent Skill Plugin
Located at: `plugins/example_agent_skill.py`

**Capabilities:**
- Analyze tasks
- Suggest approaches
- Estimate complexity
- Decompose tasks

**Usage:**
```python
result = plugin_service.execute_plugin_action(
    plugin_name='agent_skill',
    action='analyze_task',
    params={
        'task_description': 'Build a machine learning pipeline'
    }
)
```

## 🔒 Security

### Permission System
Plugins must declare required permissions:
- `FILE_READ`: Read files
- `FILE_WRITE`: Write files
- `NETWORK_ACCESS`: Access network
- `DATABASE_READ`: Read from database
- `DATABASE_WRITE`: Write to database
- `EXECUTE_CODE`: Execute arbitrary code
- `SYSTEM_ACCESS`: Access system resources
- `AGENT_CONTROL`: Control agent behavior

### Sandboxing
- Restricted imports (no os, sys, subprocess)
- Limited built-in functions
- Isolated execution environment
- Permission validation

### Verification
- Cryptographic signature verification
- File hash validation
- Import checking
- Metadata validation

## 📈 Monitoring

### Service Statistics
```python
stats = plugin_service.get_service_stats()
print(f"Loaded plugins: {stats['loaded_plugins']}")
print(f"Total plugins: {stats['registry']['total_plugins']}")
print(f"Active plugins: {stats['registry']['active_plugins']}")
```

### Plugin Health
```python
info = plugin_service.get_plugin_info('my_plugin')
print(f"Status: {info['health']['status']}")
print(f"Executions: {info['execution_count']}")
print(f"Errors: {info['error_count']}")
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/test_plugin_system.py -v
```

Run the example:
```bash
python examples/plugin_system_example.py
```

## 🔧 Configuration

### Environment Variables
- `PLUGIN_SECRET_KEY`: Secret key for plugin signing
- `PLUGIN_DIR`: Default plugin directory
- `REGISTRY_DIR`: Default registry directory

### Plugin Configuration
Each plugin can receive custom configuration during initialization:
```python
config = {
    'max_retries': 3,
    'timeout': 30,
    'custom_setting': 'value'
}

plugin_service.load_plugin('my_plugin', config=config)
```

## 📚 Best Practices

1. **Always Sign Plugins**: Use cryptographic signing for production
2. **Minimal Permissions**: Request only required permissions
3. **Error Handling**: Implement robust error handling
4. **Documentation**: Document all actions and parameters
5. **Testing**: Write comprehensive tests
6. **Versioning**: Use semantic versioning
7. **Dependencies**: Minimize external dependencies
8. **Performance**: Optimize execution time
9. **Logging**: Use proper logging
10. **Cleanup**: Always implement proper shutdown

## 🐛 Troubleshooting

### Plugin Load Failure
- Check signature validity
- Verify permissions
- Validate imports
- Check metadata completeness

### Execution Errors
- Review plugin logs
- Check parameter types
- Verify plugin is active
- Check execution count

### Registry Issues
- Verify registry directory permissions
- Check registry file integrity
- Validate plugin registration

## 🚀 Production Deployment

### Prerequisites
1. Set `PLUGIN_SECRET_KEY` environment variable
2. Configure plugin and registry directories
3. Enable security features
4. Set up monitoring

### Integration
```python
# In app.py
from api.plugin_routes import plugin_api

app.register_blueprint(plugin_api)
```

### Security Checklist
- [ ] Secret key configured
- [ ] Security enabled
- [ ] Permissions validated
- [ ] Signatures verified
- [ ] Sandboxing active
- [ ] Monitoring enabled
- [ ] Logs configured

## 📖 Additional Resources

- Example plugins in `/plugins/`
- Test suite in `/tests/test_plugin_system.py`
- Example usage in `/examples/plugin_system_example.py`
- API documentation in this README

## 🎉 Summary

The Secure Plugin Architecture provides a production-ready system for extending agent capabilities dynamically while maintaining security and stability. It supports:

- ✅ Cryptographic signing and verification
- ✅ Sandboxed execution
- ✅ Permission management
- ✅ Version control
- ✅ Dynamic loading
- ✅ Registry system
- ✅ REST API
- ✅ Monitoring
- ✅ Example plugins
- ✅ Comprehensive testing

The system is ready for deployment and can be extended with custom plugins to meet specific business needs.
