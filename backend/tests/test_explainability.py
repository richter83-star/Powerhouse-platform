"""
Tests for Explainability Engine (Phase 4)

Tests decision explanations, learning explanations, and model attribution.
"""

import pytest
from datetime import datetime

from core.explainability import ExplanationEngine, DecisionExplanation, LearningExplanation


@pytest.mark.unit
class TestExplanationEngine:
    """Test explanation engine."""
    
    def test_initialization(self):
        """Test explanation engine initialization."""
        engine = ExplanationEngine()
        
        assert engine is not None
        assert engine.decision_history == []
        assert engine.learning_history == []
    
    def test_explain_agent_decision(self):
        """Test explain_agent_decision() with various agent outputs."""
        engine = ExplanationEngine()
        
        explanation = engine.explain_agent_decision(
            agent_name="ReactAgent",
            decision="Use search tool to find information",
            context={"task": "Find information about X"},
            agent_output="Thought: I need to search... Action: search('X')"
        )
        
        assert isinstance(explanation, DecisionExplanation)
        assert explanation.agent_name == "ReactAgent"
        assert len(explanation.reasoning_steps) >= 0
        assert 0.0 <= explanation.confidence <= 1.0
    
    def test_reasoning_step_extraction(self):
        """Test reasoning step extraction."""
        engine = ExplanationEngine()
        
        # Test with structured output
        output = "Step 1: First thought\nStep 2: Second thought\nFinal Answer: Result"
        steps = engine._extract_reasoning_from_output(output)
        
        assert len(steps) > 0
        assert any("thought" in step.lower() for step in steps)
    
    def test_factor_analysis(self):
        """Test factor analysis."""
        engine = ExplanationEngine()
        
        factors = engine._analyze_decision_factors(
            agent_name="ReactAgent",
            decision="Use tool X",
            context={"task": "Complex task", "outputs_count": 3}
        )
        
        assert isinstance(factors, dict)
        assert len(factors) > 0
        # Factors should sum to reasonable values
        assert all(0.0 <= v <= 1.0 for v in factors.values())
    
    def test_confidence_estimation(self):
        """Test confidence estimation."""
        engine = ExplanationEngine()
        
        factors = {
            "agent_expertise": 0.8,
            "available_information": 0.7,
            "context_confidence": 0.75
        }
        
        confidence = engine._estimate_confidence(
            agent_name="ReactAgent",
            decision="Test decision",
            context={},
            factors=factors
        )
        
        assert 0.0 <= confidence <= 1.0
    
    def test_explain_learning_progress(self):
        """Test explain_learning_progress() with before/after metrics."""
        engine = ExplanationEngine()
        
        explanation = engine.explain_learning_progress(
            model_name="NeuralAgentSelector",
            before_metrics={"success_rate": 0.7, "latency": 200},
            after_metrics={"success_rate": 0.85, "latency": 150},
            training_examples=100,
            learning_rate=0.001
        )
        
        assert isinstance(explanation, LearningExplanation)
        assert explanation.model_name == "NeuralAgentSelector"
        assert len(explanation.what_learned) >= 0
        assert len(explanation.key_insights) >= 0
    
    def test_insight_extraction(self):
        """Test insight extraction."""
        engine = ExplanationEngine()
        
        performance_change = {
            "success_rate": 0.15,
            "latency": -50,
            "quality_score": 0.1
        }
        what_learned = ["Improved success patterns", "Optimized speed"]
        
        insights = engine._extract_insights(
            model_name="TestModel",
            performance_change=performance_change,
            what_learned=what_learned
        )
        
        assert len(insights) > 0
        assert all(isinstance(insight, str) for insight in insights)
    
    def test_model_attribution(self):
        """Test feature attribution computation."""
        engine = ExplanationEngine()
        
        attribution = engine.explain_model_prediction(
            model_name="TestModel",
            prediction="Agent A",
            input_features={
                "complexity": 0.7,
                "task_type": "reasoning",
                "history": 0.8
            },
            model_type="neural_network"
        )
        
        assert "feature_attributions" in attribution
        assert "top_features" in attribution
        assert "explanation" in attribution
    
    def test_reasoning_chain_generation(self):
        """Test reasoning chain generation from agent outputs."""
        engine = ExplanationEngine()
        
        agent_outputs = [
            {"agent": "Agent1", "output": "Step 1: Analyze problem"},
            {"agent": "Agent2", "output": "Step 2: Generate solution"},
            {"agent": "Agent3", "output": "Step 3: Final answer: 42"}
        ]
        
        chain = engine.generate_reasoning_chain(
            task="Solve problem",
            agent_outputs=agent_outputs
        )
        
        assert "steps" in chain
        assert len(chain["steps"]) == 3
        assert "final_answer" in chain
        assert chain["final_answer"] is not None

