"""Experiment Designer: Designs controlled experiments to test hypotheses."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from core.discovery.hypothesis_generator import Hypothesis
from llm.base import BaseLLMProvider
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Experiment:
    """Represents a designed experiment."""
    hypothesis: Hypothesis
    design: str
    independent_variables: List[str]
    dependent_variables: List[str]
    control_variables: List[str]
    procedure: List[str]
    expected_outcomes: Dict[str, Any]


class ExperimentDesigner:
    """Designs experiments to test hypotheses."""
    
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or LLMConfig.get_llm_provider("discovery")
        self.logger = get_logger(__name__)
    
    def design_experiment(self, hypothesis: Hypothesis) -> Experiment:
        """Design experiment to test hypothesis."""
        prompt = f"""Design a controlled experiment to test this hypothesis:

{hypothesis.statement}

Provide:
1. Experimental design type (e.g., randomized controlled trial, observational)
2. Independent variables (variables you manipulate)
3. Dependent variables (variables you measure)
4. Control variables (variables you hold constant)
5. Step-by-step procedure
6. Expected outcomes

Return as JSON."""
        
        try:
            response = self.llm.invoke(prompt=prompt, temperature=0.5, max_tokens=1000)
            import json
            result = json.loads(response.content)
            
            return Experiment(
                hypothesis=hypothesis,
                design=result.get("design", "controlled"),
                independent_variables=result.get("independent_variables", []),
                dependent_variables=result.get("dependent_variables", []),
                control_variables=result.get("control_variables", []),
                procedure=result.get("procedure", []),
                expected_outcomes=result.get("expected_outcomes", {})
            )
        except Exception as e:
            self.logger.error(f"Experiment design failed: {e}")
            # Return basic design
            return Experiment(
                hypothesis=hypothesis,
                design="controlled",
                independent_variables=hypothesis.variables[:1] if hypothesis.variables else [],
                dependent_variables=hypothesis.variables[1:] if len(hypothesis.variables) > 1 else [],
                control_variables=[],
                procedure=["1. Set up controlled conditions", "2. Manipulate independent variable", "3. Measure dependent variable"],
                expected_outcomes={}
            )

