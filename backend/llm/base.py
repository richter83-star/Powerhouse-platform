"""
Base abstract class for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LLMResponse:
    """
    Standardized response from LLM providers.
    
    Attributes:
        content: The generated text content
        model: Model used for generation
        usage: Token usage information
        finish_reason: Reason for completion (e.g., 'stop', 'length', 'content_filter')
        metadata: Additional provider-specific metadata
        timestamp: When the response was generated
    """
    content: str
    model: str
    usage: Dict[str, int]  # e.g., {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    finish_reason: str
    metadata: Dict[str, Any]
    timestamp: datetime


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers must implement this interface to ensure consistent
    behavior across different providers (OpenAI, Anthropic, etc.).
    """
    
    def __init__(self, api_key: str, default_model: str, **kwargs):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: API key for the provider
            default_model: Default model to use if not specified in invoke()
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.default_model = default_model
        self.config = kwargs
    
    @abstractmethod
    def invoke(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Invoke the LLM with a prompt.
        
        Args:
            prompt: The user prompt/message
            model: Model to use (defaults to provider's default_model)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            system_prompt: System/instruction prompt
            json_mode: Whether to enforce JSON output
            tools: List of tool/function definitions for function calling
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse: Standardized response object
            
        Raises:
            LLMError: If the API call fails
        """
        pass
    
    @abstractmethod
    def invoke_streaming(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """
        Invoke the LLM with streaming response.
        
        Args:
            prompt: The user prompt/message
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: System/instruction prompt
            **kwargs: Additional provider-specific parameters
            
        Yields:
            str: Chunks of generated text
            
        Raises:
            LLMError: If the API call fails
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in a text string.
        
        Args:
            text: Text to count tokens for
            model: Model to use for tokenization
            
        Returns:
            int: Number of tokens
        """
        pass
    
    def validate_config(self) -> bool:
        """
        Validate provider configuration.
        
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.api_key:
            from utils.errors import ConfigurationError
            raise ConfigurationError(f"API key not provided for {self.__class__.__name__}")
        return True
    
    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self.__class__.__name__.replace("Provider", "")
