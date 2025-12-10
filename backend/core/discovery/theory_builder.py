"""Theory Builder: Constructs explanatory theories from evidence."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from core.discovery.hypothesis_generator import Hypothesis
from core.discovery.experiment_designer import Experiment
from llm.base import BaseLLMProvider
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Theory:
    """Represents a scientific theory."""
    name: str
    description: str
    hypotheses: List[Hypothesis]
    evidence: List[Dict[str, Any]]
    explanatory_power: float  # 0.0-1.0
    predictive_power: float  # 0.0-1.0


class TheoryBuilder:
    """Builds theories from hypotheses and evidence."""
    
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or LLMConfig.get_llm_provider("discovery")
        self.logger = get_logger(__name__)
    
    def build_theory(
        self,
        hypotheses: List[Hypothesis],
        experimental_results: List[Dict[str, Any]]
    ) -> Theory:
        """Build theory from hypotheses and results."""
        prompt = f"""Based on these hypotheses and experimental results, construct a unified theory:

Hypotheses:
{chr(10).join([f"- {h.statement}" for h in hypotheses])}

Results:
{chr(10).join([f"- {r}" for r in experimental_results])}

Provide:
1. Theory name
2. Description
3. Explanatory power (0-1)
4. Predictive power (0-1)

Return as JSON."""
        
        try:
            response = self.llm.invoke(prompt=prompt, temperature=0.7, max_tokens=1000)
            import json
            result = json.loads(response.content)
            
            return Theory(
                name=result.get("name", "Theory"),
                description=result.get("description", ""),
                hypotheses=hypotheses,
                evidence=experimental_results,
                explanatory_power=result.get("explanatory_power", 0.5),
                predictive_power=result.get("predictive_power", 0.5)
            )
        except Exception as e:
            self.logger.error(f"Theory building failed: {e}")
            return Theory(
                name="Default Theory",
                description="Theory constructed from hypotheses",
                hypotheses=hypotheses,
                evidence=experimental_results,
                explanatory_power=0.5,
                predictive_power=0.5
            )

