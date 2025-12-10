"""
Tests for Tool Framework (Phase 1)

Tests BaseTool, built-in tools, and ToolRegistry.
"""

import pytest
from unittest.mock import Mock

from core.tools.base_tool import BaseTool, ToolResult
from core.tools.builtin_tools import SearchTool, CalculatorTool, LookupTool
from core.tools.tool_registry import ToolRegistry


@pytest.mark.unit
class TestBaseTool:
    """Test BaseTool interface."""
    
    def test_tool_initialization(self):
        """Test tool initialization."""
        class TestTool(BaseTool):
            def execute(self, **kwargs):
                return ToolResult(success=True, output="test")
            
            def _get_parameter_schema(self):
                return {"type": "object", "properties": {}}
        
        tool = TestTool(name="test_tool", description="Test tool")
        assert tool.name == "test_tool"
        assert tool.description == "Test tool"
    
    def test_tool_schema(self):
        """Test tool schema generation."""
        class TestTool(BaseTool):
            def execute(self, **kwargs):
                return ToolResult(success=True, output="test")
            
            def _get_parameter_schema(self):
                return {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string"},
                        "param2": {"type": "number"}
                    }
                }
        
        tool = TestTool(name="test_tool", description="Test tool")
        schema = tool.get_schema()
        
        assert schema["name"] == "test_tool"
        assert schema["description"] == "Test tool"
        assert "parameters" in schema
        assert "param1" in schema["parameters"]["properties"]


@pytest.mark.unit
class TestBuiltinTools:
    """Test built-in tools."""
    
    def test_search_tool(self):
        """Test SearchTool."""
        tool = SearchTool()
        result = tool.execute(query="test query")
        
        assert isinstance(result, ToolResult)
        assert result.success
        assert result.output is not None
    
    def test_calculator_tool(self):
        """Test CalculatorTool with various expressions."""
        tool = CalculatorTool()
        
        # Test addition
        result = tool.execute(expression="2 + 2")
        assert result.success
        assert "4" in str(result.output)
        
        # Test multiplication
        result = tool.execute(expression="3 * 4")
        assert result.success
        assert "12" in str(result.output)
        
        # Test invalid expression
        result = tool.execute(expression="invalid + expression")
        assert not result.success or "error" in str(result.output).lower()
    
    def test_lookup_tool(self):
        """Test LookupTool."""
        # Test with initial data
        tool = LookupTool(lookup_data={"key1": "value1"})
        
        # Test lookup with existing key
        result = tool.execute(key="key1")
        assert isinstance(result, ToolResult)
        assert result.success
        assert "value1" in str(result.output)
        
        # Test lookup with missing key
        result2 = tool.execute(key="missing_key")
        assert isinstance(result2, ToolResult)
        assert not result2.success


@pytest.mark.unit
class TestToolRegistry:
    """Test ToolRegistry."""
    
    def test_tool_registration(self):
        """Test tool registration and lookup."""
        registry = ToolRegistry()
        tool = SearchTool()
        
        registry.register(tool)
        retrieved = registry.get("search")
        
        assert retrieved is not None
        assert retrieved.name == "search"
    
    def test_tool_execution(self):
        """Test tool execution via registry."""
        registry = ToolRegistry()
        tool = CalculatorTool()
        registry.register(tool)
        
        result = registry.execute_tool("calculate", expression="2 + 2")
        
        assert result is not None
        assert isinstance(result, str)  # execute_tool returns the output string
    
    def test_tool_discovery(self):
        """Test tool discovery by capability."""
        registry = ToolRegistry()
        registry.register(SearchTool())
        registry.register(CalculatorTool())
        registry.register(LookupTool())
        
        tools = registry.list_tools()
        assert len(tools) >= 3
        
        # Test finding tools by name
        search_tool = registry.get("search")
        assert search_tool is not None
    
    def test_multiple_tool_registration(self):
        """Test registering multiple tools at once."""
        registry = ToolRegistry()
        tools = [SearchTool(), CalculatorTool(), LookupTool()]
        
        registry.register_multiple(tools)
        
        assert len(registry.list_tools()) >= 3
    
    def test_nonexistent_tool(self):
        """Test handling of nonexistent tool."""
        registry = ToolRegistry()
        
        result = registry.get("nonexistent")
        assert result is None
        
        result = registry.execute_tool("nonexistent", param="value")
        assert result is None

