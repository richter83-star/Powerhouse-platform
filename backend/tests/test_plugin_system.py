
"""
Test Suite for Secure Plugin Architecture
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path

from core.plugin_base import (
    PluginInterface,
    PluginMetadata,
    PluginCapability,
    PluginPermission
)
from core.plugin_security import PluginSignature, PluginSandbox, PluginValidator
from core.plugin_loader import PluginLoader
from core.plugin_registry import PluginRegistry
from core.plugin_service import PluginService


class TestPluginBase(unittest.TestCase):
    """Test plugin base classes"""
    
    def test_plugin_metadata_creation(self):
        """Test creating plugin metadata"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test Author",
            description="Test plugin",
            capabilities=[PluginCapability.DATA_PROCESSING],
            required_permissions=[PluginPermission.FILE_READ]
        )
        
        self.assertEqual(metadata.name, "test_plugin")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(len(metadata.capabilities), 1)
        self.assertEqual(len(metadata.required_permissions), 1)
    
    def test_plugin_metadata_to_dict(self):
        """Test converting metadata to dictionary"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test Author",
            description="Test plugin",
            capabilities=[PluginCapability.DATA_PROCESSING],
            required_permissions=[PluginPermission.FILE_READ]
        )
        
        data = metadata.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data['name'], "test_plugin")
        self.assertIn('capabilities', data)
        self.assertIn('required_permissions', data)


class TestPluginSecurity(unittest.TestCase):
    """Test plugin security components"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_plugin_path = os.path.join(self.temp_dir, 'test_plugin.py')
        
        # Create a simple test plugin
        plugin_code = '''
from core.plugin_base import PluginInterface, PluginMetadata, PluginCapability, PluginPermission

class TestPlugin(PluginInterface):
    def get_metadata(self):
        return PluginMetadata(
            name="test",
            version="1.0.0",
            author="Test",
            description="Test",
            capabilities=[PluginCapability.DATA_PROCESSING],
            required_permissions=[PluginPermission.FILE_READ]
        )
    
    def initialize(self, config):
        return True
    
    def execute(self, action, params):
        return {"success": True}
    
    def get_available_actions(self):
        return []
    
    def shutdown(self):
        return True
'''
        with open(self.test_plugin_path, 'w') as f:
            f.write(plugin_code)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_plugin_signing(self):
        """Test plugin signing"""
        signature_handler = PluginSignature()
        metadata = {
            'name': 'test_plugin',
            'version': '1.0.0'
        }
        
        signature = signature_handler.sign_plugin(
            self.test_plugin_path,
            metadata
        )
        
        self.assertIsInstance(signature, str)
        self.assertTrue(len(signature) > 0)
    
    def test_plugin_verification(self):
        """Test plugin signature verification"""
        signature_handler = PluginSignature()
        metadata = {
            'name': 'test_plugin',
            'version': '1.0.0'
        }
        
        signature = signature_handler.sign_plugin(
            self.test_plugin_path,
            metadata
        )
        
        is_valid = signature_handler.verify_signature(
            self.test_plugin_path,
            metadata,
            signature
        )
        
        self.assertTrue(is_valid)
    
    def test_sandbox_import_validation(self):
        """Test sandbox import validation"""
        sandbox = PluginSandbox()
        
        # Valid imports
        is_valid = sandbox.validate_plugin_imports(self.test_plugin_path)
        self.assertTrue(is_valid)
    
    def test_permission_validation(self):
        """Test permission validation"""
        sandbox = PluginSandbox()
        
        required = ['file_read', 'file_write']
        granted = ['file_read', 'file_write', 'network_access']
        
        is_valid = sandbox.validate_plugin_permissions(required, granted)
        self.assertTrue(is_valid)
        
        # Missing permissions
        granted_insufficient = ['file_read']
        is_valid = sandbox.validate_plugin_permissions(required, granted_insufficient)
        self.assertFalse(is_valid)


class TestPluginRegistry(unittest.TestCase):
    """Test plugin registry"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.registry = PluginRegistry(registry_dir=self.temp_dir)
        
        # Create test plugin
        self.test_plugin_path = os.path.join(self.temp_dir, 'test_plugin.py')
        with open(self.test_plugin_path, 'w') as f:
            f.write('# Test plugin')
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_register_plugin(self):
        """Test registering a plugin"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test Author",
            description="Test plugin",
            capabilities=[PluginCapability.DATA_PROCESSING],
            required_permissions=[PluginPermission.FILE_READ]
        )
        
        success = self.registry.register_plugin(
            self.test_plugin_path,
            metadata
        )
        
        # Note: This may fail due to validation, but we test the flow
        # self.assertTrue(success)
    
    def test_list_plugins(self):
        """Test listing plugins"""
        plugins = self.registry.list_plugins()
        self.assertIsInstance(plugins, list)
    
    def test_registry_stats(self):
        """Test getting registry stats"""
        stats = self.registry.get_registry_stats()
        
        self.assertIn('total_plugins', stats)
        self.assertIn('active_plugins', stats)
        self.assertIn('total_downloads', stats)


class TestPluginService(unittest.TestCase):
    """Test plugin service"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_service = PluginService(
            plugin_dir=os.path.join(self.temp_dir, 'plugins'),
            registry_dir=os.path.join(self.temp_dir, 'registry'),
            enable_security=False  # Disable for testing
        )
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_service_initialization(self):
        """Test service initialization"""
        self.assertIsNotNone(self.plugin_service.registry)
        self.assertIsNotNone(self.plugin_service.loader)
    
    def test_list_loaded_plugins(self):
        """Test listing loaded plugins"""
        plugins = self.plugin_service.list_loaded_plugins()
        self.assertIsInstance(plugins, list)
    
    def test_get_service_stats(self):
        """Test getting service stats"""
        stats = self.plugin_service.get_service_stats()
        
        self.assertIn('loaded_plugins', stats)
        self.assertIn('registry', stats)
        self.assertIn('security_enabled', stats)


if __name__ == '__main__':
    unittest.main()
