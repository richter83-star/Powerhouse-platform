"""
OpenAI LLM provider implementation.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseLLMProvider, LLMResponse
from utils.errors import LLMError
from utils.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider implementation.
    
    Supports GPT-4, GPT-3.5-turbo, and other OpenAI models.
    """
    
    def __init__(self, api_key: str, default_model: str = "gpt-4", **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            default_model: Default model (e.g., 'gpt-4', 'gpt-3.5-turbo')
            **kwargs: Additional configuration
        """
        super().__init__(api_key, default_model, **kwargs)
        self.client = openai.OpenAI(api_key=api_key)
        self.validate_config()
        logger.info(f"Initialized OpenAI provider with model: {default_model}")
    
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
        Invoke OpenAI API.
        
        Args:
            prompt: User message
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            system_prompt: System message
            json_mode: Enable JSON mode
            tools: Function calling tools
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse: Standardized response
            
        Raises:
            LLMError: If API call fails
        """
        try:
            model = model or self.default_model
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Build request parameters
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            
            if json_mode:
                params["response_format"] = {"type": "json_object"}
            
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            
            # Merge additional kwargs
            params.update(kwargs)
            
            logger.debug(f"Invoking OpenAI with model={model}, temperature={temperature}")
            
            # Make API call
            response = self.client.chat.completions.create(**params)
            
            # Extract response
            message = response.choices[0].message
            content = message.content or ""
            
            # Handle function calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                content = {
                    "content": content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "function": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                        for tc in message.tool_calls
                    ]
                }
            
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    "id": response.id,
                    "created": response.created,
                    "system_fingerprint": getattr(response, 'system_fingerprint', None)
                },
                timestamp=datetime.now()
            )
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMError(f"OpenAI API error: {str(e)}", {"provider": "openai", "model": model})
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI provider: {e}")
            raise LLMError(f"Unexpected error: {str(e)}", {"provider": "openai"})
    
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
        Invoke OpenAI API with streaming.
        
        Yields:
            str: Text chunks
        """
        try:
            model = model or self.default_model
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            
            params.update(kwargs)
            
            stream = self.client.chat.completions.create(**params)
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise LLMError(f"Streaming error: {str(e)}", {"provider": "openai"})
    
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens using tiktoken.
        
        Args:
            text: Text to count
            model: Model for tokenization
            
        Returns:
            int: Token count
        """
        try:
            import tiktoken
            model = model or self.default_model
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed, using approximation: {e}")
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4
