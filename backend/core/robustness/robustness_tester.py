"""
Robustness Tester: Evaluates system resilience under adversarial conditions.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from core.robustness.adversarial_generator import AdversarialGenerator, AdversarialExample
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RobustnessMetrics:
    """Metrics for system robustness."""
    accuracy_on_adversarial: float
    accuracy_on_clean: float
    robustness_gap: float  # Clean accuracy - adversarial accuracy
    attack_success_rate: float
    average_perturbation_norm: float
    num_tests: int


class RobustnessTester:
    """
    Tests system robustness against adversarial inputs.
    
    Evaluates:
    - Accuracy under attack
    - Perturbation tolerance
    - Failure modes
    """
    
    def __init__(self, epsilon_values: List[float] = None):
        """
        Initialize robustness tester.
        
        Args:
            epsilon_values: List of perturbation magnitudes to test
        """
        self.epsilon_values = epsilon_values or [0.01, 0.05, 0.1, 0.2]
        self.logger = get_logger(__name__)
    
    def test_robustness(
        self,
        model: Any,
        test_data: List[Tuple[np.ndarray, Any]],  # List of (input, label) pairs
        attack_method: str = "fgsm"
    ) -> RobustnessMetrics:
        """
        Test model robustness.
        
        Args:
            model: Model to test
            test_data: Test dataset
            attack_method: Attack method to use
            
        Returns:
            RobustnessMetrics
        """
        self.logger.info(f"Testing robustness with {attack_method} attack")
        
        # Test on clean data
        clean_correct = 0
        for input_data, label in test_data:
            pred = self._predict(model, input_data)
            if pred == label:
                clean_correct += 1
        
        clean_accuracy = clean_correct / len(test_data) if test_data else 0.0
        
        # Test on adversarial data
        adversarial_correct = 0
        attack_successes = 0
        perturbation_norms = []
        
        generator = AdversarialGenerator(method=attack_method)
        
        for input_data, label in test_data:
            # Generate adversarial example with different epsilons
            best_epsilon = None
            best_example = None
            
            for epsilon in self.epsilon_values:
                generator.epsilon = epsilon
                example = generator.generate(model, input_data, target=label)
                
                if example.attack_success:
                    if best_example is None or example.perturbation_norm < best_example.perturbation_norm:
                        best_example = example
                        best_epsilon = epsilon
                    break
            
            if best_example:
                attack_successes += 1
                perturbation_norms.append(best_example.perturbation_norm)
                
                # Check if prediction changed
                adversarial_pred = self._predict(model, best_example.adversarial_input)
                if adversarial_pred == label:
                    adversarial_correct += 1
            else:
                # Attack failed, check if original prediction correct
                pred = self._predict(model, input_data)
                if pred == label:
                    adversarial_correct += 1
        
        adversarial_accuracy = adversarial_correct / len(test_data) if test_data else 0.0
        attack_success_rate = attack_successes / len(test_data) if test_data else 0.0
        avg_perturbation = np.mean(perturbation_norms) if perturbation_norms else 0.0
        
        return RobustnessMetrics(
            accuracy_on_adversarial=adversarial_accuracy,
            accuracy_on_clean=clean_accuracy,
            robustness_gap=clean_accuracy - adversarial_accuracy,
            attack_success_rate=attack_success_rate,
            average_perturbation_norm=avg_perturbation,
            num_tests=len(test_data)
        )
    
    def _predict(self, model: Any, input_data: np.ndarray) -> Any:
        """Get model prediction."""
        try:
            import torch
            if isinstance(model, torch.nn.Module):
                with torch.no_grad():
                    input_tensor = torch.FloatTensor(input_data)
                    output = model(input_tensor)
                    if output.dim() > 1:
                        return torch.argmax(output, dim=1).item()
                    else:
                        return output.item()
        except ImportError:
            pass
        
        # Fallback: assume callable
        output = model(input_data)
        if isinstance(output, np.ndarray):
            return np.argmax(output) if output.size > 1 else output[0]
        return output

