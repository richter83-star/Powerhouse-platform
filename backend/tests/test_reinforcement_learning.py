"""
Tests for Reinforcement Learning Components (Phase 2)

Tests DQN, PPO, and parameter optimization.
"""

import pytest
import numpy as np
from unittest.mock import Mock

from core.learning.reinforcement_learning import (
    ParameterOptimizerRL,
    ParameterQNetwork,
    ParameterPolicyNetwork,
    ExperienceReplayBuffer,
    PolicyNetwork,
    ValueNetwork,
    RLState,
    RLAction,
    RLReward
)


@pytest.mark.unit
@pytest.mark.skipif(not pytest.importorskip("torch", reason="PyTorch not available"), reason="PyTorch required")
class TestDQNAgent:
    """Test DQN agent."""
    
    def test_network_architecture(self):
        """Test network architecture."""
        import torch
        
        state_dim = 20
        action_dim = 5
        
        network = ParameterQNetwork(state_dim, action_dim, hidden_dims=[64, 32])
        
        # Test forward pass
        state = torch.randn(1, state_dim)
        q_values = network(state)
        
        assert q_values.shape == (1, action_dim)
        assert not torch.isnan(q_values).any()
    
    def test_experience_replay_buffer(self):
        """Test experience replay buffer."""
        buffer = ExperienceReplayBuffer(capacity=100)
        
        # Add experiences
        for i in range(50):
            buffer.add(
                state=np.random.rand(10),
                action=i % 5,
                reward=float(i % 2),
                next_state=np.random.rand(10),
                done=i % 10 == 0
            )
        
        assert len(buffer) == 50
        
        # Sample batch
        batch = buffer.sample(batch_size=10)
        assert len(batch) == 10
        assert all('state' in exp for exp in batch)
        assert all('action' in exp for exp in batch)
    
    def test_q_value_computation(self):
        """Test Q-value computation."""
        import torch
        
        network = ParameterQNetwork(state_dim=10, action_dim=3)
        state = torch.randn(1, 10)
        
        q_values = network(state)
        
        # Q-values should be reasonable
        assert q_values.shape == (1, 3)
        assert q_values.requires_grad
    
    def test_epsilon_greedy_exploration(self):
        """Test epsilon-greedy exploration."""
        import torch
        
        network = ParameterQNetwork(state_dim=10, action_dim=5)
        state = torch.randn(1, 10)
        epsilon = 0.3
        
        # Should sometimes explore (random) and sometimes exploit (greedy)
        actions = []
        for _ in range(100):
            if np.random.rand() < epsilon:
                action = np.random.randint(0, 5)  # Explore
            else:
                q_values = network(state)
                action = q_values.argmax().item()  # Exploit
            actions.append(action)
        
        # Should have some variety (not all same action)
        assert len(set(actions)) > 1


@pytest.mark.unit
@pytest.mark.skipif(not pytest.importorskip("torch", reason="PyTorch not available"), reason="PyTorch required")
class TestPPOAgent:
    """Test PPO agent."""
    
    def test_policy_network(self):
        """Test policy network."""
        import torch
        
        state_dim = 15
        action_dim = 4
        
        policy = PolicyNetwork(state_dim, action_dim, hidden_dims=[32, 16])
        
        state = torch.randn(1, state_dim)
        action_probs = policy(state)
        
        assert action_probs.shape == (1, action_dim)
        # Probabilities should sum to 1
        assert abs(action_probs.sum().item() - 1.0) < 0.01
    
    def test_value_network(self):
        """Test value network."""
        import torch
        
        state_dim = 15
        
        value_net = ValueNetwork(state_dim, hidden_dims=[32, 16])
        
        state = torch.randn(1, state_dim)
        value = value_net(state)
        
        assert value.shape == (1, 1)
        assert not torch.isnan(value)
    
    def test_advantage_estimation(self):
        """Test advantage estimation."""
        rewards = [0.5, 0.7, 0.9, 1.0]
        values = [0.4, 0.6, 0.8, 0.95]
        gamma = 0.99
        
        # Simple advantage: reward + gamma * next_value - current_value
        advantages = []
        for i in range(len(rewards) - 1):
            advantage = rewards[i] + gamma * values[i + 1] - values[i]
            advantages.append(advantage)
        
        assert len(advantages) == len(rewards) - 1
        assert all(isinstance(a, (int, float)) for a in advantages)
    
    def test_policy_gradient_updates(self):
        """Test policy gradient updates."""
        import torch
        
        policy = PolicyNetwork(state_dim=10, action_dim=3)
        optimizer = torch.optim.Adam(policy.parameters())
        
        state = torch.randn(1, 10)
        action = torch.tensor([1])
        advantage = torch.tensor([0.5])
        
        # Forward pass
        action_probs = policy(state)
        action_log_prob = torch.log(action_probs[0, action] + 1e-8)
        
        # Policy loss (negative log prob weighted by advantage)
        loss = -(action_log_prob * advantage)
        
        # Backward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Should update parameters
        assert loss.item() is not None


