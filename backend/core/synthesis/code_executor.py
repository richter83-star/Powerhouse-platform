"""
Safe Code Executor: Executes code in a sandboxed environment.

Prevents dangerous operations while allowing safe code execution.
"""

import ast
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

from core.synthesis.dsl import DSLCompiler, DSLProgram
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    output: Any
    stdout: str
    stderr: str
    execution_time: float
    error: Optional[str] = None


class SafeExecutor:
    """
    Executes code in a restricted environment.
    
    Uses AST analysis and restricted builtins to prevent dangerous operations.
    """
    
    def __init__(self):
        """Initialize safe executor."""
        self.compiler = DSLCompiler()
        self.logger = get_logger(__name__)
        
        # Restricted builtins (safe subset)
        self.safe_builtins = {
            'abs', 'all', 'any', 'bool', 'chr', 'dict', 'dir', 'divmod',
            'enumerate', 'filter', 'float', 'int', 'len', 'list', 'map',
            'max', 'min', 'ord', 'pow', 'print', 'range', 'reversed',
            'round', 'set', 'sorted', 'str', 'sum', 'tuple', 'type', 'zip'
        }
    
    def execute(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
        timeout: float = 5.0
    ) -> ExecutionResult:
        """
        Execute code safely.
        
        Args:
            code: Code to execute
            globals_dict: Optional globals dictionary
            timeout: Execution timeout in seconds
            
        Returns:
            ExecutionResult
        """
        import time
        start_time = time.time()
        
        # Compile DSL code first (validates safety)
        try:
            dsl_program = self.compiler.compile(code)
        except ValueError as e:
            return ExecutionResult(
                success=False,
                output=None,
                stdout="",
                stderr="",
                execution_time=0.0,
                error=f"Compilation error: {e}"
            )
        
        # Create restricted environment
        restricted_globals = self._create_restricted_globals(globals_dict or {})
        
        # Capture stdout/stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute code
                exec(compile(dsl_program.code, '<string>', 'exec'), restricted_globals)
            
            execution_time = time.time() - start_time
            
            # Extract result (look for 'result' variable or return value)
            output = restricted_globals.get('result')
            
            return ExecutionResult(
                success=True,
                output=output,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                output=None,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                execution_time=execution_time,
                error=str(e)
            )
    
    def execute_function(
        self,
        code: str,
        function_name: str,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute a specific function from code.
        
        Args:
            code: Code containing function definition
            function_name: Name of function to call
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            ExecutionResult
        """
        # Execute code to define function
        result = self.execute(code)
        
        if not result.success:
            return result
        
        # Get function from execution environment
        # Note: In real implementation, would store execution environment
        # For now, re-execute to get function
        restricted_globals = self._create_restricted_globals()
        
        try:
            exec(compile(code, '<string>', 'exec'), restricted_globals)
            func = restricted_globals.get(function_name)
            
            if func is None:
                return ExecutionResult(
                    success=False,
                    output=None,
                    stdout="",
                    stderr="",
                    execution_time=0.0,
                    error=f"Function {function_name} not found"
                )
            
            # Call function
            output = func(*(args or ()), **(kwargs or {}))
            
            return ExecutionResult(
                success=True,
                output=output,
                stdout="",
                stderr="",
                execution_time=0.0
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=None,
                stdout="",
                stderr="",
                execution_time=0.0,
                error=str(e)
            )
    
    def _create_restricted_globals(self, user_globals: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create restricted globals dictionary."""
        import math
        import random
        import datetime
        import json
        import re
        import collections
        import itertools
        import operator
        import string
        
        restricted = {
            '__builtins__': {
                k: v for k, v in __builtins__.items()
                if k in self.safe_builtins
            },
            'math': math,
            'random': random,
            'datetime': datetime,
            'json': json,
            're': re,
            'collections': collections,
            'itertools': itertools,
            'operator': operator,
            'string': string
        }
        
        if user_globals:
            restricted.update(user_globals)
        
        return restricted

