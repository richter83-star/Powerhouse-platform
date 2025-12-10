"""
Hypothesis Generator: Generates testable hypotheses from data patterns.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from llm.base import BaseLLMProvider
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Hypothesis:
    """Represents a scientific hypothesis."""
    statement: str
    variables: List[str]
    predicted_relationship: str
    testability_score: float  # 0.0-1.0
    novelty_score: float  # 0.0-1.0
    metadata: Dict[str, Any] = None


class HypothesisGenerator:
    """Generates testable hypotheses from data patterns."""
    
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or LLMConfig.get_llm_provider("discovery")
        self.logger = get_logger(__name__)
    
    def generate_from_data(self, data: Dict[str, np.ndarray], num_hypotheses: int = 5) -> List[Hypothesis]:
        """Generate hypotheses from data patterns."""
        # Analyze correlations
        correlations = self._analyze_correlations(data)
        
        # Generate hypotheses using LLM
        hypotheses = []
        
        prompt = f"""Based on the following data patterns, generate {num_hypotheses} testable hypotheses:

{self._format_correlations(correlations)}

For each hypothesis, provide:
1. A clear, testable statement
2. Variables involved
3. Predicted relationship
4. Testability (0-1)
5. Novelty (0-1)

Return as JSON array."""
        
        try:
            response = self.llm.invoke(prompt=prompt, temperature=0.7, max_tokens=1500)
            import json
            results = json.loads(response.content)
            
            for result in results:
                hypotheses.append(Hypothesis(
                    statement=result["statement"],
                    variables=result["variables"],
                    predicted_relationship=result["relationship"],
                    testability_score=result.get("testability", 0.5),
                    novelty_score=result.get("novelty", 0.5)
                ))
        except Exception as e:
            self.logger.error(f"Hypothesis generation failed: {e}")
        
        return hypotheses
    
    def _analyze_correlations(self, data: Dict[str, np.ndarray]) -> Dict:
        """Analyze correlations between variables."""
        correlations = {}
        variables = list(data.keys())
        
        for i, var1 in enumerate(variables):
            for var2 in variables[i+1:]:
                if len(data[var1]) == len(data[var2]):
                    corr = np.corrcoef(data[var1], data[var2])[0, 1]
                    if not np.isnan(corr):
                        correlations[f"{var1}-{var2}"] = float(corr)
        
        return correlations
    
    def _format_correlations(self, correlations: Dict) -> str:
        """Format correlations for prompt."""
        lines = ["Variable Correlations:"]
        for pair, corr in sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)[:10]:
            lines.append(f"  {pair}: {corr:.3f}")
        return "\n".join(lines)

