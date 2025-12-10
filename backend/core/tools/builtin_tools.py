"""
Built-in tools for agents.
"""

import re
import json
from typing import Any, Dict
from core.tools.base_tool import BaseTool, ToolResult


class SearchTool(BaseTool):
    """Mock search tool for demonstration."""
    
    def __init__(self):
        super().__init__(
            name="search",
            description="Search for information on a given query"
        )
    
    def execute(self, query: str) -> ToolResult:
        """
        Execute search.
        
        Args:
            query: Search query
        """
        # Mock implementation
        return ToolResult(
            success=True,
            output=f"Search results for '{query}': [This is a mock search tool. In production, this would connect to a real search API.]",
            metadata={"query": query}
        )
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }


class CalculatorTool(BaseTool):
    """Calculator tool for mathematical expressions."""
    
    def __init__(self):
        super().__init__(
            name="calculate",
            description="Evaluate a mathematical expression safely"
        )
    
    def execute(self, expression: str) -> ToolResult:
        """
        Calculate mathematical expression.
        
        Args:
            expression: Mathematical expression to evaluate
        """
        try:
            # Basic safety: only allow numbers, operators, and basic functions
            safe_pattern = r'^[0-9+\-*/().\s]+$'
            if not re.match(safe_pattern, expression):
                return ToolResult(
                    success=False,
                    output=None,
                    error="Expression contains unsafe characters"
                )
            
            # Use eval for simple expressions (in production, use a proper parser)
            result = eval(expression)
            return ToolResult(
                success=True,
                output=str(result),
                metadata={"expression": expression, "result": result}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')"
                }
            },
            "required": ["expression"]
        }


class LookupTool(BaseTool):
    """Lookup tool for key-value lookups."""
    
    def __init__(self, lookup_data: Dict[str, Any] = None):
        """
        Initialize lookup tool.
        
        Args:
            lookup_data: Dictionary of lookup data (default: empty)
        """
        super().__init__(
            name="lookup",
            description="Look up a value by key in a knowledge base"
        )
        self.lookup_data = lookup_data or {}
    
    def execute(self, key: str) -> ToolResult:
        """
        Look up a key.
        
        Args:
            key: Key to look up
        """
        if key in self.lookup_data:
            return ToolResult(
                success=True,
                output=self.lookup_data[key],
                metadata={"key": key}
            )
        else:
            return ToolResult(
                success=False,
                output=None,
                error=f"Key '{key}' not found in lookup data"
            )
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The key to look up"
                }
            },
            "required": ["key"]
        }


def get_default_tools():
    """Get list of default built-in tools."""
    return [
        SearchTool(),
        CalculatorTool(),
        LookupTool()
    ]

