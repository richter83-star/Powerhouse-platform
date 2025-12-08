
"""
RouteLLM provider implementation using Abacus.AI's intelligent routing service.

RouteLLM automatically selects the best model for each task, optimizing for
quality, cost, or a balance of both. Supports GPT-4, Claude-3, Gemini, and more.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import requests
import json

from .base import BaseLLMProvider, LLMResponse
from utils.logging import get_logger
from utils.errors import LLMError

logger = get_logger(__name__)


class RouteLLMProvider(BaseLLMProvider):
    """
    RouteLLM provider that uses Abacus.AI's intelligent model routing.
    
    Features:
    - Automatic model selection based on task complexity
    - Cost optimization while maintaining quality
    - Access to GPT-4, GPT-3.5, Claude-3, Gemini, Llama, Mistral, and more
    - Transparent routing decisions with metadata
    
    Routing Strategies:
    - 'quality-first': Prioritizes best models (GPT-4, Claude-3-Opus)
    - 'balanced': Smart mix for 90% quality at 40% cost (RECOMMENDED)
    - 'cost-optimized': Prefers cheaper models when sufficient
    """
    
    BASE_URL = "https://apps.abacus.ai/v1/chat/completions"
    
    def __init__(
        self,
        api_key: str,
        routing_strategy: str = "balanced",
        default_model: str = "auto",
        **kwargs
    ):
        """
        Initialize RouteLLM provider.
        
        Args:
            api_key: Abacus.AI API key
            routing_strategy: 'quality-first', 'balanced', or 'cost-optimized'
            default_model: Default to 'auto' for automatic routing
            **kwargs: Additional configuration
        """
        super().__init__(api_key=api_key, default_model=default_model, **kwargs)
        
        valid_strategies = ["quality-first", "balanced", "cost-optimized"]
        if routing_strategy not in valid_strategies:
            logger.warning(
                f"Invalid routing strategy '{routing_strategy}'. "
                f"Using 'balanced'. Valid: {valid_strategies}"
            )
            routing_strategy = "balanced"
        
        self.routing_strategy = routing_strategy
        self.base_url = self.BASE_URL
        
        logger.info(
            f"Initialized RouteLLM provider with strategy: {routing_strategy}"
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
        Invoke RouteLLM with automatic model selection.
        
        Args:
            prompt: User message/prompt
            model: Override automatic routing (e.g., 'gpt-4', 'claude-3-sonnet')
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            system_prompt: System instruction message
            json_mode: Force JSON output format
            tools: Function/tool definitions for function calling
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse: Response with content, model used, usage stats
        """
        # Build messages array
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Build request payload
        payload = {
            "messages": messages,
            "temperature": temperature,
        }
        
        # Add model if specified (overrides automatic routing)
        if model and model != "auto":
            payload["model"] = model
            logger.debug(f"Using explicit model: {model}")
        else:
            # Let RouteLLM decide based on strategy
            payload["routing_strategy"] = self.routing_strategy
            logger.debug(f"Using routing strategy: {self.routing_strategy}")
        
        # Add optional parameters
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        if tools:
            payload["tools"] = tools
        
        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in payload:
                payload[key] = value
        
        # Make API request
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            logger.debug(f"Sending request to RouteLLM: {self.base_url}")
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract response data
            content = data["choices"][0]["message"]["content"]
            model_used = data.get("model", "unknown")
            usage = data.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
            finish_reason = data["choices"][0].get("finish_reason", "stop")
            
            # Build metadata
            metadata = {
                "routing_strategy": self.routing_strategy,
                "model_selected": model_used,
                "explicit_model": model is not None and model != "auto",
            }
            
            # Add routing confidence if available
            if "routing_confidence" in data:
                metadata["routing_confidence"] = data["routing_confidence"]
            
            # Add cost information if available
            if "cost_usd" in data:
                metadata["cost_usd"] = data["cost_usd"]
            
            # Add function call if present
            if "function_call" in data["choices"][0]["message"]:
                metadata["function_call"] = data["choices"][0]["message"]["function_call"]
            
            logger.info(
                f"RouteLLM routed to {model_used} | "
                f"Tokens: {usage.get('total_tokens', 0)} | "
                f"Strategy: {self.routing_strategy}"
            )
            
            return LLMResponse(
                content=content,
                model=model_used,
                usage=usage,
                finish_reason=finish_reason,
                metadata=metadata,
                timestamp=datetime.now()
            )
            
        except requests.exceptions.RequestException as e:
            error_msg = f"RouteLLM API request failed: {str(e)}"
            logger.error(error_msg)
            
            # Try to extract error details from response
            try:
                error_data = e.response.json() if hasattr(e, 'response') else {}
                error_detail = error_data.get('error', {}).get('message', str(e))
                error_msg = f"RouteLLM API error: {error_detail}"
            except:
                pass
            
            raise LLMError(error_msg)
    
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
        Invoke RouteLLM with streaming response.
        
        Args:
            prompt: User message/prompt
            model: Override automatic routing
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: System instruction message
            **kwargs: Additional parameters
            
        Yields:
            str: Chunks of generated text
        """
        # Build messages array
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Build request payload
        payload = {
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        
        # Add model or routing strategy
        if model and model != "auto":
            payload["model"] = model
        else:
            payload["routing_strategy"] = self.routing_strategy
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in payload:
                payload[key] = value
        
        # Make streaming request
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                stream=True,
                timeout=60
            )
            response.raise_for_status()
            
            # Parse SSE stream
            for line in response.iter_lines():
                if not line:
                    continue
                
                line = line.decode('utf-8')
                
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    
                    if data_str == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(data_str)
                        delta = data.get('choices', [{}])[0].get('delta', {})
                        content = delta.get('content', '')
                        
                        if content:
                            yield content
                            
                    except json.JSONDecodeError:
                        continue
            
        except requests.exceptions.RequestException as e:
            error_msg = f"RouteLLM streaming request failed: {str(e)}"
            logger.error(error_msg)
            raise LLMError(error_msg)
    
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Estimate token count for text.
        
        This is a rough estimation. For exact counts, use tiktoken library.
        
        Args:
            text: Text to count tokens for
            model: Model to use for tokenization (ignored for estimation)
            
        Returns:
            int: Estimated token count
        """
        # Simple estimation: ~1.3 tokens per word
        # This works reasonably well for English text
        words = len(text.split())
        estimated_tokens = int(words * 1.3)
        
        return estimated_tokens
    
    def set_routing_strategy(self, strategy: str) -> None:
        """
        Change the routing strategy.
        
        Args:
            strategy: 'quality-first', 'balanced', or 'cost-optimized'
        """
        valid_strategies = ["quality-first", "balanced", "cost-optimized"]
        if strategy not in valid_strategies:
            raise ValueError(
                f"Invalid strategy '{strategy}'. Valid: {valid_strategies}"
            )
        
        self.routing_strategy = strategy
        logger.info(f"Updated routing strategy to: {strategy}")
    
    def get_analytics(self) -> Dict[str, Any]:
        """
        Get analytics about RouteLLM usage.
        
        Note: This is a placeholder. In production, you'd track this
        in a database or metrics system.
        
        Returns:
            Dict: Analytics data
        """
        return {
            "provider": "RouteLLM",
            "routing_strategy": self.routing_strategy,
            "status": "active"
        }

