"""
Code Verifier: Validates generated code for correctness and security.
"""

import ast
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

from core.synthesis.code_executor import SafeExecutor, ExecutionResult
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VerificationResult:
    """Result of code verification."""
    is_valid: bool
    syntax_valid: bool
    security_valid: bool
    test_valid: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class CodeVerifier:
    """
    Verifies generated code for correctness, security, and functionality.
    
    Checks:
    - Syntax validity
    - Security (no dangerous operations)
    - Test cases (if provided)
    - Code quality
    """
    
    def __init__(self):
        """Initialize code verifier."""
        self.executor = SafeExecutor()
        self.logger = get_logger(__name__)
    
    def verify(
        self,
        code: str,
        test_cases: Optional[List[Dict[str, Any]]] = None,
        check_security: bool = True
    ) -> VerificationResult:
        """
        Verify code.
        
        Args:
            code: Code to verify
            test_cases: Optional test cases [{"input": ..., "expected_output": ..., "function": "func_name"}]
            check_security: Whether to check security
            
        Returns:
            VerificationResult
        """
        issues = []
        warnings = []
        
        # Check syntax
        syntax_valid = self._check_syntax(code)
        if not syntax_valid:
            issues.append("Syntax errors detected")
        
        # Check security
        security_valid = True
        if check_security:
            security_valid, security_issues = self._check_security(code)
            issues.extend(security_issues)
        
        # Run test cases
        test_valid = True
        if test_cases:
            test_valid, test_issues = self._run_tests(code, test_cases)
            issues.extend(test_issues)
        
        is_valid = syntax_valid and security_valid and (test_valid if test_cases else True)
        
        return VerificationResult(
            is_valid=is_valid,
            syntax_valid=syntax_valid,
            security_valid=security_valid,
            test_valid=test_valid,
            issues=issues,
            warnings=warnings
        )
    
    def _check_syntax(self, code: str) -> bool:
        """Check Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    def _check_security(self, code: str) -> tuple[bool, List[str]]:
        """Check for security issues."""
        issues = []
        
        # Dangerous patterns
        dangerous_patterns = [
            (r'eval\s*\(', 'eval() calls'),
            (r'exec\s*\(', 'exec() calls'),
            (r'__import__', '__import__ usage'),
            (r'open\s*\(', 'file I/O operations'),
            (r'subprocess', 'subprocess calls'),
            (r'os\.system', 'os.system calls'),
        ]
        
        for pattern, description in dangerous_patterns:
            if re.search(pattern, code):
                issues.append(f"Security issue: {description}")
        
        return len(issues) == 0, issues
    
    def _run_tests(self, code: str, test_cases: List[Dict[str, Any]]) -> tuple[bool, List[str]]:
        """Run test cases."""
        issues = []
        
        for i, test_case in enumerate(test_cases):
            function_name = test_case.get("function")
            if not function_name:
                issues.append(f"Test case {i+1}: No function name specified")
                continue
            
            input_data = test_case.get("input")
            expected_output = test_case.get("expected_output")
            
            # Execute function
            result = self.executor.execute_function(
                code=code,
                function_name=function_name,
                args=input_data if isinstance(input_data, tuple) else (input_data,),
                kwargs=test_case.get("kwargs")
            )
            
            if not result.success:
                issues.append(f"Test case {i+1}: Execution failed - {result.error}")
                continue
            
            # Check output
            if result.output != expected_output:
                issues.append(
                    f"Test case {i+1}: Expected {expected_output}, got {result.output}"
                )
        
        return len(issues) == 0, issues

