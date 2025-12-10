"""
Explanation Engine for AI Decision Transparency

Provides explainability and interpretability features to understand
agent decisions, learning progress, and system behavior.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DecisionExplanation:
    """Explanation of an agent decision."""
    agent_name: str
    decision: str
    reasoning_steps: List[str]
    factors_considered: Dict[str, float]  # Factor -> importance score
    confidence: float
    alternatives: List[Dict[str, Any]]
    timestamp: datetime
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class LearningExplanation:
    """Explanation of learning progress."""
    model_name: str
    what_learned: List[str]  # What patterns/concepts were learned
    performance_change: Dict[str, float]  # Metric -> change
    key_insights: List[str]
    improvement_factors: Dict[str, float]  # Factor -> contribution
    learned_from: int  # Number of examples
    learning_rate: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


class ExplanationEngine:
    """
    Explanation engine for generating human-readable explanations
    of agent behavior and learning.
    """
    
    def __init__(self):
        """Initialize explanation engine."""
        self.decision_history: List[DecisionExplanation] = []
        self.learning_history: List[LearningExplanation] = []
        self.attribution_cache: Dict[str, Dict[str, float]] = {}
        
        logger.info("ExplanationEngine initialized")
    
    def explain_agent_decision(
        self,
        agent_name: str,
        decision: str,
        context: Dict[str, Any],
        reasoning_trace: Optional[List[str]] = None,
        agent_output: Optional[Any] = None
    ) -> DecisionExplanation:
        """
        Generate explanation for an agent decision.
        
        Args:
            agent_name: Name of the agent
            decision: The decision made
            context: Execution context
            reasoning_trace: Optional reasoning steps
            agent_output: Optional agent output
            
        Returns:
            Decision explanation
        """
        # Extract reasoning steps
        reasoning_steps = reasoning_trace or []
        
        # If agent output is a string, try to extract reasoning
        if isinstance(agent_output, str) and not reasoning_steps:
            reasoning_steps = self._extract_reasoning_from_output(agent_output)
        
        # Analyze factors that influenced decision
        factors = self._analyze_decision_factors(agent_name, decision, context)
        
        # Calculate confidence
        confidence = self._estimate_confidence(agent_name, decision, context, factors)
        
        # Generate alternatives
        alternatives = self._generate_alternatives(agent_name, decision, context)
        
        explanation = DecisionExplanation(
            agent_name=agent_name,
            decision=decision,
            reasoning_steps=reasoning_steps,
            factors_considered=factors,
            confidence=confidence,
            alternatives=alternatives,
            timestamp=datetime.now(),
            context=self._sanitize_context(context)
        )
        
        self.decision_history.append(explanation)
        
        logger.debug(f"Generated explanation for {agent_name} decision")
        
        return explanation
    
    def explain_learning_progress(
        self,
        model_name: str,
        before_metrics: Dict[str, float],
        after_metrics: Dict[str, float],
        training_examples: int,
        learning_rate: float
    ) -> LearningExplanation:
        """
        Generate explanation of learning progress.
        
        Args:
            model_name: Name of the model
            before_metrics: Metrics before learning
            after_metrics: Metrics after learning
            training_examples: Number of training examples
            learning_rate: Learning rate used
            
        Returns:
            Learning explanation
        """
        # Calculate performance changes
        performance_change = {}
        for metric in set(before_metrics.keys()) | set(after_metrics.keys()):
            before = before_metrics.get(metric, 0.0)
            after = after_metrics.get(metric, before)
            change = after - before
            performance_change[metric] = change
        
        # Determine what was learned
        what_learned = self._identify_learned_concepts(
            model_name, before_metrics, after_metrics
        )
        
        # Extract key insights
        key_insights = self._extract_insights(
            model_name, performance_change, what_learned
        )
        
        # Analyze improvement factors
        improvement_factors = self._analyze_improvement_factors(
            performance_change, training_examples
        )
        
        explanation = LearningExplanation(
            model_name=model_name,
            what_learned=what_learned,
            performance_change=performance_change,
            key_insights=key_insights,
            improvement_factors=improvement_factors,
            learned_from=training_examples,
            learning_rate=learning_rate,
            timestamp=datetime.now()
        )
        
        self.learning_history.append(explanation)
        
        logger.debug(f"Generated learning explanation for {model_name}")
        
        return explanation
    
    def explain_model_prediction(
        self,
        model_name: str,
        prediction: Any,
        input_features: Dict[str, Any],
        model_type: str = "neural_network"
    ) -> Dict[str, Any]:
        """
        Explain why a model made a specific prediction.
        
        Uses attribution methods like:
        - Gradient-based attribution (for neural networks)
        - Feature importance (for tree models)
        - Attention weights (for transformers)
        
        Args:
            model_name: Name of the model
            prediction: Model prediction
            input_features: Input features
            model_type: Type of model
            
        Returns:
            Attribution explanation
        """
        cache_key = f"{model_name}_{hash(str(input_features))}"
        
        if cache_key in self.attribution_cache:
            attribution = self.attribution_cache[cache_key]
        else:
            attribution = self._compute_attribution(
                model_name, prediction, input_features, model_type
            )
            self.attribution_cache[cache_key] = attribution
        
        return {
            "model": model_name,
            "prediction": prediction,
            "feature_attributions": attribution,
            "top_features": sorted(
                attribution.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:5],
            "explanation": self._generate_attribution_text(attribution)
        }
    
    def generate_reasoning_chain(
        self,
        task: str,
        agent_outputs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a human-readable reasoning chain from agent outputs.
        
        Args:
            task: Original task
            agent_outputs: List of agent outputs
            
        Returns:
            Reasoning chain explanation
        """
        chain = {
            "task": task,
            "steps": [],
            "final_answer": None,
            "reasoning_path": []
        }
        
        for i, output in enumerate(agent_outputs):
            agent_name = output.get("agent", "Unknown")
            result = output.get("output", "")
            
            step = {
                "step_number": i + 1,
                "agent": agent_name,
                "action": self._infer_action(result),
                "result": result[:200] if isinstance(result, str) else str(result)[:200],
                "contribution": self._assess_contribution(result, task)
            }
            
            chain["steps"].append(step)
            chain["reasoning_path"].append(f"Step {i+1}: {agent_name} - {step['action']}")
        
        # Extract final answer
        if agent_outputs:
            final_output = agent_outputs[-1].get("output", "")
            chain["final_answer"] = self._extract_final_answer(final_output)
        
        return chain
    
    def _extract_reasoning_from_output(self, output: str) -> List[str]:
        """Extract reasoning steps from agent output."""
        reasoning_steps = []
        
        # Look for common patterns
        import re
        
        # Pattern: "Step 1:", "1.", "Thought:", etc.
        patterns = [
            r'(?:Step \d+|Thought \d+|Reasoning \d+)[:.]\s*(.+?)(?=\n|Step |Thought |Reasoning |$)',
            r'^\d+[\.\)]\s*(.+)$',
            r'Thought[:]\s*(.+?)(?=\n|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output, re.MULTILINE | re.IGNORECASE)
            if matches:
                reasoning_steps.extend(matches)
                break
        
        # If no structured reasoning found, split by sentences
        if not reasoning_steps:
            sentences = output.split('.')
            reasoning_steps = [s.strip() for s in sentences if s.strip()][:5]
        
        return reasoning_steps
    
    def _analyze_decision_factors(
        self,
        agent_name: str,
        decision: str,
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Analyze factors that influenced the decision."""
        factors = {}
        
        # Task complexity
        task = context.get("task", "")
        factors["task_complexity"] = min(1.0, len(task) / 500.0)
        
        # Available information
        outputs_count = len(context.get("outputs", []))
        factors["available_information"] = min(1.0, outputs_count / 5.0)
        
        # Agent expertise (heuristic based on agent type)
        expertise_map = {
            "React": 0.8,
            "TreeOfThought": 0.9,
            "ChainOfThought": 0.85,
            "Planning": 0.75
        }
        factors["agent_expertise"] = expertise_map.get(agent_name, 0.7)
        
        # Confidence from context
        if "confidence" in context:
            factors["context_confidence"] = float(context["confidence"])
        else:
            factors["context_confidence"] = 0.7
        
        # Normalize factors
        total = sum(factors.values())
        if total > 0:
            factors = {k: v / total for k, v in factors.items()}
        
        return factors
    
    def _estimate_confidence(
        self,
        agent_name: str,
        decision: str,
        context: Dict[str, Any],
        factors: Dict[str, float]
    ) -> float:
        """Estimate confidence in the decision."""
        # Weighted combination of factors
        confidence = (
            factors.get("agent_expertise", 0.7) * 0.4 +
            factors.get("available_information", 0.5) * 0.3 +
            factors.get("context_confidence", 0.7) * 0.3
        )
        
        # Adjust based on decision length (longer decisions might be less confident)
        if isinstance(decision, str):
            if len(decision) > 500:
                confidence *= 0.9  # Slight penalty for very long decisions
        
        return min(1.0, max(0.0, confidence))
    
    def _generate_alternatives(
        self,
        agent_name: str,
        decision: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate alternative decisions that could have been made."""
        alternatives = []
        
        # Generate alternatives based on agent type
        if "React" in agent_name:
            alternatives.append({
                "decision": "Use different reasoning approach",
                "rationale": "Could use chain-of-thought instead",
                "likelihood": 0.3
            })
        
        if context.get("outputs"):
            alternatives.append({
                "decision": "Combine with previous agent outputs",
                "rationale": "Previous agents provided relevant information",
                "likelihood": 0.5
            })
        
        return alternatives
    
    def _identify_learned_concepts(
        self,
        model_name: str,
        before_metrics: Dict[str, float],
        after_metrics: Dict[str, float]
    ) -> List[str]:
        """Identify what concepts the model learned."""
        learned = []
        
        # Check improvements in different metrics
        if "success_rate" in after_metrics and "success_rate" in before_metrics:
            improvement = after_metrics["success_rate"] - before_metrics["success_rate"]
            if improvement > 0.1:
                learned.append("Improved success patterns")
        
        if "latency" in after_metrics and "latency" in before_metrics:
            improvement = before_metrics["latency"] - after_metrics["latency"]
            if improvement > 100:  # Faster
                learned.append("Optimized execution speed")
        
        if "quality_score" in after_metrics and "quality_score" in before_metrics:
            improvement = after_metrics["quality_score"] - before_metrics["quality_score"]
            if improvement > 0.1:
                learned.append("Enhanced output quality")
        
        if not learned:
            learned.append("General performance improvement")
        
        return learned
    
    def _extract_insights(
        self,
        model_name: str,
        performance_change: Dict[str, float],
        what_learned: List[str]
    ) -> List[str]:
        """Extract key insights from learning."""
        insights = []
        
        # Biggest improvement
        if performance_change:
            best_improvement = max(performance_change.items(), key=lambda x: abs(x[1]))
            insights.append(
                f"Largest improvement in {best_improvement[0]}: "
                f"{best_improvement[1]:.2%}"
            )
        
        # Learning efficiency
        if what_learned:
            insights.append(f"Model learned: {', '.join(what_learned[:3])}")
        
        return insights
    
    def _analyze_improvement_factors(
        self,
        performance_change: Dict[str, float],
        training_examples: int
    ) -> Dict[str, float]:
        """Analyze what factors contributed to improvement."""
        factors = {}
        
        total_improvement = sum(abs(v) for v in performance_change.values())
        
        if total_improvement > 0:
            for metric, change in performance_change.items():
                factors[metric] = abs(change) / total_improvement
        
        # Data quality factor
        factors["data_quality"] = min(1.0, training_examples / 100.0)
        
        return factors
    
    def _compute_attribution(
        self,
        model_name: str,
        prediction: Any,
        input_features: Dict[str, Any],
        model_type: str
    ) -> Dict[str, float]:
        """Compute feature attribution."""
        # Simplified attribution
        # In production, would use gradient-based methods, SHAP, etc.
        
        attribution = {}
        
        # Simple heuristic: distribute importance evenly
        # In production, would use actual model gradients
        feature_count = len(input_features)
        base_importance = 1.0 / feature_count if feature_count > 0 else 0.0
        
        for feature_name, feature_value in input_features.items():
            # Weight by feature magnitude (normalized)
            if isinstance(feature_value, (int, float)):
                importance = base_importance * (1.0 + abs(feature_value) * 0.1)
            else:
                importance = base_importance
            attribution[feature_name] = importance
        
        # Normalize
        total = sum(attribution.values())
        if total > 0:
            attribution = {k: v / total for k, v in attribution.items()}
        
        return attribution
    
    def _generate_attribution_text(self, attribution: Dict[str, float]) -> str:
        """Generate human-readable attribution text."""
        if not attribution:
            return "No feature attributions available."
        
        top_features = sorted(
            attribution.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:3]
        
        text = "The prediction was primarily influenced by: "
        text += ", ".join([
            f"{name} ({importance:.1%})" for name, importance in top_features
        ])
        
        return text
    
    def _infer_action(self, result: Any) -> str:
        """Infer what action the agent took."""
        result_str = str(result).lower()
        
        if "reason" in result_str or "think" in result_str:
            return "Reasoning"
        elif "plan" in result_str or "step" in result_str:
            return "Planning"
        elif "calculate" in result_str or "compute" in result_str:
            return "Calculation"
        elif "search" in result_str or "lookup" in result_str:
            return "Information Retrieval"
        elif "evaluat" in result_str or "assess" in result_str:
            return "Evaluation"
        else:
            return "Processing"
    
    def _assess_contribution(self, result: Any, task: str) -> str:
        """Assess how the result contributes to the task."""
        result_str = str(result).lower()
        task_lower = task.lower()
        
        # Check if result addresses task keywords
        task_keywords = task_lower.split()
        matches = sum(1 for keyword in task_keywords if keyword in result_str)
        
        if matches > len(task_keywords) * 0.3:
            return "High - Directly addresses task requirements"
        elif matches > 0:
            return "Medium - Partially addresses task"
        else:
            return "Low - Indirect contribution"
    
    def _extract_final_answer(self, output: Any) -> str:
        """Extract final answer from output."""
        if isinstance(output, str):
            # Look for "Final Answer:", "Answer:", "Conclusion:", etc.
            import re
            patterns = [
                r'(?:Final Answer|Answer|Conclusion)[:]\s*(.+?)(?=\n|$)',
                r'Therefore[,.]\s*(.+?)(?=\n|$)',
                r'In conclusion[,.]\s*(.+?)(?=\n|$)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            
            # Fallback: last sentence
            sentences = output.split('.')
            if sentences:
                return sentences[-1].strip()
        
        return str(output)[:200]
    
    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize context for explanation (remove sensitive data)."""
        sanitized = {}
        
        # Include only relevant fields
        allowed_keys = [
            "task", "run_id", "outputs_count", "agent_count",
            "execution_mode", "timestamp"
        ]
        
        for key in allowed_keys:
            if key in context:
                sanitized[key] = context[key]
        
        return sanitized
    
    def get_explanation_summary(self) -> Dict[str, Any]:
        """Get summary of all explanations."""
        return {
            "total_decisions_explained": len(self.decision_history),
            "total_learning_explanations": len(self.learning_history),
            "recent_decisions": [
                d.to_dict() for d in self.decision_history[-10:]
            ],
            "recent_learning": [
                l.to_dict() for l in self.learning_history[-5:]
            ]
        }


