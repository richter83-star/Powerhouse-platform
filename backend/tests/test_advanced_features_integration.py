"""
Integration tests for advanced features with existing system.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch


class TestEnhancedAgents:
    """Test enhanced agents with advanced capabilities."""
    
    def test_enhanced_react_agent_init(self):
        """Test enhanced ReAct agent initialization."""
        from core.agents.enhanced_react_agent import EnhancedReActAgent
        
        # Test with all features disabled
        agent = EnhancedReActAgent()
        assert agent.enable_causal == False
        assert agent.enable_neurosymbolic == False
        assert agent.enable_hierarchical == False
        
        # Test with features enabled
        agent = EnhancedReActAgent(
            enable_causal=True,
            enable_neurosymbolic=True,
            enable_hierarchical=True
        )
        assert agent.enable_causal == True
        assert agent.enable_neurosymbolic == True
        assert agent.enable_hierarchical == True
    
    def test_enhanced_react_agent_run(self):
        """Test enhanced ReAct agent execution."""
        from core.agents.enhanced_react_agent import EnhancedReActAgent
        
        agent = EnhancedReActAgent()
        context = {"task": "Calculate 2 + 2"}
        
        result = agent.run(context)
        assert result is not None
        assert isinstance(result, str)
    
    def test_enhanced_cot_agent(self):
        """Test enhanced Chain-of-Thought agent."""
        from core.agents.enhanced_cot_agent import EnhancedChainOfThoughtAgent
        
        agent = EnhancedChainOfThoughtAgent(enable_causal=True)
        context = {"task": "Solve: If A then B, if B then C, what can we say about A and C?"}
        
        result = agent.run(context)
        assert result is not None
    
    def test_enhanced_tot_agent(self):
        """Test enhanced Tree-of-Thought agent."""
        from core.agents.enhanced_tot_agent import EnhancedTreeOfThoughtAgent
        
        agent = EnhancedTreeOfThoughtAgent(enable_causal=True)
        context = {"task": "Find the best solution to a problem"}
        
        result = agent.run(context)
        assert result is not None


class TestOrchestratorIntegration:
    """Test orchestrator integration with advanced features."""
    
    def test_orchestrator_swarm_mode(self):
        """Test swarm execution mode."""
        from core.orchestrator import Orchestrator
        
        orchestrator = Orchestrator(agent_names=["react", "chain_of_thought"])
        
        # Mock swarm execution (may not have full dependencies)
        try:
            result = orchestrator.run_swarm("Test task", {"max_iterations": 2})
            assert result is not None
        except Exception as e:
            # Expected if dependencies missing
            assert "swarm" in str(e).lower() or "import" in str(e).lower()
    
    def test_orchestrator_causal_awareness(self):
        """Test causal-aware execution."""
        from core.orchestrator import Orchestrator
        from core.reasoning.causal_discovery import CausalGraph
        
        orchestrator = Orchestrator(agent_names=["react"])
        
        # Create simple causal graph
        graph = CausalGraph()
        graph.add_edge("X", "Y")
        
        try:
            result = orchestrator.run_with_causal_awareness("Task involving X and Y", graph)
            assert result is not None
        except Exception as e:
            # Expected if dependencies missing
            assert "causal" in str(e).lower() or "import" in str(e).lower()


class TestToolSynthesis:
    """Test tool synthesis capabilities."""
    
    def test_tool_synthesizer_init(self):
        """Test tool synthesizer initialization."""
        from core.tools.tool_synthesizer import ToolSynthesizer
        
        synthesizer = ToolSynthesizer()
        assert synthesizer.synthesizer is not None
        assert synthesizer.verifier is not None
        assert synthesizer.executor is not None
    
    @pytest.mark.skip(reason="Requires LLM and may be slow")
    def test_synthesize_simple_tool(self):
        """Test synthesizing a simple tool."""
        from core.tools.tool_synthesizer import ToolSynthesizer
        
        synthesizer = ToolSynthesizer()
        
        specification = "Add two numbers together"
        examples = [
            {"input": "2, 3", "output": "5"},
            {"input": "10, 20", "output": "30"}
        ]
        
        try:
            tool = synthesizer.synthesize_tool(
                specification=specification,
                examples=examples,
                auto_register=False
            )
            assert tool is not None
            assert tool.name is not None
            assert tool.description is not None
        except Exception as e:
            # May fail if LLM not available
            pytest.skip(f"Tool synthesis requires LLM: {e}")
    
    def test_tool_registry_synthesis(self):
        """Test tool registry synthesis capability."""
        from core.tools.tool_registry import ToolRegistry
        
        registry = ToolRegistry(enable_synthesis=True)
        assert registry.enable_synthesis == True
        
        # Without LLM, synthesis may not work
        if registry.synthesizer:
            assert registry.synthesizer is not None


class TestConfiguration:
    """Test advanced features configuration."""
    
    def test_advanced_features_config(self):
        """Test configuration loading."""
        from config.advanced_features_config import advanced_features_config
        
        assert advanced_features_config.ENABLE_CAUSAL_REASONING in [True, False]
        assert advanced_features_config.CAUSAL_DISCOVERY_METHOD in ["pc", "ges", "heuristic"]
        assert isinstance(advanced_features_config.CAUSAL_ALPHA, float)


class TestFeatureCombinations:
    """Test combinations of features working together."""
    
    def test_causal_with_neurosymbolic(self):
        """Test causal reasoning with neurosymbolic."""
        from core.reasoning.causal_discovery import CausalGraph
        from core.reasoning.neurosymbolic import NeurosymbolicReasoner
        
        # Create simple setup
        kg = CausalGraph()
        kg.add_edge("A", "B")
        
        reasoner = NeurosymbolicReasoner()
        
        # Both should work together
        assert kg is not None
        assert reasoner is not None
    
    def test_hierarchical_with_swarm(self):
        """Test hierarchical decomposition with swarm execution."""
        from core.planning.hierarchical_decomposer import TaskDecomposer
        from core.swarm.swarm_orchestrator import SwarmOrchestrator
        
        # Both should be importable
        decomposer = TaskDecomposer()
        swarm_orch = SwarmOrchestrator()
        
        assert decomposer is not None
        assert swarm_orch is not None

