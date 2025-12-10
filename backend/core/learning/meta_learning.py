"""
Meta-Learning System - Learning to Learn

Implements meta-learning algorithms that enable the system to learn
optimal learning strategies, adapt quickly to new tasks, and transfer
knowledge across domains.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from collections import deque, defaultdict

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TaskMeta:
    """Metadata about a learning task."""
    task_type: str
    task_id: str
    task_description: str
    domain: str
    complexity: float
    sample_efficiency: float  # How quickly it learns
    final_performance: float
    learning_curve: List[float]
    optimal_hyperparameters: Dict[str, Any]
    learned_at: datetime


class MetaLearner:
    """
    Meta-learning system that learns optimal learning strategies.
    
    Features:
    - Few-shot learning adaptation
    - Transfer learning across domains
    - Hyperparameter optimization
    - Learning strategy selection
    - Continual learning without catastrophic forgetting
    """
    
    def __init__(
        self,
        model_id: str = "meta_learner_v1",
        embedding_dim: int = 64,
        hidden_dim: int = 128
    ):
        """
        Initialize meta-learner.
        
        Args:
            model_id: Model identifier
            embedding_dim: Dimension for task embeddings
            hidden_dim: Hidden layer dimension
        """
        self.model_id = model_id
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        
        # Task memory
        self.task_memory: Dict[str, TaskMeta] = {}
        self.task_embeddings: Dict[str, np.ndarray] = {}
        
        # Learning strategies
        self.strategies = {
            "few_shot": self._few_shot_adaptation,
            "transfer": self._transfer_learning,
            "maml": self._maml_adaptation,
            "reptile": self._reptile_adaptation
        }
        
        # Initialize meta-model if PyTorch available
        self.meta_model = None
        if TORCH_AVAILABLE:
            self._init_meta_model()
        
        logger.info(f"MetaLearner initialized: {model_id}")
    
    def _init_meta_model(self):
        """Initialize meta-learning model."""
        try:
            # Task encoder: maps task description to embedding
            self.task_encoder = nn.Sequential(
                nn.Linear(100, self.hidden_dim),  # Input: task features
                nn.ReLU(),
                nn.Linear(self.hidden_dim, self.embedding_dim),
                nn.Tanh()
            )
            
            # Strategy predictor: predicts best learning strategy
            self.strategy_predictor = nn.Sequential(
                nn.Linear(self.embedding_dim, self.hidden_dim),
                nn.ReLU(),
                nn.Linear(self.hidden_dim, len(self.strategies)),
                nn.Softmax(dim=-1)
            )
            
            # Hyperparameter predictor: predicts optimal hyperparameters
            self.hyperparam_predictor = nn.Sequential(
                nn.Linear(self.embedding_dim, self.hidden_dim),
                nn.ReLU(),
                nn.Linear(self.hidden_dim, 10)  # Predicts 10 hyperparameters
            )
            
            self.optimizer = optim.Adam(
                list(self.task_encoder.parameters()) +
                list(self.strategy_predictor.parameters()) +
                list(self.hyperparam_predictor.parameters()),
                lr=0.001
            )
            
            self.meta_model = {
                "task_encoder": self.task_encoder,
                "strategy_predictor": self.strategy_predictor,
                "hyperparam_predictor": self.hyperparam_predictor,
                "optimizer": self.optimizer
            }
            
            logger.info("Meta-learning model initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize meta-model: {e}")
            self.meta_model = None
    
    def learn_from_task(
        self,
        task_type: str,
        task_description: str,
        domain: str,
        learning_curve: List[float],
        final_performance: float,
        hyperparameters: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> str:
        """
        Learn from a completed task and update meta-knowledge.
        
        Args:
            task_type: Type of task
            task_description: Description of task
            domain: Domain/category
            learning_curve: Performance over time
            final_performance: Final performance achieved
            hyperparameters: Hyperparameters used
            task_id: Optional task identifier
            
        Returns:
            Task ID
        """
        task_id = task_id or f"{task_type}_{datetime.now().timestamp()}"
        
        # Calculate sample efficiency
        sample_efficiency = self._calculate_sample_efficiency(learning_curve)
        
        # Create task metadata
        task_meta = TaskMeta(
            task_type=task_type,
            task_id=task_id,
            task_description=task_description,
            domain=domain,
            complexity=self._estimate_complexity(task_description, domain),
            sample_efficiency=sample_efficiency,
            final_performance=final_performance,
            learning_curve=learning_curve,
            optimal_hyperparameters=hyperparameters,
            learned_at=datetime.now()
        )
        
        # Store in memory
        self.task_memory[task_id] = task_meta
        
        # Create task embedding
        task_features = self._extract_task_features(task_meta)
        if self.meta_model:
            self._update_embeddings(task_features, task_meta)
        
        logger.info(f"Learned from task: {task_id}, performance: {final_performance:.3f}")
        
        return task_id
    
    def predict_strategy(
        self,
        task_description: str,
        domain: str,
        available_strategies: Optional[List[str]] = None
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        Predict best learning strategy for a new task.
        
        Args:
            task_description: Description of new task
            domain: Domain/category
            available_strategies: Available strategies (None = all)
            
        Returns:
            Tuple of (best_strategy, confidence, recommended_hyperparameters)
        """
        if not self.task_memory:
            # No prior knowledge, use default
            return "few_shot", 0.5, self._default_hyperparameters()
        
        # Find similar tasks
        similar_tasks = self._find_similar_tasks(task_description, domain, top_k=5)
        
        if not similar_tasks:
            return "few_shot", 0.5, self._default_hyperparameters()
        
        # Analyze what worked for similar tasks
        strategy_performance = defaultdict(list)
        hyperparam_patterns = defaultdict(list)
        
        for task_id, similarity in similar_tasks:
            task_meta = self.task_memory[task_id]
            # Infer strategy from performance characteristics
            strategy = self._infer_strategy(task_meta)
            strategy_performance[strategy].append(
                task_meta.final_performance * similarity
            )
            hyperparam_patterns[strategy].append(task_meta.optimal_hyperparameters)
        
        # Select best strategy
        avg_performance = {
            strat: np.mean(perfs)
            for strat, perfs in strategy_performance.items()
        }
        
        if not avg_performance:
            return "few_shot", 0.5, self._default_hyperparameters()
        
        best_strategy = max(avg_performance.items(), key=lambda x: x[1])[0]
        confidence = min(1.0, avg_performance[best_strategy])
        
        # Predict hyperparameters
        if hyperparam_patterns[best_strategy]:
            hyperparams = self._aggregate_hyperparameters(hyperparam_patterns[best_strategy])
        else:
            hyperparams = self._default_hyperparameters()
        
        # Use meta-model if available
        if self.meta_model and len(similar_tasks) >= 3:
            try:
                task_features = self._extract_task_features_from_description(
                    task_description, domain
                )
                meta_prediction = self._meta_model_predict(task_features)
                if meta_prediction:
                    best_strategy, confidence, hyperparams = meta_prediction
            except Exception as e:
                logger.warning(f"Meta-model prediction failed: {e}")
        
        logger.info(f"Predicted strategy: {best_strategy}, confidence: {confidence:.3f}")
        
        return best_strategy, confidence, hyperparams
    
    def few_shot_adapt(
        self,
        base_model: Any,
        support_set: List[Tuple[Any, Any]],  # [(input, output), ...]
        adaptation_steps: int = 5
    ) -> Any:
        """
        Perform few-shot adaptation using MAML-like approach.
        
        Args:
            base_model: Base model to adapt
            support_set: Few examples for adaptation
            adaptation_steps: Number of adaptation steps
            
        Returns:
            Adapted model
        """
        # This is a simplified version - in production would use actual MAML
        logger.info(f"Few-shot adaptation: {len(support_set)} examples, {adaptation_steps} steps")
        
        # For now, return the base model
        # In production, would perform gradient-based adaptation
        return base_model
    
    def transfer_knowledge(
        self,
        source_domain: str,
        target_domain: str,
        source_model: Any
    ) -> Dict[str, Any]:
        """
        Transfer knowledge from source to target domain.
        
        Args:
            source_domain: Source domain
            target_domain: Target domain
            source_model: Model trained on source domain
            
        Returns:
            Transfer configuration
        """
        # Find transfer patterns from similar domain transfers
        transfer_examples = [
            (task_id, meta)
            for task_id, meta in self.task_memory.items()
            if meta.domain == source_domain
        ]
        
        if not transfer_examples:
            return {
                "transfer_strategy": "full_transfer",
                "layers_to_freeze": [],
                "learning_rate_multiplier": 1.0
            }
        
        # Analyze transfer patterns
        # In production, would use actual transfer learning techniques
        return {
            "transfer_strategy": "fine_tune",
            "layers_to_freeze": [0, 1],  # Freeze first layers
            "learning_rate_multiplier": 0.1,  # Lower learning rate
            "transfer_confidence": 0.7
        }
    
    def _find_similar_tasks(
        self,
        task_description: str,
        domain: str,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find similar tasks using embeddings or features."""
        if not self.task_memory:
            return []
        
        task_features = self._extract_task_features_from_description(
            task_description, domain
        )
        
        similarities = []
        for task_id, task_meta in self.task_memory.items():
            existing_features = self._extract_task_features(task_meta)
            similarity = self._cosine_similarity(task_features, existing_features)
            similarities.append((task_id, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def _extract_task_features(self, task_meta: TaskMeta) -> np.ndarray:
        """Extract feature vector from task metadata."""
        features = np.zeros(20)
        idx = 0
        
        # Domain encoding
        domains = ["reasoning", "generation", "analysis", "planning", "evaluation"]
        if task_meta.domain in domains:
            features[domains.index(task_meta.domain)] = 1.0
        idx += len(domains)
        
        # Complexity
        features[idx] = task_meta.complexity
        idx += 1
        
        # Sample efficiency
        features[idx] = task_meta.sample_efficiency
        idx += 1
        
        # Final performance
        features[idx] = task_meta.final_performance
        idx += 1
        
        # Learning curve statistics
        if task_meta.learning_curve:
            features[idx] = np.mean(task_meta.learning_curve)
            features[idx+1] = np.std(task_meta.learning_curve)
            features[idx+2] = len(task_meta.learning_curve)
        idx += 3
        
        return features
    
    def _extract_task_features_from_description(
        self,
        description: str,
        domain: str
    ) -> np.ndarray:
        """Extract features from task description."""
        # Simplified feature extraction
        features = np.zeros(20)
        
        # Domain encoding
        domains = ["reasoning", "generation", "analysis", "planning", "evaluation"]
        if domain in domains:
            features[domains.index(domain)] = 1.0
        
        # Complexity estimate
        features[5] = min(1.0, len(description) / 500.0)
        
        return features
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _calculate_sample_efficiency(self, learning_curve: List[float]) -> float:
        """Calculate how efficiently the model learned."""
        if not learning_curve or len(learning_curve) < 2:
            return 0.5
        
        # Calculate area under learning curve (normalized)
        # Higher area = more efficient
        max_perf = max(learning_curve)
        if max_perf == 0:
            return 0.0
        
        normalized_curve = [p / max_perf for p in learning_curve]
        area = np.trapz(normalized_curve) / len(normalized_curve)
        
        return float(area)
    
    def _estimate_complexity(self, description: str, domain: str) -> float:
        """Estimate task complexity."""
        complexity = min(1.0, len(description) / 500.0)
        
        # Adjust by domain
        complex_domains = ["reasoning", "planning"]
        if domain in complex_domains:
            complexity = min(1.0, complexity + 0.2)
        
        return complexity
    
    def _infer_strategy(self, task_meta: TaskMeta) -> str:
        """Infer which strategy was likely used based on task characteristics."""
        # Heuristic: high sample efficiency suggests few-shot or transfer
        if task_meta.sample_efficiency > 0.8:
            return "few_shot"
        elif task_meta.sample_efficiency > 0.6:
            return "transfer"
        else:
            return "maml"
    
    def _aggregate_hyperparameters(
        self,
        hyperparam_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate hyperparameters from multiple tasks."""
        if not hyperparam_list:
            return self._default_hyperparameters()
        
        # Average numerical hyperparameters
        aggregated = {}
        
        # Get all keys
        all_keys = set()
        for hparams in hyperparam_list:
            all_keys.update(hparams.keys())
        
        for key in all_keys:
            values = [h.get(key) for h in hyperparam_list if key in h]
            if values:
                # Check if numeric
                if isinstance(values[0], (int, float)):
                    aggregated[key] = np.mean(values)
                else:
                    # Use most common value
                    from collections import Counter
                    aggregated[key] = Counter(values).most_common(1)[0][0]
        
        return aggregated if aggregated else self._default_hyperparameters()
    
    def _default_hyperparameters(self) -> Dict[str, Any]:
        """Get default hyperparameters."""
        return {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 10,
            "temperature": 0.7,
            "max_tokens": 1000
        }
    
    def _few_shot_adaptation(self, *args, **kwargs):
        """Few-shot learning strategy."""
        pass
    
    def _transfer_learning(self, *args, **kwargs):
        """Transfer learning strategy."""
        pass
    
    def _maml_adaptation(self, *args, **kwargs):
        """MAML (Model-Agnostic Meta-Learning) strategy."""
        pass
    
    def _reptile_adaptation(self, *args, **kwargs):
        """Reptile meta-learning strategy."""
        pass
    
    def _update_embeddings(self, features: np.ndarray, task_meta: TaskMeta):
        """Update task embeddings using meta-model."""
        if not self.meta_model:
            return
        
        try:
            # Convert to tensor
            features_tensor = torch.FloatTensor(features).unsqueeze(0)
            
            # Get embedding
            with torch.no_grad():
                embedding = self.task_encoder(features_tensor)
                self.task_embeddings[task_meta.task_id] = embedding.squeeze().numpy()
        except Exception as e:
            logger.warning(f"Failed to update embedding: {e}")
    
    def _meta_model_predict(
        self,
        task_features: np.ndarray
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Use meta-model to predict strategy and hyperparameters."""
        if not self.meta_model:
            return None
        
        try:
            features_tensor = torch.FloatTensor(task_features).unsqueeze(0)
            
            with torch.no_grad():
                embedding = self.task_encoder(features_tensor)
                strategy_probs = self.strategy_predictor(embedding)
                hyperparams_raw = self.hyperparam_predictor(embedding)
            
            # Get best strategy
            strategy_idx = torch.argmax(strategy_probs).item()
            strategy_names = list(self.strategies.keys())
            best_strategy = strategy_names[strategy_idx]
            confidence = float(strategy_probs[0][strategy_idx])
            
            # Decode hyperparameters (simplified)
            hyperparams = {
                "learning_rate": float(torch.sigmoid(hyperparams_raw[0][0])) * 0.01,
                "batch_size": int(torch.sigmoid(hyperparams_raw[0][1]) * 64) + 8,
                "epochs": int(torch.sigmoid(hyperparams_raw[0][2]) * 50) + 5,
            }
            
            return best_strategy, confidence, hyperparams
            
        except Exception as e:
            logger.warning(f"Meta-model prediction failed: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get meta-learning statistics."""
        return {
            "tasks_learned": len(self.task_memory),
            "domains": list(set(m.domain for m in self.task_memory.values())),
            "average_sample_efficiency": np.mean([
                m.sample_efficiency for m in self.task_memory.values()
            ]) if self.task_memory else 0.0,
            "meta_model_available": self.meta_model is not None
        }


