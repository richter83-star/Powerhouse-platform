
"""
LLM Provider Configuration for Powerhouse Multi-Agent Platform.
"""

import os
from typing import Dict, Any, Optional


class LLMConfig:
    """
    Configuration for LLM providers and routing strategies.
    """
    
    # Default provider: RouteLLM
    DEFAULT_PROVIDER = "routellm"
    
    # Routing strategies by environment
    ROUTING_STRATEGIES = {
        "development": "cost-optimized",  # Save money during dev
        "staging": "balanced",             # Test production behavior
        "production": "balanced",          # Best quality for real users
    }
    
    # Get current environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    
    # Default routing strategy
    DEFAULT_ROUTING_STRATEGY = ROUTING_STRATEGIES.get(
        ENVIRONMENT, "balanced"
    )
    
    # API Keys
    ABACUSAI_API_KEY = os.getenv("ABACUSAI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Agent-specific overrides (optional)
    # Some agents may benefit from specific routing strategies
    AGENT_OVERRIDES: Dict[str, str] = {
        # High-complexity agents
        "tree_of_thought": "quality-first",     # Always use best model
        "debate": "quality-first",              # Multi-perspective needs quality
        "multi_agent": "quality-first",         # Coordination is complex
        
        # Medium-complexity agents
        "react": "balanced",                    # Smart mix
        "reflection": "balanced",               # Good self-critique
        "hierarchical_agents": "balanced",      # Delegation logic
        
        # Low-complexity agents
        "chain_of_thought": "cost-optimized",   # Simple sequential reasoning
        "planning": "cost-optimized",           # Structured output
        
        # Adaptive agents (let RouteLLM decide)
        "auto_loop_agent": "balanced",
        "memory_agent": "balanced",
        "adaptive_memory": "balanced",
    }
    
    # Provider-specific configurations
    PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
        "routellm": {
            "api_key": ABACUSAI_API_KEY,
            "default_model": "auto",
            "routing_strategy": DEFAULT_ROUTING_STRATEGY,
        },
        "openai": {
            "api_key": OPENAI_API_KEY,
            "default_model": "gpt-4",
        },
        "anthropic": {
            "api_key": ANTHROPIC_API_KEY,
            "default_model": "claude-3-sonnet-20240229",
        }
    }
    
    @classmethod
    def get_provider_config(cls, provider: str) -> Dict[str, Any]:
        """
        Get configuration for a specific provider.
        
        Args:
            provider: Provider name ('routellm', 'openai', 'anthropic')
            
        Returns:
            Dict[str, Any]: Provider configuration
        """
        return cls.PROVIDER_CONFIGS.get(provider, {})
    
    @classmethod
    def get_routing_strategy_for_agent(cls, agent_name: str) -> str:
        """
        Get the routing strategy for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            str: Routing strategy ('quality-first', 'balanced', 'cost-optimized')
        """
        return cls.AGENT_OVERRIDES.get(
            agent_name, 
            cls.DEFAULT_ROUTING_STRATEGY
        )
    
    @classmethod
    def get_llm_provider(cls, agent_name: Optional[str] = None):
        """
        Get configured LLM provider instance.
        
        Args:
            agent_name: Optional agent name for strategy override
            
        Returns:
            BaseLLMProvider: Configured LLM provider
        """
        from llm.factory import LLMFactory
        
        # Get routing strategy
        routing_strategy = cls.DEFAULT_ROUTING_STRATEGY
        if agent_name:
            routing_strategy = cls.get_routing_strategy_for_agent(agent_name)
        
        # Get provider config
        config = cls.get_provider_config(cls.DEFAULT_PROVIDER).copy()
        
        # Update routing strategy if using RouteLLM
        if cls.DEFAULT_PROVIDER == "routellm":
            config["routing_strategy"] = routing_strategy
        
        # Create provider
        return LLMFactory.create(
            provider_type=cls.DEFAULT_PROVIDER,
            **config
        )


# Export configuration
llm_config = LLMConfig()

