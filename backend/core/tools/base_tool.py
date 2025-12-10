"""
Base tool interface for agent tool integration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseTool(ABC):
    """
    Base class for all tools that agents can use.
    
    Tools are functions or APIs that agents can invoke to interact
    with external systems, perform calculations, search, etc.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize tool.
        
        Args:
            name: Unique tool name
            description: Human-readable description of what the tool does
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult: Result of tool execution
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get OpenAPI-style schema for this tool.
        
        Returns:
            dict: Tool schema for LLM function calling
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameter_schema()
        }
    
    @abstractmethod
    def _get_parameter_schema(self) -> Dict[str, Any]:
        """
        Get parameter schema for this tool.
        
        Returns:
            dict: Parameter schema
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"

