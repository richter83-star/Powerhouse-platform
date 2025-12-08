"""
Anthropic (Claude) LLM provider implementation.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseLLMProvider, LLMResponse
from utils.errors import LLMError
from utils.logging import get_logger

logger = get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude API provider implementation.
    
    Supports Claude 3 models (Opus, Sonnet, Haiku).
    """
    
    def __init__(self, api_key: str, default_model: str = "claude-3-sonnet-20240229", **kwargs):
        """
        Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            default_model: Default Claude model
            **kwargs: Additional configuration
        """
        super().__init__(api_key, default_model, **kwargs)
        self.client = anthropic.Anthropic(api_key=api_key)
        self.validate_config()
        logger.info(f"Initialized Anthropic provider with model: {default_model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
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
        Invoke Anthropic API.
        
        Args:
            prompt: User message
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            system_prompt: System message
            json_mode: Enable JSON mode (via system prompt)
            tools: Tool definitions
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse: Standardized response
            
        Raises:
            LLMError: If API call fails
        """
        try:
            model = model or self.default_model
            max_tokens = max_tokens or 2000
            
            # Build request parameters
            params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # Add system prompt
            if system_prompt:
                if json_mode:
                    system_prompt += "\n\nYou must respond with valid JSON only."
                params["system"] = system_prompt
            elif json_mode:
                params["system"] = "You must respond with valid JSON only."
            
            # Add tools if provided
            if tools:
                params["tools"] = tools
            
            # Merge additional kwargs
            params.update(kwargs)
            
            logger.debug(f"Invoking Anthropic with model={model}, temperature={temperature}")
            
            # Make API call
            response = self.client.messages.create(**params)
            
            # Extract content
            content = ""
            tool_calls = []
            
            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "function": block.name,
                        "arguments": block.input
                    })
            
            # If tool calls exist, structure response
            if tool_calls:
                content = {
                    "content": content,
                    "tool_calls": tool_calls
                }
            
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.stop_reason,
                metadata={
                    "id": response.id,
                    "type": response.type,
                    "role": response.role
                },
                timestamp=datetime.now()
            )
            
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMError(f"Anthropic API error: {str(e)}", {"provider": "anthropic", "model": model})
        except Exception as e:
            logger.error(f"Unexpected error in Anthropic provider: {e}")
            raise LLMError(f"Unexpected error: {str(e)}", {"provider": "anthropic"})
    
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
        Invoke Anthropic API with streaming.
        
        Yields:
            str: Text chunks
        """
        try:
            model = model or self.default_model
            max_tokens = max_tokens or 2000
            
            params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            if system_prompt:
                params["system"] = system_prompt
            
            params.update(kwargs)
            
            with self.client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise LLMError(f"Streaming error: {str(e)}", {"provider": "anthropic"})
    
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens using Anthropic's token counter.
        
        Args:
            text: Text to count
            model: Model for tokenization
            
        Returns:
            int: Token count
        """
        try:
            # Anthropic provides a count_tokens method
            count = self.client.count_tokens(text)
            return count
        except Exception as e:
            logger.warning(f"Token counting failed, using approximation: {e}")
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4
