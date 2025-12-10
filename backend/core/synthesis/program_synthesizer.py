"""
Program Synthesizer: Generates code from natural language specifications.

Uses LLM to generate executable code from task descriptions.
"""

import ast
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from llm.base import BaseLLMProvider
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GeneratedProgram:
    """Represents a generated program."""
    code: str
    language: str
    description: str
    parameters: Dict[str, Any] = None
    metadata: Dict[str, Any] = None


class ProgramSynthesizer:
    """
    Synthesizes programs from natural language specifications.
    
    Generates code using LLM, validates syntax, and prepares for execution.
    """
    
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None, target_language: str = "python"):
        """
        Initialize program synthesizer.
        
        Args:
            llm_provider: LLM provider for code generation
            target_language: Target programming language
        """
        self.llm = llm_provider or LLMConfig.get_llm_provider("code_generation")
        self.target_language = target_language
        self.logger = get_logger(__name__)
    
    def synthesize(
        self,
        specification: str,
        examples: Optional[List[Dict[str, str]]] = None,  # [{"input": "...", "output": "..."}]
        constraints: Optional[List[str]] = None
    ) -> GeneratedProgram:
        """
        Synthesize program from specification.
        
        Args:
            specification: Natural language task description
            examples: Optional input/output examples
            constraints: Optional constraints (e.g., "no file I/O", "must be pure function")
            
        Returns:
            GeneratedProgram
        """
        prompt = self._build_prompt(specification, examples, constraints)
        
        try:
            response = self.llm.invoke(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for code generation
                max_tokens=2000,
                json_mode=True
            )
            
            # Parse response
            result = json.loads(response.content)
            
            code = result.get("code", "")
            description = result.get("description", specification)
            parameters = result.get("parameters", {})
            
            # Validate syntax
            if self.target_language == "python":
                self._validate_python_syntax(code)
            
            return GeneratedProgram(
                code=code,
                language=self.target_language,
                description=description,
                parameters=parameters,
                metadata={
                    "specification": specification,
                    "generated_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Program synthesis failed: {e}")
            raise
    
    def _build_prompt(
        self,
        specification: str,
        examples: Optional[List[Dict[str, str]]],
        constraints: Optional[List[str]]
    ) -> str:
        """Build prompt for code generation."""
        prompt = f"""Generate a {self.target_language} program that satisfies the following specification:

{specification}

"""
        
        if constraints:
            prompt += "Constraints:\n"
            for constraint in constraints:
                prompt += f"- {constraint}\n"
            prompt += "\n"
        
        if examples:
            prompt += "Examples:\n"
            for i, example in enumerate(examples, 1):
                prompt += f"Example {i}:\n"
                prompt += f"Input: {example['input']}\n"
                prompt += f"Output: {example['output']}\n\n"
        
        prompt += f"""Return a JSON object with:
{{
  "code": "the generated {self.target_language} code",
  "description": "brief description of what the code does",
  "parameters": {{"param_name": "description"}}
}}

Return only valid JSON, no markdown formatting."""
        
        return prompt
    
    def _validate_python_syntax(self, code: str) -> None:
        """Validate Python syntax."""
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Generated code has syntax errors: {e}")

