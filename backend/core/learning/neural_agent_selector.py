"""
Neural network-based agent selection model.

This module implements a neural network model for selecting the best agent
for a given task, replacing simple statistical tracking with learned patterns.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from collections import deque
import pickle
from pathlib import Path

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Use sklearn as fallback
    try:
        from sklearn.neural_network import MLPRegressor
        from sklearn.preprocessing import StandardScaler
        SKLEARN_AVAILABLE = True
    except ImportError:
        SKLEARN_AVAILABLE = False

from utils.logging import get_logger
from core.feedback_pipeline import OutcomeEvent, OutcomeStatus

logger = get_logger(__name__)


@dataclass
class AgentSelectionFeatures:
    """Features for agent selection model."""
    task_complexity: float  # 0.0-1.0
    task_type_encoded: np.ndarray  # One-hot encoding
    context_features: np.ndarray  # Contextual features
    agent_history_success_rate: float  # Historical success rate
    agent_history_latency: float  # Historical average latency
    current_load: float  # Current system load
    available_resources: float  # Available compute resources


class NeuralAgentSelector:
    """
    Neural network model for selecting the best agent for a task.
    
    Uses either PyTorch (if available) or scikit-learn as fallback.
    """
    
    def __init__(
        self,
        model_id: str = "neural_agent_selector_v1",
        input_dim: int = 50,  # Dimension of feature vector
        hidden_dims: List[int] = [64, 32],
        num_agents: int = 19,
        learning_rate: float = 0.001
    ):
        """
        Initialize neural agent selector.
        
        Args:
            model_id: Model identifier
            input_dim: Input feature dimension
            hidden_dims: Hidden layer dimensions
            num_agents: Number of agents to choose from
            learning_rate: Learning rate for optimization
        """
        self.model_id = model_id
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.num_agents = num_agents
        self.learning_rate = learning_rate
        
        self.training_data: deque = deque(maxlen=1000)
        self.update_count = 0
        self.last_update = datetime.utcnow()
        
        # Initialize model
        self.model = None
        self.scaler = None
        self._initialize_model()
        
        logger.info(f"Initialized NeuralAgentSelector (PyTorch: {TORCH_AVAILABLE}, sklearn: {SKLEARN_AVAILABLE})")
    
    def _initialize_model(self):
        """Initialize the neural network model."""
        if TORCH_AVAILABLE:
            self._init_pytorch_model()
        elif SKLEARN_AVAILABLE:
            self._init_sklearn_model()
        else:
            logger.warning("Neither PyTorch nor sklearn available. Using fallback model.")
            self.model = None
    
    def _init_pytorch_model(self):
        """Initialize PyTorch neural network."""
        layers = []
        prev_dim = self.input_dim
        
        # Build hidden layers
        for hidden_dim in self.hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim
        
        # Output layer (scores for each agent)
        layers.append(nn.Linear(prev_dim, self.num_agents))
        
        self.model = nn.Sequential(*layers)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()
        self.model.train()
        
        logger.info("Initialized PyTorch neural network model")
    
    def _init_sklearn_model(self):
        """Initialize sklearn MLP model."""
        hidden_layer_sizes = tuple(self.hidden_dims)
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden_layer_sizes,
            learning_rate_init=self.learning_rate,
            max_iter=500,
            random_state=42,
            early_stopping=True
        )
        self.scaler = StandardScaler()
        logger.info("Initialized sklearn MLP model")
    
    def extract_features(
        self,
        task: str,
        task_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        agent_name: Optional[str] = None,
        agent_history: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Extract features for agent selection.
        
        Args:
            task: Task description
            task_type: Type of task
            context: Task context
            agent_name: Agent name (for history lookup)
            agent_history: Agent performance history
            
        Returns:
            Feature vector
        """
        features = np.zeros(self.input_dim)
        idx = 0
        
        # Task complexity (simple heuristic based on length and keywords)
        task_complexity = min(1.0, len(task) / 500.0)  # Normalize by max expected length
        complexity_keywords = ["analyze", "synthesize", "evaluate", "compare", "design"]
        for keyword in complexity_keywords:
            if keyword in task.lower():
                task_complexity += 0.1
        task_complexity = min(1.0, task_complexity)
        features[idx] = task_complexity
        idx += 1
        
        # Task type encoding (simple one-hot for common types)
        task_types = ["reasoning", "analysis", "generation", "planning", "evaluation"]
        task_type_encoded = np.zeros(len(task_types))
        if task_type:
            try:
                type_idx = task_types.index(task_type.lower())
                task_type_encoded[type_idx] = 1.0
            except ValueError:
                pass
        features[idx:idx+len(task_types)] = task_type_encoded
        idx += len(task_types)
        
        # Agent history features
        if agent_history:
            features[idx] = agent_history.get("success_rate", 0.5)
            features[idx+1] = agent_history.get("avg_latency_ms", 1000.0) / 10000.0  # Normalize
            features[idx+2] = agent_history.get("total_runs", 0) / 100.0  # Normalize
        else:
            features[idx:idx+3] = [0.5, 0.1, 0.0]  # Defaults
        idx += 3
        
        # Context features
        if context:
            context_features = [
                context.get("complexity", 0.5),
                context.get("urgency", 0.5),
                len(context.get("outputs", [])) / 10.0,  # Normalize
            ]
            features[idx:idx+len(context_features)] = context_features
            idx += len(context_features)
        
        # System features (placeholder - would come from system monitoring)
        system_features = [
            0.5,  # Current load (normalized)
            0.8,  # Available resources (normalized)
        ]
        features[idx:idx+len(system_features)] = system_features
        idx += len(system_features)
        
        # Pad or truncate to exact dimension
        if idx < self.input_dim:
            features[idx:] = 0.0
        elif idx > self.input_dim:
            features = features[:self.input_dim]
        
        return features
    
    def predict_agent_scores(
        self,
        task: str,
        task_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        agent_histories: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[Tuple[str, float]]:
        """
        Predict scores for all agents.
        
        Args:
            task: Task description
            task_type: Type of task
            context: Task context
            agent_histories: Histories for all agents
            
        Returns:
            List of (agent_name, score) tuples, sorted by score descending
        """
        if self.model is None:
            # Fallback to uniform scores
            logger.warning("Model not initialized, returning uniform scores")
            agent_names = list(agent_histories.keys()) if agent_histories else []
            return [(name, 0.5) for name in agent_names]
        
        agent_histories = agent_histories or {}
        
        # Extract features for each agent
        all_features = []
        agent_names = []
        
        for agent_name, history in agent_histories.items():
            features = self.extract_features(
                task=task,
                task_type=task_type,
                context=context,
                agent_name=agent_name,
                agent_history=history
            )
            all_features.append(features)
            agent_names.append(agent_name)
        
        if not all_features:
            return []
        
        X = np.array(all_features)
        
        # Predict using model
        if TORCH_AVAILABLE and isinstance(self.model, nn.Module):
            self.model.eval()
            with torch.no_grad():
                X_tensor = torch.FloatTensor(X)
                scores = self.model(X_tensor).numpy()
                # Get scores for each agent (take mean or max of output)
                agent_scores = scores.mean(axis=1) if len(scores.shape) > 1 else scores
        elif SKLEARN_AVAILABLE and hasattr(self.model, 'predict'):
            # Scale features
            if self.scaler:
                X_scaled = self.scaler.transform(X)
            else:
                X_scaled = X
            # Predict (returns scores per agent)
            scores = self.model.predict(X_scaled)
            agent_scores = scores if isinstance(scores, np.ndarray) else np.array([scores])
        else:
            # Fallback
            agent_scores = np.array([0.5] * len(agent_names))
        
        # Combine agent names with scores
        results = list(zip(agent_names, agent_scores))
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def update(self, event: OutcomeEvent, features: Optional[np.ndarray] = None) -> None:
        """
        Update model with outcome event.
        
        Args:
            event: Outcome event from agent execution
            features: Feature vector used for prediction (optional)
        """
        # Create training sample
        if features is None:
            features = self.extract_features(
                task=event.action_type or "",
                task_type=event.action_type,
                agent_name=event.agent_name
            )
        
        # Target: success score (1.0 for success, 0.0 for failure)
        target = 1.0 if event.status == OutcomeStatus.SUCCESS else 0.0
        
        # Adjust target based on quality score if available
        if event.quality_score is not None:
            target = event.quality_score
        
        # Store training data
        self.training_data.append({
            "features": features,
            "target": target,
            "agent_name": event.agent_name,
            "timestamp": datetime.utcnow()
        })
        
        self.update_count += 1
        self.last_update = datetime.utcnow()
        
        # Trigger training if we have enough data
        if len(self.training_data) >= 50 and len(self.training_data) % 10 == 0:
            self._train()
    
    def _train(self):
        """Train the model on collected data."""
        if len(self.training_data) < 10:
            return
        
        # Prepare training data
        X = np.array([sample["features"] for sample in self.training_data])
        y = np.array([sample["target"] for sample in self.training_data])
        
        if TORCH_AVAILABLE and isinstance(self.model, nn.Module):
            self._train_pytorch(X, y)
        elif SKLEARN_AVAILABLE and hasattr(self.model, 'fit'):
            self._train_sklearn(X, y)
    
    def _train_pytorch(self, X: np.ndarray, y: np.ndarray):
        """Train PyTorch model."""
        try:
            self.model.train()
            
            # Convert to tensors
            X_tensor = torch.FloatTensor(X)
            y_tensor = torch.FloatTensor(y).unsqueeze(1)  # Add dimension for output
            
            # Expand y to match output dimension (repeat for each agent score)
            # This is simplified - in production, we'd have proper multi-output
            y_expanded = y_tensor.repeat(1, self.num_agents)
            
            # Training loop (mini-batch)
            batch_size = min(32, len(X))
            for epoch in range(5):  # Quick training
                # Shuffle
                indices = torch.randperm(len(X))
                X_shuffled = X_tensor[indices]
                y_shuffled = y_expanded[indices]
                
                # Mini-batch training
                for i in range(0, len(X), batch_size):
                    batch_X = X_shuffled[i:i+batch_size]
                    batch_y = y_shuffled[i:i+batch_size]
                    
                    # Forward pass
                    self.optimizer.zero_grad()
                    output = self.model(batch_X)
                    loss = self.criterion(output, batch_y)
                    
                    # Backward pass
                    loss.backward()
                    self.optimizer.step()
            
            logger.debug(f"PyTorch model trained on {len(X)} samples, loss: {loss.item():.4f}")
            
        except Exception as e:
            logger.error(f"Error training PyTorch model: {e}", exc_info=True)
    
    def _train_sklearn(self, X: np.ndarray, y: np.ndarray):
        """Train sklearn model."""
        try:
            # Scale features
            if self.scaler:
                X_scaled = self.scaler.fit_transform(X)
            else:
                self.scaler = StandardScaler()
                X_scaled = self.scaler.fit_transform(X)
            
            # For sklearn, we need to create target for each agent
            # Simplified: use mean of all targets (in production, track per-agent)
            y_mean = y.mean()
            y_expanded = np.full((len(X), self.num_agents), y_mean)
            
            # Train
            self.model.fit(X_scaled, y_expanded)
            
            logger.debug(f"sklearn model trained on {len(X)} samples")
            
        except Exception as e:
            logger.error(f"Error training sklearn model: {e}", exc_info=True)
    
    def save(self, filepath: str) -> None:
        """Save model to file."""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            save_data = {
                "model_id": self.model_id,
                "input_dim": self.input_dim,
                "hidden_dims": self.hidden_dims,
                "num_agents": self.num_agents,
                "update_count": self.update_count,
                "last_update": self.last_update.isoformat(),
                "training_data": list(self.training_data)
            }
            
            if TORCH_AVAILABLE and isinstance(self.model, nn.Module):
                save_data["model_state"] = self.model.state_dict()
                save_data["optimizer_state"] = self.optimizer.state_dict()
                save_data["model_type"] = "pytorch"
            elif SKLEARN_AVAILABLE:
                save_data["model"] = self.model
                save_data["scaler"] = self.scaler
                save_data["model_type"] = "sklearn"
            
            with open(path, 'wb') as f:
                pickle.dump(save_data, f)
            
            logger.info(f"Saved model to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}", exc_info=True)
    
    def load(self, filepath: str) -> None:
        """Load model from file."""
        try:
            path = Path(filepath)
            if not path.exists():
                logger.warning(f"Model file not found: {filepath}")
                return
            
            with open(path, 'rb') as f:
                save_data = pickle.load(f)
            
            self.model_id = save_data.get("model_id", self.model_id)
            self.input_dim = save_data.get("input_dim", self.input_dim)
            self.hidden_dims = save_data.get("hidden_dims", self.hidden_dims)
            self.num_agents = save_data.get("num_agents", self.num_agents)
            self.update_count = save_data.get("update_count", 0)
            
            model_type = save_data.get("model_type", "unknown")
            
            if model_type == "pytorch" and TORCH_AVAILABLE:
                self._init_pytorch_model()
                self.model.load_state_dict(save_data["model_state"])
                self.optimizer.load_state_dict(save_data["optimizer_state"])
            elif model_type == "sklearn" and SKLEARN_AVAILABLE:
                self.model = save_data["model"]
                self.scaler = save_data.get("scaler")
            
            self.training_data = deque(save_data.get("training_data", []), maxlen=1000)
            
            logger.info(f"Loaded model from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}", exc_info=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "model_id": self.model_id,
            "input_dim": self.input_dim,
            "hidden_dims": self.hidden_dims,
            "num_agents": self.num_agents,
            "update_count": self.update_count,
            "last_update": self.last_update.isoformat(),
            "training_samples": len(self.training_data),
            "model_type": "pytorch" if (TORCH_AVAILABLE and isinstance(self.model, nn.Module)) else "sklearn" if SKLEARN_AVAILABLE else "none"
        }

