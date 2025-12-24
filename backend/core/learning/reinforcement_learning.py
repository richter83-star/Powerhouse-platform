"""
Reinforcement Learning components for parameter optimization.

Implements Q-learning and policy gradient methods for optimizing
LLM parameters and agent selection policies.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import random
import numpy as np
from collections import deque, defaultdict

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Create dummy nn module for when PyTorch is not available
    class _DummyNN:
        class Module:
            pass
        class Linear:
            pass
        class ReLU:
            pass
        class Sequential:
            pass
        class MSELoss:
            pass
        class Tanh:
            pass
        class Softmax:
            pass
    nn = _DummyNN()
    torch = None
    F = None

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RLState:
    """State in the RL environment."""
    task_complexity: float
    current_parameters: Dict[str, float]  # LLM parameters
    system_load: float
    agent_performance_history: Dict[str, float]
    task_type: Optional[str] = None


@dataclass
class RLAction:
    """Action in the RL environment."""
    parameter_adjustments: Dict[str, float]  # Adjustments to LLM parameters
    agent_selection: Optional[str] = None


@dataclass
class RLReward:
    """Reward signal for RL."""
    success: float  # 1.0 for success, 0.0 for failure
    quality_score: float  # 0.0-1.0
    latency_penalty: float  # Negative reward for high latency
    cost_penalty: float  # Negative reward for high cost
    total: float  # Combined reward
    
    def __post_init__(self):
        if not hasattr(self, 'total') or self.total is None:
            # Calculate total reward
            self.total = (
                self.success * 0.4 +
                self.quality_score * 0.3 -
                self.latency_penalty * 0.2 -
                self.cost_penalty * 0.1
            )


class ExperienceReplayBuffer:
    """Simple experience replay buffer for off-policy RL."""

    def __init__(self, capacity: int = 10000) -> None:
        self._buffer = deque(maxlen=capacity)

    def add(self, state: np.ndarray, action: Any, reward: float, next_state: np.ndarray, done: bool) -> None:
        """Add a transition to the buffer."""
        self._buffer.append(
            {
                "state": state,
                "action": action,
                "reward": reward,
                "next_state": next_state,
                "done": done,
            }
        )

    def sample(self, batch_size: int) -> List[Dict[str, Any]]:
        """Sample a batch of transitions."""
        if batch_size <= 0:
            return []
        return random.sample(self._buffer, min(batch_size, len(self._buffer)))

    def __len__(self) -> int:
        return len(self._buffer)


if TORCH_AVAILABLE:
    class ParameterQNetwork(nn.Module):
        """Q-Network for parameter optimization."""
        
        def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = [128, 64]):
            """
            Initialize Q-network.
            
            Args:
                state_dim: Dimension of state representation
                action_dim: Dimension of action space
                hidden_dims: Hidden layer dimensions
            """
            super().__init__()
            
            layers = []
            prev_dim = state_dim
            
            for hidden_dim in hidden_dims:
                layers.append(nn.Linear(prev_dim, hidden_dim))
                layers.append(nn.ReLU())
                prev_dim = hidden_dim
            
            layers.append(nn.Linear(prev_dim, action_dim))
            
            self.network = nn.Sequential(*layers)
        
        def forward(self, state: torch.Tensor) -> torch.Tensor:
            """Forward pass."""
            return self.network(state)
else:
    # Dummy classes when PyTorch is not available
    class ParameterQNetwork:
        pass


if TORCH_AVAILABLE:
    class ParameterPolicyNetwork(nn.Module):
        """Policy network for parameter optimization using policy gradients."""
        
        def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = [128, 64]):
            """
            Initialize policy network.
            
            Args:
                state_dim: Dimension of state representation
                action_dim: Dimension of action space
                hidden_dims: Hidden layer dimensions
            """
            super().__init__()
            
            # Shared feature extractor
            layers = []
            prev_dim = state_dim
            
            for hidden_dim in hidden_dims:
                layers.append(nn.Linear(prev_dim, hidden_dim))
                layers.append(nn.ReLU())
                prev_dim = hidden_dim
            
            self.feature_extractor = nn.Sequential(*layers)
            
            # Action mean and std (for continuous actions)
            self.action_mean = nn.Linear(prev_dim, action_dim)
            self.action_std = nn.Linear(prev_dim, action_dim)
        
        def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
            """Forward pass."""
            features = self.feature_extractor(state)
            mean = torch.tanh(self.action_mean(features))  # Bound to [-1, 1]
            std = F.softplus(self.action_std(features)) + 0.01  # Ensure positive std
            return mean, std
        
        def sample(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
            """Sample action from policy."""
            mean, std = self.forward(state)
            dist = torch.distributions.Normal(mean, std)
            action = dist.sample()
            log_prob = dist.log_prob(action).sum(dim=-1, keepdim=True)
            return action, log_prob
else:
    # Dummy class when PyTorch is not available
    class ParameterPolicyNetwork:
        pass


if TORCH_AVAILABLE:
    class PolicyNetwork(nn.Module):
        """Policy network for discrete action selection."""

        def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = [64, 32]):
            super().__init__()
            layers = []
            prev_dim = state_dim

            for hidden_dim in hidden_dims:
                layers.append(nn.Linear(prev_dim, hidden_dim))
                layers.append(nn.ReLU())
                prev_dim = hidden_dim

            layers.append(nn.Linear(prev_dim, action_dim))
            self.network = nn.Sequential(*layers)
            self.softmax = nn.Softmax(dim=-1)

        def forward(self, state: torch.Tensor) -> torch.Tensor:
            logits = self.network(state)
            return self.softmax(logits)
else:
    class PolicyNetwork:
        pass


if TORCH_AVAILABLE:
    class ValueNetwork(nn.Module):
        """Value network for state-value estimation."""

        def __init__(self, state_dim: int, hidden_dims: List[int] = [64, 32]):
            super().__init__()
            layers = []
            prev_dim = state_dim

            for hidden_dim in hidden_dims:
                layers.append(nn.Linear(prev_dim, hidden_dim))
                layers.append(nn.ReLU())
                prev_dim = hidden_dim

            layers.append(nn.Linear(prev_dim, 1))
            self.network = nn.Sequential(*layers)

        def forward(self, state: torch.Tensor) -> torch.Tensor:
            return self.network(state)
else:
    class ValueNetwork:
        pass


class ParameterOptimizerRL:
    """
    Reinforcement Learning agent for optimizing LLM parameters.
    
    Uses either Q-learning or policy gradients to learn optimal parameter values
    based on task outcomes.
    """
    
    def __init__(
        self,
        state_dim: int = 20,
        action_dim: int = 3,  # temperature, max_tokens, top_p
        algorithm: str = "dqn",  # "dqn" or "ppo"
        learning_rate: float = 0.001,
        gamma: float = 0.99,  # Discount factor
        epsilon: float = 1.0,  # Exploration rate (for DQN)
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
        replay_buffer_size: int = 10000,
        batch_size: int = 64
    ):
        """
        Initialize RL optimizer.
        
        Args:
            state_dim: Dimension of state representation
            action_dim: Dimension of action space
            algorithm: RL algorithm ("dqn" or "ppo")
            learning_rate: Learning rate
            gamma: Discount factor
            epsilon: Initial exploration rate (DQN)
            epsilon_decay: Epsilon decay rate
            epsilon_min: Minimum epsilon
            replay_buffer_size: Size of experience replay buffer
            batch_size: Training batch size
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for ParameterOptimizerRL")
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.algorithm = algorithm
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.batch_size = batch_size
        
        # Initialize networks
        if algorithm == "dqn":
            self.q_network = ParameterQNetwork(state_dim, action_dim)
            self.target_q_network = ParameterQNetwork(state_dim, action_dim)
            self.target_q_network.load_state_dict(self.q_network.state_dict())
            self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
            self.replay_buffer = deque(maxlen=replay_buffer_size)
            
        elif algorithm == "ppo":
            self.policy_network = ParameterPolicyNetwork(state_dim, action_dim)
            self.optimizer = optim.Adam(self.policy_network.parameters(), lr=learning_rate)
            self.trajectory_buffer = []
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        if algorithm == "dqn":
            self.q_network.to(self.device)
            self.target_q_network.to(self.device)
        else:
            self.policy_network.to(self.device)
        
        # Training stats
        self.total_updates = 0
        self.total_reward = 0.0
        self.episode_rewards = deque(maxlen=100)
        
        logger.info(
            f"Initialized RL optimizer: algorithm={algorithm}, "
            f"state_dim={state_dim}, action_dim={action_dim}"
        )
    
    def encode_state(self, state: RLState) -> np.ndarray:
        """
        Encode state to feature vector.
        
        Args:
            state: RL state
            
        Returns:
            Feature vector
        """
        features = np.zeros(self.state_dim)
        idx = 0
        
        # Task complexity
        features[idx] = state.task_complexity
        idx += 1
        
        # Current parameters (temperature, max_tokens, top_p)
        params = state.current_parameters
        features[idx] = params.get("temperature", 0.7)
        features[idx+1] = params.get("max_tokens", 1000) / 4000.0  # Normalize
        features[idx+2] = params.get("top_p", 0.9)
        idx += 3
        
        # System load
        features[idx] = state.system_load
        idx += 1
        
        # Agent performance history (top 5 agents)
        perf_values = list(state.agent_performance_history.values())[:5]
        features[idx:idx+len(perf_values)] = perf_values
        idx += 5
        
        # Task type encoding
        task_types = ["reasoning", "generation", "analysis", "planning"]
        if state.task_type:
            try:
                type_idx = task_types.index(state.task_type.lower())
                features[idx+type_idx] = 1.0
            except ValueError:
                pass
        idx += len(task_types)
        
        # Pad if needed
        if idx < self.state_dim:
            features[idx:] = 0.0
        elif idx > self.state_dim:
            features = features[:self.state_dim]
        
        return features
    
    def decode_action(self, action: np.ndarray) -> Dict[str, float]:
        """
        Decode action vector to parameter adjustments.
        
        Args:
            action: Action vector (typically [-1, 1] range)
            
        Returns:
            Parameter adjustments
        """
        # Scale actions to reasonable ranges
        adjustments = {
            "temperature": float(np.clip(action[0] * 0.2, -0.5, 0.5)),  # ±0.5 adjustment
            "max_tokens": int(np.clip(action[1] * 500, -1000, 1000)),  # ±1000 tokens
            "top_p": float(np.clip(action[2] * 0.1, -0.3, 0.3))  # ±0.3 adjustment
        }
        return adjustments
    
    def select_action(self, state: RLState, training: bool = True) -> RLAction:
        """
        Select action given current state.
        
        Args:
            state: Current state
            training: Whether in training mode (affects exploration)
            
        Returns:
            Selected action
        """
        state_features = self.encode_state(state)
        state_tensor = torch.FloatTensor(state_features).unsqueeze(0).to(self.device)
        
        if self.algorithm == "dqn":
            # Epsilon-greedy action selection
            if training and np.random.random() < self.epsilon:
                # Explore: random action
                action = np.random.uniform(-1, 1, self.action_dim)
            else:
                # Exploit: select best action
                with torch.no_grad():
                    q_values = self.q_network(state_tensor)
                    action = q_values.cpu().numpy().squeeze()
                    # Convert Q-values to actions (assuming continuous action space)
                    action = np.tanh(action)  # Bound to [-1, 1]
            
            # Decay epsilon
            if training:
                self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        else:  # PPO
            if training:
                action_tensor, _ = self.policy_network.sample(state_tensor)
                action = action_tensor.cpu().numpy().squeeze()
            else:
                mean, _ = self.policy_network(state_tensor)
                action = mean.cpu().numpy().squeeze()
        
        # Decode to parameter adjustments
        parameter_adjustments = self.decode_action(action)
        
        return RLAction(parameter_adjustments=parameter_adjustments)
    
    def update(
        self,
        state: RLState,
        action: RLAction,
        reward: RLReward,
        next_state: Optional[RLState] = None,
        done: bool = False
    ) -> None:
        """
        Update RL agent with experience.
        
        Args:
            state: Current state
            action: Action taken
            next_state: Next state (None if done)
            reward: Reward received
            done: Whether episode is done
        """
        state_features = self.encode_state(state)
        
        if self.algorithm == "dqn":
            # Store in replay buffer
            next_features = self.encode_state(next_state) if next_state else np.zeros(self.state_dim)
            action_encoded = np.array([
                action.parameter_adjustments.get("temperature", 0),
                action.parameter_adjustments.get("max_tokens", 0) / 1000.0,
                action.parameter_adjustments.get("top_p", 0)
            ])
            
            self.replay_buffer.append((
                state_features,
                action_encoded,
                reward.total,
                next_features,
                done
            ))
            
            # Train from replay buffer
            if len(self.replay_buffer) >= self.batch_size:
                self._train_dqn()
        
        else:  # PPO
            # Store in trajectory buffer
            action_encoded = np.array([
                action.parameter_adjustments.get("temperature", 0),
                action.parameter_adjustments.get("max_tokens", 0) / 1000.0,
                action.parameter_adjustments.get("top_p", 0)
            ])
            
            self.trajectory_buffer.append((
                state_features,
                action_encoded,
                reward.total,
                next_state
            ))
            
            if done and len(self.trajectory_buffer) > 0:
                self._train_ppo()
                self.trajectory_buffer.clear()
        
        self.total_reward += reward.total
        if done:
            self.episode_rewards.append(self.total_reward)
            self.total_reward = 0.0
    
    def _train_dqn(self):
        """Train DQN from replay buffer."""
        if len(self.replay_buffer) < self.batch_size:
            return
        
        # Sample batch
        batch = np.random.choice(len(self.replay_buffer), self.batch_size, replace=False)
        batch_data = [self.replay_buffer[i] for i in batch]
        
        states = torch.FloatTensor([s[0] for s in batch_data]).to(self.device)
        actions = torch.FloatTensor([s[1] for s in batch_data]).to(self.device)
        rewards = torch.FloatTensor([s[2] for s in batch_data]).to(self.device)
        next_states = torch.FloatTensor([s[3] for s in batch_data]).to(self.device)
        dones = torch.BoolTensor([s[4] for s in batch_data]).to(self.device)
        
        # Compute Q-values
        q_values = self.q_network(states)
        
        # Compute target Q-values
        with torch.no_grad():
            next_q_values = self.target_q_network(next_states)
            target_q_values = rewards + (1 - dones.float()) * self.gamma * next_q_values.max(dim=1)[0]
        
        # Compute loss
        # Note: This is simplified - in production, use proper action selection
        loss = nn.MSELoss()(q_values.mean(dim=1), target_q_values)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()
        
        # Update target network (soft update)
        tau = 0.01
        for target_param, param in zip(self.target_q_network.parameters(), self.q_network.parameters()):
            target_param.data.copy_(tau * param.data + (1 - tau) * target_param.data)
        
        self.total_updates += 1
        
        if self.total_updates % 100 == 0:
            logger.debug(f"DQN training: updates={self.total_updates}, loss={loss.item():.4f}")
    
    def _train_ppo(self):
        """Train PPO from trajectory buffer."""
        if len(self.trajectory_buffer) < 10:
            return
        
        # Compute returns
        returns = []
        G = 0
        for _, _, reward, _ in reversed(self.trajectory_buffer):
            G = reward + self.gamma * G
            returns.insert(0, G)
        
        returns = torch.FloatTensor(returns).to(self.device)
        returns = (returns - returns.mean()) / (returns.std() + 1e-8)  # Normalize
        
        # Prepare data
        states = torch.FloatTensor([s[0] for s in self.trajectory_buffer]).to(self.device)
        actions = torch.FloatTensor([s[1] for s in self.trajectory_buffer]).to(self.device)
        
        # Get old log probs
        with torch.no_grad():
            _, old_log_probs = self.policy_network.sample(states)
        
        # PPO update (simplified)
        for _ in range(4):  # Multiple epochs
            mean, std = self.policy_network(states)
            dist = torch.distributions.Normal(mean, std)
            new_log_probs = dist.log_prob(actions).sum(dim=-1, keepdim=True)
            
            # Importance sampling ratio
            ratio = torch.exp(new_log_probs - old_log_probs)
            
            # PPO clipped objective
            advantages = returns.unsqueeze(1)  # Simplified
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 0.8, 1.2) * advantages
            loss = -torch.min(surr1, surr2).mean()
            
            # Optimize
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy_network.parameters(), 1.0)
            self.optimizer.step()
        
        self.total_updates += 1
        logger.debug(f"PPO training: updates={self.total_updates}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get training statistics."""
        stats = {
            "algorithm": self.algorithm,
            "total_updates": self.total_updates,
            "epsilon": self.epsilon if self.algorithm == "dqn" else None,
            "episode_count": len(self.episode_rewards),
            "average_reward": np.mean(self.episode_rewards) if self.episode_rewards else 0.0,
            "last_reward": self.episode_rewards[-1] if self.episode_rewards else 0.0
        }
        return stats

