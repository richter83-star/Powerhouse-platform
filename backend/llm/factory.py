"""
Factory for creating LLM provider instances.
"""

from typing import Optional, Dict, Any
from enum import Enum

from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .routellm_provider import RouteLLMProvider
from utils.errors import ConfigurationError
from utils.logging import get_logger

logger = get_logger(__name__)


class LLMProviderType(str, Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    ROUTELLM = "routellm"


class LLMFactory:
    """
    Factory for creating LLM provider instances.
    
    This factory makes it easy to instantiate the correct provider
    based on configuration and ensures consistent initialization.
    """
    
    _providers: Dict[LLMProviderType, type] = {
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.ANTHROPIC: AnthropicProvider,
        LLMProviderType.ROUTELLM: RouteLLMProvider,
    }
    
    @classmethod
    def create(
        cls,
        provider_type: str,
        api_key: str,
        default_model: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_type: Type of provider ('openai', 'anthropic')
            api_key: API key for the provider
            default_model: Default model to use
            **kwargs: Additional provider-specific configuration
            
        Returns:
            BaseLLMProvider: Initialized provider instance
            
        Raises:
            ConfigurationError: If provider type is unsupported or configuration is invalid
            
        Example:
            >>> factory = LLMFactory()
            >>> provider = factory.create("openai", api_key="sk-...", default_model="gpt-4")
            >>> response = provider.invoke("Hello, world!")
        """
        try:
            provider_enum = LLMProviderType(provider_type.lower())
        except ValueError:
            supported = ", ".join([p.value for p in LLMProviderType])
            raise ConfigurationError(
                f"Unsupported provider type: {provider_type}. Supported: {supported}"
            )
        
        provider_class = cls._providers.get(provider_enum)
        if not provider_class:
            raise ConfigurationError(f"Provider class not found for: {provider_type}")
        
        if not api_key:
            raise ConfigurationError(f"API key required for {provider_type}")
        
        # Set default model if not provided
        if not default_model:
            default_models = {
                LLMProviderType.OPENAI: "gpt-4",
                LLMProviderType.ANTHROPIC: "claude-3-sonnet-20240229",
                LLMProviderType.ROUTELLM: "auto"  # RouteLLM uses automatic routing
            }
            default_model = default_models.get(provider_enum)
        
        logger.info(f"Creating {provider_type} provider with model: {default_model}")
        
        return provider_class(
            api_key=api_key,
            default_model=default_model,
            **kwargs
        )
    
    @classmethod
    def register_provider(cls, provider_type: str, provider_class: type) -> None:
        """
        Register a custom LLM provider.
        
        This allows extending the factory with new providers without modifying the core code.
        
        Args:
            provider_type: Unique identifier for the provider
            provider_class: Provider class (must inherit from BaseLLMProvider)
            
        Raises:
            ConfigurationError: If provider_class doesn't inherit from BaseLLMProvider
            
        Example:
            >>> class CustomProvider(BaseLLMProvider):
            ...     pass
            >>> LLMFactory.register_provider("custom", CustomProvider)
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise ConfigurationError(
                f"Provider class must inherit from BaseLLMProvider"
            )
        
        # Create enum value dynamically
        provider_enum = LLMProviderType(provider_type.lower())
        cls._providers[provider_enum] = provider_class
        logger.info(f"Registered custom provider: {provider_type}")
    
    @classmethod
    def list_providers(cls) -> list:
        """
        List all registered provider types.
        
        Returns:
            list: List of provider type strings
        """
        return [p.value for p in cls._providers.keys()]
