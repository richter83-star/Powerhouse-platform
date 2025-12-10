"""
Domain-Specific Language (DSL) for agent-created tools.

Restricted language that prevents dangerous operations while allowing
useful tool creation.
"""

import ast
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DSLProgram:
    """Represents a DSL program."""
    code: str
    functions: List[str]  # List of function names defined
    allowed_imports: List[str] = None
    metadata: Dict[str, Any] = None


class DSLCompiler:
    """
    Compiler for restricted DSL.
    
    Validates that code only uses safe operations.
    """
    
    # Allowed operations
    ALLOWED_IMPORTS = {
        "math", "random", "datetime", "json", "re", "collections",
        "itertools", "operator", "string", "base64", "hashlib"
    }
    
    FORBIDDEN_OPERATIONS = {
        "open", "file", "__import__", "eval", "exec", "compile",
        "importlib", "subprocess", "os", "sys", "socket",
        "pickle", "shelve", "__builtins__"
    }
    
    def __init__(self):
        """Initialize DSL compiler."""
        self.logger = get_logger(__name__)
    
    def compile(self, code: str) -> DSLProgram:
        """
        Compile and validate DSL code.
        
        Args:
            code: DSL code to compile
            
        Returns:
            DSLProgram
            
        Raises:
            ValueError: If code contains forbidden operations
        """
        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Syntax error: {e}")
        
        # Analyze AST
        self._analyze_ast(tree)
        
        # Extract function definitions
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        
        # Extract imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Validate imports
        for imp in imports:
            if imp.split('.')[0] not in self.ALLOWED_IMPORTS:
                raise ValueError(f"Forbidden import: {imp}")
        
        return DSLProgram(
            code=code,
            functions=functions,
            allowed_imports=imports,
            metadata={
                "compiled_at": datetime.now().isoformat(),
                "num_functions": len(functions)
            }
        )
    
    def _analyze_ast(self, node: ast.AST) -> None:
        """Analyze AST for forbidden operations."""
        for child in ast.walk(node):
            # Check for forbidden function calls
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    if child.func.id in self.FORBIDDEN_OPERATIONS:
                        raise ValueError(f"Forbidden operation: {child.func.id}")
                elif isinstance(child.func, ast.Attribute):
                    # Check attribute access
                    if isinstance(child.func.value, ast.Name):
                        if child.func.value.id in self.FORBIDDEN_OPERATIONS:
                            raise ValueError(f"Forbidden module access: {child.func.value.id}")
            
            # Check for forbidden imports
            if isinstance(child, ast.Import):
                for alias in child.names:
                    if alias.name.split('.')[0] in self.FORBIDDEN_OPERATIONS:
                        raise ValueError(f"Forbidden import: {alias.name}")
            
            if isinstance(child, ast.ImportFrom):
                if child.module and child.module.split('.')[0] in self.FORBIDDEN_OPERATIONS:
                    raise ValueError(f"Forbidden import: {child.module}")

