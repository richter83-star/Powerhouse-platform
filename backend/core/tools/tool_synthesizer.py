"""
Tool Synthesizer: Enables agents to create their own tools dynamically.
"""

from typing import Dict, Any, Optional, List
from core.tools.base_tool import BaseTool, ToolResult
from core.tools.tool_registry import ToolRegistry
from core.synthesis.program_synthesizer import ProgramSynthesizer
from core.synthesis.code_executor import SafeExecutor, ExecutionResult
from core.synthesis.code_verifier import CodeVerifier
from utils.logging import get_logger

logger = get_logger(__name__)


class SynthesizedTool(BaseTool):
    """Tool created through program synthesis."""
    
    def __init__(self, name: str, description: str, code: str, parameters: Dict[str, Any]):
        """
        Initialize synthesized tool.
        
        Args:
            name: Tool name
            description: Tool description
            code: Generated code
            parameters: Tool parameters schema
        """
        super().__init__(name=name, description=description)
        self._code = code
        self._parameters = parameters
        self.executor = SafeExecutor()
        self.logger = get_logger(__name__)
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute synthesized tool."""
        from core.tools.base_tool import ToolResult
        
        # Find the main function in code
        function_name = self._extract_function_name(self._code)
        
        if not function_name:
            return ToolResult(
                success=False,
                output=None,
                error="No function found in synthesized code"
            )
        
        # Prepare arguments
        args = tuple(kwargs.values())
        
        # Execute
        result = self.executor.execute_function(
            code=self._code,
            function_name=function_name,
            args=args,
            kwargs=kwargs
        )
        
        if result.success:
            return ToolResult(
                success=True,
                output=result.output,
                metadata={"function": function_name}
            )
        else:
            return ToolResult(
                success=False,
                output=None,
                error=result.error
            )
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for tool."""
        if self._parameters:
            # Convert to JSON schema format
            properties = {}
            for param_name, param_info in self._parameters.items():
                if isinstance(param_info, dict):
                    properties[param_name] = {
                        "type": param_info.get("type", "string"),
                        "description": param_info.get("description", f"Parameter {param_name}")
                    }
                else:
                    properties[param_name] = {
                        "type": "string",
                        "description": f"Parameter {param_name}"
                    }
            
            return {
                "type": "object",
                "properties": properties,
                "required": list(properties.keys())
            }
        return {"type": "object", "properties": {}}
    
    def _extract_function_name(self, code: str) -> Optional[str]:
        """Extract function name from code."""
        import re
        # Look for def statements
        match = re.search(r'def\s+(\w+)\s*\(', code)
        if match:
            return match.group(1)
        return None


class ToolSynthesizer:
    """
    Synthesizes tools from natural language specifications.
    """
    
    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        """
        Initialize tool synthesizer.
        
        Args:
            tool_registry: Optional tool registry to register synthesized tools
        """
        self.synthesizer = ProgramSynthesizer()
        self.verifier = CodeVerifier()
        self.executor = SafeExecutor()
        self.tool_registry = tool_registry
        self.logger = get_logger(__name__)
    
    def synthesize_tool(
        self,
        specification: str,
        tool_name: Optional[str] = None,
        examples: Optional[List[Dict[str, str]]] = None,
        constraints: Optional[List[str]] = None,
        auto_register: bool = True
    ) -> SynthesizedTool:
        """
        Synthesize a tool from specification.
        
        Args:
            specification: Natural language tool specification
            tool_name: Optional tool name (generated if not provided)
            examples: Optional input/output examples
            constraints: Optional constraints (e.g., "no file I/O")
            auto_register: Whether to automatically register tool
            
        Returns:
            SynthesizedTool instance
        """
        # Add safety constraints
        safety_constraints = [
            "no file I/O operations",
            "no network access",
            "no system calls",
            "must be a pure function"
        ]
        if constraints:
            safety_constraints.extend(constraints)
        
        # Synthesize code
        program = self.synthesizer.synthesize(
            specification=specification,
            examples=examples,
            constraints=safety_constraints
        )
        
        # Verify code
        verification = self.verifier.verify(
            code=program.code,
            check_security=True
        )
        
        if not verification.is_valid:
            raise ValueError(f"Generated code failed verification: {verification.issues}")
        
        # Generate tool name if not provided
        if not tool_name:
            tool_name = self._generate_tool_name(specification)
        
        # Extract parameters from code
        parameters = self._extract_parameters(program.code)
        
        # Create tool
        tool = SynthesizedTool(
            name=tool_name,
            description=program.description or specification,
            code=program.code,
            parameters=parameters
        )
        
        # Register if requested
        if auto_register and self.tool_registry:
            self.tool_registry.register(tool)
            self.logger.info(f"Synthesized and registered tool: {tool_name}")
        
        return tool
    
    def _generate_tool_name(self, specification: str) -> str:
        """Generate tool name from specification."""
        # Simple heuristic: use first few words
        words = specification.split()[:3]
        name = "_".join(words).lower()
        # Clean up
        name = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
        return f"synthesized_{name}"
    
    def _extract_parameters(self, code: str) -> Dict[str, Any]:
        """Extract parameter schema from code."""
        import ast
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    params = {}
                    for arg in node.args.args:
                        param_name = arg.arg
                        # Skip 'self' parameter
                        if param_name == 'self':
                            continue
                        param_type = "string"  # Default
                        if arg.annotation:
                            if isinstance(arg.annotation, ast.Name):
                                py_type = arg.annotation.id.lower()
                                # Map Python types to JSON schema types
                                type_map = {
                                    "int": "integer",
                                    "float": "number",
                                    "str": "string",
                                    "bool": "boolean",
                                    "list": "array",
                                    "dict": "object"
                                }
                                param_type = type_map.get(py_type, "string")
                        params[param_name] = {
                            "type": param_type,
                            "description": f"Parameter {param_name}",
                            "required": True
                        }
                    return params if params else {}
        except Exception as e:
            self.logger.warning(f"Failed to extract parameters: {e}")
        
        return {}

