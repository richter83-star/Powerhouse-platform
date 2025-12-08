
"""
Core module exports.
"""

from .base_agent import BaseAgent
from .agent_loader import AgentLoader
from .orchestrator import Orchestrator
from .action_dispatcher import ActionDispatcher
from .feedback_pipeline import FeedbackPipeline, OutcomeEvent, OutcomeStatus
from .online_learning import RealTimeModelUpdater
from .performance_monitor import (
    PerformanceMonitor,
    get_performance_monitor,
    init_performance_monitor,
    PerformanceMetrics,
    AgentPerformance,
    PerformanceAlert,
    AlertLevel,
    MetricType
)
from .dynamic_config_manager import (
    DynamicConfigManager,
    get_config_manager,
    AdjustmentStrategy,
    AdjustmentRule,
    ParameterBounds,
    ConfigurationScope
)
from .performance_monitor_with_config import (
    AdaptivePerformanceMonitor,
    get_adaptive_monitor
)
from .adaptive_orchestrator import AdaptiveOrchestrator

# Plugin system
from .plugin_base import (
    PluginInterface,
    PluginMetadata,
    PluginCapability,
    PluginPermission,
    PluginException,
    PluginInitializationError,
    PluginExecutionError,
    PluginSecurityError,
    PluginValidationError
)
from .plugin_security import PluginSignature, PluginSandbox, PluginValidator
from .plugin_loader import PluginLoader, PluginInstance
from .plugin_registry import PluginRegistry, PluginRegistryEntry
from .plugin_service import PluginService
from .orchestrator_with_plugins import PluginEnabledOrchestrator

# Self-update CI/CD system
from .version_detector import (
    VersionDetector,
    VersionInfo,
    VersionComparison,
    UpdateSource,
    UpdatePriority
)
from .update_simulator import (
    UpdateSimulator,
    SimulationResult,
    SimulationConfig,
    SimulationStatus,
    TestType
)
from .update_policy_engine import (
    UpdatePolicyEngine,
    PolicyEvaluation,
    UpdatePolicy,
    UpdateDecision,
    RiskLevel
)
from .cicd_integrator import (
    CICDIntegrator,
    CICDConfig,
    CICDProvider,
    DeploymentTrigger,
    DeploymentResult,
    DeploymentStatus
)
from .rollout_controller import (
    RolloutController,
    RolloutConfig,
    RolloutStrategy,
    RolloutStatus,
    RolloutPhase
)
from .self_update_orchestrator import (
    SelfUpdateOrchestrator,
    UpdateWorkflow
)

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentLoader",
    
    # Orchestration
    "Orchestrator",
    "ActionDispatcher",
    "AdaptiveOrchestrator",
    
    # Feedback and learning
    "FeedbackPipeline",
    "OutcomeEvent",
    "OutcomeStatus",
    "RealTimeModelUpdater",
    
    # Performance monitoring
    "PerformanceMonitor",
    "get_performance_monitor",
    "init_performance_monitor",
    "PerformanceMetrics",
    "AgentPerformance",
    "PerformanceAlert",
    "AlertLevel",
    "MetricType",
    
    # Dynamic self-configuration
    "DynamicConfigManager",
    "get_config_manager",
    "AdjustmentStrategy",
    "AdjustmentRule",
    "ParameterBounds",
    "ConfigurationScope",
    "AdaptivePerformanceMonitor",
    "get_adaptive_monitor",
    
    # Plugin system
    "PluginInterface",
    "PluginMetadata",
    "PluginCapability",
    "PluginPermission",
    "PluginException",
    "PluginInitializationError",
    "PluginExecutionError",
    "PluginSecurityError",
    "PluginValidationError",
    "PluginSignature",
    "PluginSandbox",
    "PluginValidator",
    "PluginLoader",
    "PluginInstance",
    "PluginRegistry",
    "PluginRegistryEntry",
    "PluginService",
    "PluginEnabledOrchestrator",
    
    # Self-update CI/CD system
    "VersionDetector",
    "VersionInfo",
    "VersionComparison",
    "UpdateSource",
    "UpdatePriority",
    "UpdateSimulator",
    "SimulationResult",
    "SimulationConfig",
    "SimulationStatus",
    "TestType",
    "UpdatePolicyEngine",
    "PolicyEvaluation",
    "UpdatePolicy",
    "UpdateDecision",
    "RiskLevel",
    "CICDIntegrator",
    "CICDConfig",
    "CICDProvider",
    "DeploymentTrigger",
    "DeploymentResult",
    "DeploymentStatus",
    "RolloutController",
    "RolloutConfig",
    "RolloutStrategy",
    "RolloutStatus",
    "RolloutPhase",
    "SelfUpdateOrchestrator",
    "UpdateWorkflow",
]