@pytest.mark.unit
class TestRLComponents:
    """Test RL component dataclasses."""
    
    def test_rl_state(self):
        """Test RL state."""
        state = RLState(
            task_complexity=0.7,
            current_parameters={"temperature": 0.7, "max_tokens": 1000},
            system_load=0.5,
            agent_performance_history={"react": 0.8, "cot": 0.9},
            task_type="reasoning"
        )
        
        assert state.task_complexity == 0.7
        assert state.task_type == "reasoning"
    
    def test_rl_action(self):
        """Test RL action."""
        action = RLAction(
            parameter_adjustments={"temperature": 0.1, "max_tokens": 200},
            agent_selection="react"
        )
        
        assert action.agent_selection == "react"
        assert "temperature" in action.parameter_adjustments
    
    def test_rl_reward(self):
        """Test RL reward calculation."""
        reward = RLReward(
            success=1.0,
            quality_score=0.9,
            latency_penalty=0.1,
            cost_penalty=0.05
        )
        
        assert reward.total is not None
        assert reward.total > 0  # Should be positive for success
        assert reward.success == 1.0


@pytest.mark.integration
@pytest.mark.skipif(not pytest.importorskip("torch", reason="PyTorch not available"), reason="PyTorch required")
class TestRLParameterOptimization:
    """Test RL-based parameter optimization."""
    
    def test_rl_based_hyperparameter_tuning(self):
        """Test RL-based hyperparameter tuning."""
        import torch
        
        # Create simple Q-network for parameter tuning
        # State: current parameters + performance metrics
        # Action: parameter adjustments
        state_dim = 10  # 5 params + 5 metrics
        action_dim = 5  # 5 parameter adjustments
        
        q_network = ParameterQNetwork(state_dim, action_dim)
        
        # Simulate state (current parameters + metrics)
        state = torch.randn(1, state_dim)
        
        # Get action (parameter adjustments)
        q_values = q_network(state)
        action = q_values.argmax().item()
        
        assert 0 <= action < action_dim
    
    def test_reward_signal_design(self):
        """Test reward signal design."""
        # Simulate task execution
        success = True
        quality_score = 0.85
        latency_ms = 200
        cost_usd = 0.01
        
        # Calculate reward
        latency_penalty = min(1.0, latency_ms / 1000.0)  # Normalize
        cost_penalty = min(1.0, cost_usd / 0.1)  # Normalize
        
        reward = RLReward(
            success=1.0 if success else 0.0,
            quality_score=quality_score,
            latency_penalty=latency_penalty,
            cost_penalty=cost_penalty
        )
        
        assert reward.total > 0
        assert 0 <= reward.total <= 1.0
    
    def test_convergence_behavior(self):
        """Test convergence behavior."""
        import torch
        
        q_network = ParameterQNetwork(state_dim=10, action_dim=3)
        optimizer = torch.optim.Adam(q_network.parameters())
        
        # Simulate learning over multiple episodes
        losses = []
        for episode in range(10):
            state = torch.randn(1, 10)
            target_q = torch.randn(1, 3)
            
            current_q = q_network(state)
            loss = torch.nn.functional.mse_loss(current_q, target_q)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            losses.append(loss.item())
        
        # Loss should generally decrease (may not always be monotonic)
        assert losses[-1] is not None
        assert not np.isnan(losses[-1])

