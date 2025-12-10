"""
Tool registry for managing available tools.
"""

from typing import Dict, List, Optional, Any
from core.tools.base_tool import BaseTool
from utils.logging import get_logger

# Optional tool synthesis support
try:
    from core.tools.tool_synthesizer import ToolSynthesizer
    TOOL_SYNTHESIS_AVAILABLE = True
except ImportError:
    TOOL_SYNTHESIS_AVAILABLE = False
    ToolSynthesizer = None

logger = get_logger(__name__)


class ToolRegistry:
    """
    Registry for managing tools available to agents.
    
    Supports tool synthesis for dynamic tool creation.
    """
    
    def __init__(self, enable_synthesis: bool = True):
        """
        Initialize tool registry.
        
        Args:
            enable_synthesis: Enable tool synthesis capability
        """
        self._tools: Dict[str, BaseTool] = {}
        self.enable_synthesis = enable_synthesis
        self.synthesizer = None
        
        if enable_synthesis and TOOL_SYNTHESIS_AVAILABLE:
            self.synthesizer = ToolSynthesizer(tool_registry=self)
    
    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
        """
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} already registered, overwriting")
        
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def register_multiple(self, tools: List[BaseTool]) -> None:
        """
        Register multiple tools.
        
        Args:
            tools: List of tool instances
        """
        for tool in tools:
            self.register(tool)
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            BaseTool or None if not found
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get OpenAPI schemas for all tools.
        
        Returns:
            List of tool schemas for LLM function calling
        """
        return [tool.get_schema() for tool in self._tools.values()]
    
    def synthesize_tool(
        self,
        specification: str,
        tool_name: Optional[str] = None,
        examples: Optional[List[Dict[str, str]]] = None,
        constraints: Optional[List[str]] = None
    ) -> Optional[BaseTool]:
        """
        Synthesize a new tool from specification.
        
        Args:
            specification: Natural language tool specification
            tool_name: Optional tool name
            examples: Optional input/output examples
            constraints: Optional constraints
            
        Returns:
            Synthesized tool or None if synthesis disabled/failed
        """
        if not self.synthesizer:
            logger.warning("Tool synthesis not available")
            return None
        
        try:
            tool = self.synthesizer.synthesize_tool(
                specification=specification,
                tool_name=tool_name,
                examples=examples,
                constraints=constraints,
                auto_register=True  # Already registered by synthesizer
            )
            return tool
        except Exception as e:
            logger.error(f"Tool synthesis failed: {e}")
            return None
    
    def execute_tool(self, tool_name: str, **kwargs) -> Optional[Any]:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool parameters
            
        Returns:
            Tool result output or None if tool not found
        """
        tool = self.get(tool_name)
        if not tool:
            logger.error(f"Tool {tool_name} not found")
            return None
        
        try:
            result = tool.execute(**kwargs)
            if result.success:
                return result.output
            else:
                logger.error(f"Tool {tool_name} failed: {result.error}")
                return None
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return None


# Global tool registry instance
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry

