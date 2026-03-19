"""
Swarm Feedback Bridge: Bidirectional signal flow between RL and Swarm execution.

This module closes the feedback loop between the RL parameter optimizer and the
Swarm orchestrator. Swarm execution outcomes are translated into RL reward signals
so the Q-network learns to improve agent parameter selection over time.

Signal flow:
    SwarmOrchestrator.execute_swarm() → SwarmExecutionFeedback
    → RL.ingest_swarm_outcome() → Q-network update
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.learning.reinforcement_learning import (
    ParameterOptimizerRL,
    RLAction,
    RLReward,
    RLState,
    TORCH_AVAILABLE,
)
from utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data transfer object
# ---------------------------------------------------------------------------

@dataclass
class SwarmExecutionFeedback:
    """
    Captures a single swarm execution outcome for RL ingestion.

    Fields map directly to the components of RLReward so that the bridge
    can construct the reward signal without external heuristics.
    """

    # Execution identity
    run_id: str
    task: str
    task_type: Optional[str] = None

    # Outcome quality (0.0 – 1.0 each)
    success: float = 0.0          # Did the swarm produce a usable result?
    quality_score: float = 0.0    # Quality of the best agent output

    # Cost signals (positive = penalty, will be negated in reward)
    latency_ms: float = 0.0       # Wall-clock time of execute_swarm()
    cost_estimate: float = 0.0    # Token / API cost proxy

    # System snapshot at execution time
    system_load: float = 0.5
    num_agents: int = 1

    # Per-agent performance snapshot used to build RLState
    agent_performance: Dict[str, float] = field(default_factory=dict)

    # The LLM parameters that were in effect during this swarm run
    parameters_used: Dict[str, float] = field(default_factory=dict)

    # Raw swarm result for logging / debugging
    raw_result: Optional[Dict[str, Any]] = None

    timestamp: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------

class SwarmFeedbackBridge:
    """
    Bidirectional bridge between SwarmOrchestrator and ParameterOptimizerRL.

    Responsibilities:
    - Convert swarm outcomes into (RLState, RLAction, RLReward) triples.
    - Feed those triples into the RL agent's update() method.
    - Expose the RL agent's recommended parameter adjustments so the swarm
      orchestrator can apply them before the next execution.
    - Keep a rolling history for diagnostics.

    Usage (in ph_server.py or orchestration loop)::

        bridge = SwarmFeedbackBridge(rl_optimizer)

        # After a swarm run:
        feedback = SwarmExecutionFeedback(
            run_id=run_id, task=task, success=1.0, quality_score=0.85,
            latency_ms=1200.0, parameters_used=current_params,
            agent_performance=agent_stats,
        )
        bridge.ingest_swarm_outcome(feedback)

        # Before the next swarm run:
        adjustments = bridge.get_recommended_adjustments(task, system_load)
    """

    # Normalisation constants
    _MAX_LATENCY_MS: float = 30_000.0   # 30 s ceiling for latency penalty
    _MAX_COST: float = 1.0              # Relative cost ceiling

    def __init__(
        self,
        rl_optimizer: Optional[ParameterOptimizerRL] = None,
        *,
        state_dim: int = 20,
        action_dim: int = 3,
        algorithm: str = "dqn",
        latency_penalty_weight: float = 0.2,
        cost_penalty_weight: float = 0.1,
    ) -> None:
        """
        Args:
            rl_optimizer: Pre-existing RL optimizer.  If None and PyTorch is
                available, one is created automatically.
            state_dim: State vector dimensionality forwarded to RL agent.
            action_dim: Action vector dimensionality.
            algorithm: "dqn" or "ppo".
            latency_penalty_weight: Reward weight for latency penalty.
            cost_penalty_weight: Reward weight for cost penalty.
        """
        self.latency_penalty_weight = latency_penalty_weight
        self.cost_penalty_weight = cost_penalty_weight

        if rl_optimizer is not None:
            self.rl = rl_optimizer
        elif TORCH_AVAILABLE:
            self.rl = ParameterOptimizerRL(
                state_dim=state_dim,
                action_dim=action_dim,
                algorithm=algorithm,
            )
            logger.info("SwarmFeedbackBridge created new ParameterOptimizerRL instance")
        else:
            self.rl = None
            logger.warning(
                "PyTorch unavailable – SwarmFeedbackBridge running in no-op mode"
            )

        # Rolling history for diagnostics
        self._history: List[SwarmExecutionFeedback] = []
        self._last_state: Optional[RLState] = None
        self._last_action: Optional[RLAction] = None
        self._ingestion_count: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest_swarm_outcome(self, feedback: SwarmExecutionFeedback) -> None:
        """
        Translate a swarm execution outcome into an RL update.

        This is the primary entry point.  Call it once after every
        ``SwarmOrchestrator.execute_swarm()`` invocation.
        """
        self._history.append(feedback)

        if self.rl is None:
            logger.debug("RL unavailable – skipping ingest")
            return

        state = self._build_rl_state(feedback)
        action = self._build_rl_action(feedback)
        reward = self._build_rl_reward(feedback)

        # If we have a previous (state, action) pair we can form a proper
        # transition.  On the very first call we still do a single-step
        # update which seeds the replay buffer.
        self.rl.update(
            state=self._last_state if self._last_state else state,
            action=self._last_action if self._last_action else action,
            reward=reward,
            next_state=state,
            done=False,
        )

        self._last_state = state
        self._last_action = action
        self._ingestion_count += 1

        logger.debug(
            "RL update #%d | reward=%.3f (success=%.2f, quality=%.2f, "
            "lat_pen=%.3f, cost_pen=%.3f)",
            self._ingestion_count,
            reward.total,
            reward.success,
            reward.quality_score,
            reward.latency_penalty,
            reward.cost_penalty,
        )

    def get_recommended_adjustments(
        self,
        task: str = "",
        system_load: float = 0.5,
        current_parameters: Optional[Dict[str, float]] = None,
        agent_performance: Optional[Dict[str, float]] = None,
        task_type: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Ask the RL agent for its recommended parameter adjustments.

        Returns an empty dict when RL is unavailable or not yet trained.
        """
        if self.rl is None:
            return {}

        state = RLState(
            task_complexity=min(1.0, len(task) / 500.0),
            current_parameters=current_parameters or {
                "temperature": 0.7,
                "max_tokens": 1000,
                "top_p": 0.9,
            },
            system_load=system_load,
            agent_performance_history=agent_performance or {},
            task_type=task_type,
        )

        action = self.rl.select_action(state, training=False)
        return action.parameter_adjustments

    def get_statistics(self) -> Dict[str, Any]:
        """Return bridge + RL statistics for monitoring."""
        stats: Dict[str, Any] = {
            "ingestion_count": self._ingestion_count,
            "history_length": len(self._history),
        }
        if self.rl is not None:
            stats["rl"] = self.rl.get_statistics()
        else:
            stats["rl"] = None
        return stats

    # ------------------------------------------------------------------
    # Persistence: save / load RL state across restarts
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """
        Persist the RL optimizer state and bridge counters to *path*.

        Creates parent directories automatically.  Uses ``torch.save`` for
        network weights (when PyTorch is available) and pickle for the rest.

        Args:
            path: File path (e.g. ``"data/rl_bridge.pkl"``).
        """
        if self.rl is None:
            logger.warning("save() called but RL optimizer is None – nothing saved")
            return
        try:
            dest = Path(path)
            dest.parent.mkdir(parents=True, exist_ok=True)

            checkpoint: Dict[str, Any] = {
                "ingestion_count": self._ingestion_count,
                "history_length": len(self._history),
                "rl_algorithm": self.rl.algorithm,
                "rl_total_updates": self.rl.total_updates,
                "rl_epsilon": self.rl.epsilon,
                "rl_episode_rewards": list(self.rl.episode_rewards),
            }

            if TORCH_AVAILABLE:
                import torch
                if self.rl.algorithm == "dqn":
                    checkpoint["q_network_state"]        = self.rl.q_network.state_dict()
                    checkpoint["target_q_network_state"] = self.rl.target_q_network.state_dict()
                    checkpoint["optimizer_state"]        = self.rl.optimizer.state_dict()
                    checkpoint["replay_buffer"]          = list(self.rl.replay_buffer)
                else:
                    checkpoint["policy_network_state"] = self.rl.policy_network.state_dict()
                    checkpoint["optimizer_state"]      = self.rl.optimizer.state_dict()
                    checkpoint["trajectory_buffer"]    = self.rl.trajectory_buffer
                torch.save(checkpoint, str(dest))
            else:
                with open(dest, "wb") as fh:
                    pickle.dump(checkpoint, fh)

            logger.info("RL bridge saved to %s (updates=%d)", dest,
                        self.rl.total_updates)
        except Exception as exc:
            logger.error("Failed to save RL bridge: %s", exc, exc_info=True)

    def load(self, path: str) -> None:
        """
        Restore RL optimizer state from a previously saved checkpoint.

        Silently returns if the file does not exist (first-run scenario).

        Args:
            path: File path written by :meth:`save`.
        """
        if self.rl is None:
            logger.warning("load() called but RL optimizer is None – nothing loaded")
            return
        src = Path(path)
        if not src.exists():
            logger.info("RL checkpoint not found at %s – starting fresh", src)
            return
        try:
            if TORCH_AVAILABLE:
                import torch
                checkpoint = torch.load(str(src), map_location="cpu")
            else:
                with open(src, "rb") as fh:
                    checkpoint = pickle.load(fh)

            self._ingestion_count = checkpoint.get("ingestion_count", 0)
            self.rl.total_updates = checkpoint.get("rl_total_updates", 0)
            self.rl.epsilon       = checkpoint.get("rl_epsilon", self.rl.epsilon)

            from collections import deque
            rewards = checkpoint.get("rl_episode_rewards", [])
            self.rl.episode_rewards = deque(rewards, maxlen=100)

            if TORCH_AVAILABLE:
                import torch
                if self.rl.algorithm == "dqn":
                    if "q_network_state" in checkpoint:
                        self.rl.q_network.load_state_dict(checkpoint["q_network_state"])
                        self.rl.target_q_network.load_state_dict(
                            checkpoint["target_q_network_state"]
                        )
                        self.rl.optimizer.load_state_dict(checkpoint["optimizer_state"])
                    if "replay_buffer" in checkpoint:
                        self.rl.replay_buffer = deque(
                            checkpoint["replay_buffer"],
                            maxlen=self.rl.replay_buffer.maxlen,
                        )
                else:
                    if "policy_network_state" in checkpoint:
                        self.rl.policy_network.load_state_dict(
                            checkpoint["policy_network_state"]
                        )
                        self.rl.optimizer.load_state_dict(checkpoint["optimizer_state"])
                    if "trajectory_buffer" in checkpoint:
                        self.rl.trajectory_buffer = checkpoint["trajectory_buffer"]

            logger.info("RL bridge loaded from %s (updates=%d, ingestions=%d)",
                        src, self.rl.total_updates, self._ingestion_count)
        except Exception as exc:
            logger.error("Failed to load RL bridge from %s: %s", src, exc,
                         exc_info=True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_rl_state(self, fb: SwarmExecutionFeedback) -> RLState:
        return RLState(
            task_complexity=min(1.0, len(fb.task) / 500.0),
            current_parameters=fb.parameters_used or {
                "temperature": 0.7,
                "max_tokens": 1000,
                "top_p": 0.9,
            },
            system_load=fb.system_load,
            agent_performance_history=fb.agent_performance,
            task_type=fb.task_type,
        )

    def _build_rl_action(self, fb: SwarmExecutionFeedback) -> RLAction:
        """Reconstruct the action that produced this outcome."""
        params = fb.parameters_used or {}
        return RLAction(
            parameter_adjustments={
                "temperature": params.get("temperature", 0.7) - 0.7,
                "max_tokens": params.get("max_tokens", 1000) - 1000,
                "top_p": params.get("top_p", 0.9) - 0.9,
            }
        )

    def _build_rl_reward(self, fb: SwarmExecutionFeedback) -> RLReward:
        latency_penalty = min(
            1.0, fb.latency_ms / self._MAX_LATENCY_MS
        ) * self.latency_penalty_weight

        cost_penalty = min(
            1.0, fb.cost_estimate / self._MAX_COST
        ) * self.cost_penalty_weight

        total = (
            fb.success * 0.4
            + fb.quality_score * 0.3
            - latency_penalty
            - cost_penalty
        )

        return RLReward(
            success=fb.success,
            quality_score=fb.quality_score,
            latency_penalty=latency_penalty,
            cost_penalty=cost_penalty,
            total=total,
        )


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def build_swarm_feedback_bridge(
    rl_optimizer: Optional[ParameterOptimizerRL] = None,
) -> SwarmFeedbackBridge:
    """Factory for creating a bridge with sensible defaults."""
    return SwarmFeedbackBridge(rl_optimizer=rl_optimizer)


def swarm_result_to_feedback(
    run_id: str,
    task: str,
    swarm_result: Dict[str, Any],
    parameters_used: Optional[Dict[str, float]] = None,
    task_type: Optional[str] = None,
) -> SwarmExecutionFeedback:
    """
    Convert the raw dict returned by ``SwarmOrchestrator.execute_swarm()``
    into a ``SwarmExecutionFeedback`` ready for bridge ingestion.

    Args:
        run_id: Unique identifier for this orchestration run.
        task: Original task string.
        swarm_result: Dict returned by SwarmOrchestrator.execute_swarm().
        parameters_used: LLM parameters active during the run.
        task_type: Optional task classification.
    """
    iterations: List[Dict[str, Any]] = swarm_result.get("results", [])
    all_results: List[Any] = [
        r.get("result", "")
        for iteration in iterations
        for r in iteration.get("results", [])
    ]

    # Heuristic success / quality scoring from raw results
    success_keywords = {"success", "complete", "done", "finished"}
    error_keywords = {"error", "fail", "exception"}

    success_count = sum(
        1 for r in all_results
        if isinstance(r, str)
        and any(kw in r.lower() for kw in success_keywords)
    )
    error_count = sum(
        1 for r in all_results
        if isinstance(r, str)
        and any(kw in r.lower() for kw in error_keywords)
    )
    total = len(all_results) or 1

    success = success_count / total
    quality = max(0.0, (success_count - error_count) / total)

    # Agent performance from swarm stats
    swarm_stats: Dict[str, Any] = swarm_result.get("swarm_statistics", {})
    num_agents: int = swarm_stats.get("num_agents", 1)

    return SwarmExecutionFeedback(
        run_id=run_id,
        task=task,
        task_type=task_type,
        success=success,
        quality_score=quality,
        latency_ms=0.0,          # Caller may set after timing
        cost_estimate=0.0,       # Caller may set after billing
        system_load=0.5,
        num_agents=num_agents,
        agent_performance={},
        parameters_used=parameters_used or {},
        raw_result=swarm_result,
    )
