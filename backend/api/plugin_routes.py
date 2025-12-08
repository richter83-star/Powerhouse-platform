
"""
Secure Plugin Architecture - REST API Routes
Provides API endpoints for plugin management.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging

from core.plugin_service import PluginService
from core.plugin_base import PluginCapability, PluginPermission

logger = logging.getLogger(__name__)

# Initialize blueprint
plugin_api = Blueprint('plugin_api', __name__, url_prefix='/api/plugins')

# Initialize plugin service
plugin_service = PluginService(
    plugin_dir='./plugins',
    registry_dir='./plugin_registry',
    enable_security=True
)


@plugin_api.route('/install', methods=['POST'])
def install_plugin():
    """
    Install a new plugin.
    
    Request Body:
        {
            "plugin_path": "/path/to/plugin.py",
            "metadata": {
                "name": "plugin_name",
                "version": "1.0.0",
                "author": "author_name",
                "description": "Plugin description",
                "capabilities": ["data_processing"],
                "required_permissions": ["file_read"]
            },
            "auto_load": true
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'plugin_path' not in data or 'metadata' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        result = plugin_service.install_plugin(
            plugin_path=data['plugin_path'],
            metadata=data['metadata'],
            auto_load=data.get('auto_load', True)
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Install plugin error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@plugin_api.route('/uninstall/<plugin_name>', methods=['DELETE'])
def uninstall_plugin(plugin_name: str):
    """
    Uninstall a plugin.
    
    Query Parameters:
        version: Plugin version (optional)
    """
    try:
        version = request.args.get('version')
        
        result = plugin_service.uninstall_plugin(plugin_name, version)
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Uninstall plugin error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@plugin_api.route('/load/<plugin_name>', methods=['POST'])
def load_plugin(plugin_name: str):
    """
    Load a plugin.
    
    Request Body:
        {
            "version": "1.0.0",  // optional
            "config": {}  // optional
        }
    """
    try:
        data = request.get_json() or {}
        
        result = plugin_service.load_plugin(
            plugin_name=plugin_name,
            version=data.get('version'),
            config=data.get('config')
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Load plugin error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@plugin_api.route('/unload/<plugin_name>', methods=['POST'])
def unload_plugin(plugin_name: str):
    """Unload a plugin"""
    try:
        result = plugin_service.unload_plugin(plugin_name)
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Unload plugin error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@plugin_api.route('/execute/<plugin_name>/<action>', methods=['POST'])
def execute_plugin_action(plugin_name: str, action: str):
    """
    Execute a plugin action.
    
    Request Body:
        {
            "params": {}
        }
    """
    try:
        data = request.get_json() or {}
        params = data.get('params', {})
        
        result = plugin_service.execute_plugin_action(
            plugin_name=plugin_name,
            action=action,
            params=params
        )
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Execute plugin action error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@plugin_api.route('/info/<plugin_name>', methods=['GET'])
def get_plugin_info(plugin_name: str):
    """Get information about a loaded plugin"""
    try:
        info = plugin_service.get_plugin_info(plugin_name)
        
        if info:
            return jsonify({
                'success': True,
                'plugin': info
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Plugin not loaded'
            }), 404
            
    except Exception as e:
        logger.error(f"Get plugin info error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@plugin_api.route('/loaded', methods=['GET'])
def list_loaded_plugins():
    """List all loaded plugins"""
    try:
        plugins = plugin_service.list_loaded_plugins()
        
        return jsonify({
            'success': True,
            'plugins': plugins,
            'count': len(plugins)
        }), 200
        
    except Exception as e:
        logger.error(f"List loaded plugins error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@plugin_api.route('/available', methods=['GET'])
def list_available_plugins():
    """
    List available plugins in registry.
    
    Query Parameters:
        capability: Filter by capability
        author: Filter by author
        keyword: Search keyword
    """
    try:
        capability = request.args.get('capability')
        author = request.args.get('author')
        keyword = request.args.get('keyword')
        
        plugins = plugin_service.list_available_plugins(
            capability=capability,
            author=author,
            keyword=keyword
        )
        
        return jsonify({
            'success': True,
            'plugins': plugins,
            'count': len(plugins)
        }), 200
        
    except Exception as e:
        logger.error(f"List available plugins error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@plugin_api.route('/capabilities', methods=['GET'])
def list_capabilities():
    """List all available plugin capabilities"""
    try:
        capabilities = [
            {
                'value': cap.value,
                'name': cap.name
            }
            for cap in PluginCapability
        ]
        
        return jsonify({
            'success': True,
            'capabilities': capabilities
        }), 200
        
    except Exception as e:
        logger.error(f"List capabilities error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@plugin_api.route('/permissions', methods=['GET'])
def list_permissions():
    """List all available plugin permissions"""
    try:
        permissions = [
            {
                'value': perm.value,
                'name': perm.name
            }
            for perm in PluginPermission
        ]
        
        return jsonify({
            'success': True,
            'permissions': permissions
        }), 200
        
    except Exception as e:
        logger.error(f"List permissions error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@plugin_api.route('/stats', methods=['GET'])
def get_service_stats():
    """Get plugin service statistics"""
    try:
        stats = plugin_service.get_service_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Get service stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@plugin_api.route('/validate', methods=['POST'])
def validate_plugin():
    """
    Validate a plugin without installing.
    
    Request Body:
        {
            "plugin_path": "/path/to/plugin.py",
            "metadata": {}
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'plugin_path' not in data or 'metadata' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        result = plugin_service.validate_plugin(
            plugin_path=data['plugin_path'],
            metadata=data['metadata']
        )
        
        return jsonify({
            'success': True,
            'validation': result
        }), 200
        
    except Exception as e:
        logger.error(f"Validate plugin error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Health check endpoint
@plugin_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'plugin_service'
    }), 200
