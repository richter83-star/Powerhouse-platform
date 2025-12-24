"""
Neural network-based learning modules.
"""

from core.learning.neural_agent_selector import NeuralAgentSelector, AgentSelectionFeatures
from core.learning.training_pipeline import (
    ModelTrainingPipeline, TrainingConfig, TrainingMetrics, TrainingDataset
)
# Alias for backwards compatibility
TrainingPipeline = ModelTrainingPipeline
from core.learning.reinforcement_learning import (
    ParameterOptimizerRL, RLState, RLAction, RLReward,
    ParameterQNetwork, ParameterPolicyNetwork,
    ExperienceReplayBuffer, PolicyNetwork, ValueNetwork
)

from core.learning.external_memory import ExternalMemoryBank, MemorySlot
from core.learning.memory_controller import MemoryController, MemoryReadWrite
from core.learning.mann import MANNModel, MANNWrapper
from core.learning.knowledge_distillation import (
    KnowledgeDistiller, DistillationConfig, EnsembleDistiller
)
from core.learning.model_compression import (
    ModelCompressor, CompressionConfig
)

__all__ = [
    "NeuralAgentSelector",
    "AgentSelectionFeatures",
    "ModelTrainingPipeline",
    "TrainingPipeline",  # Alias
    "TrainingConfig",
    "TrainingMetrics",
    "TrainingDataset",
    "ParameterOptimizerRL",
    "RLState",
    "RLAction",
    "RLReward",
    "ParameterQNetwork",
    "ParameterPolicyNetwork",
    "ExperienceReplayBuffer",
    "PolicyNetwork",
    "ValueNetwork",
    "ExternalMemoryBank",
    "MemorySlot",
    "MemoryController",
    "MemoryReadWrite",
    "MANNModel",
    "MANNWrapper",
    "KnowledgeDistiller",
    "DistillationConfig",
    "EnsembleDistiller",
    "ModelCompressor",
    "CompressionConfig"
]

