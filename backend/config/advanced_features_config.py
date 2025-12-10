"""
Configuration for Advanced AI Features.

Controls which advanced features are enabled and their settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class AdvancedFeaturesConfig(BaseSettings):
    """Configuration for advanced AI features."""
    
    # Feature Flags
    ENABLE_CAUSAL_REASONING: bool = True
    ENABLE_NEUROSYMBOLIC: bool = True
    ENABLE_HIERARCHICAL_DECOMPOSITION: bool = True
    ENABLE_MANN: bool = True
    ENABLE_KNOWLEDGE_DISTILLATION: bool = True
    ENABLE_SWARM_INTELLIGENCE: bool = True
    ENABLE_ADVERSARIAL_ROBUSTNESS: bool = True
    ENABLE_PROGRAM_SYNTHESIS: bool = True
    ENABLE_SCIENTIFIC_DISCOVERY: bool = True
    ENABLE_MULTIMODAL_LEARNING: bool = True
    
    # Causal Reasoning
    CAUSAL_DISCOVERY_METHOD: str = "pc"  # "pc", "ges", "heuristic"
    CAUSAL_ALPHA: float = 0.05
    
    # Program Synthesis
    PROGRAM_SYNTHESIS_TEMPERATURE: float = 0.3
    PROGRAM_SYNTHESIS_TIMEOUT: float = 5.0
    
    # Swarm Intelligence
    SWARM_DEFAULT_ITERATIONS: int = 10
    SWARM_STIGMERGY_DECAY_RATE: float = 0.1
    
    # MANN
    MANN_MEMORY_SIZE: int = 128
    MANN_KEY_DIM: int = 64
    MANN_VALUE_DIM: int = 128
    
    # Knowledge Distillation
    DISTILLATION_TEMPERATURE: float = 3.0
    DISTILLATION_ALPHA: float = 0.7
    DISTILLATION_BETA: float = 0.3
    
    # Adversarial Robustness
    ADVERSARIAL_EPSILON: float = 0.1
    ADVERSARIAL_ATTACK_METHOD: str = "fgsm"  # "fgsm", "pgd"
    
    # Multi-Modal
    MULTIMODAL_MODEL_TYPE: str = "clip"  # "clip", "blip"
    
    class Config:
        env_prefix = "ADVANCED_FEATURES_"
        case_sensitive = False


# Global config instance
advanced_features_config = AdvancedFeaturesConfig()

