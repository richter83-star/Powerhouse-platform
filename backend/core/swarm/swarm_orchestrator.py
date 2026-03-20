"""
Swarm Orchestrator: Coordinates agent swarm without central control.

Uses stigmergy and emergent behaviors for decentralized coordination.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

from core.swarm.stigmergy import StigmergicMemory
from core.swarm.emergent_detector import EmergentBehaviorDetector
from core.orchestrator import Orchestrator
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SwarmAgent:
    """Represents an agent in the swarm."""
    agent_id: str
    agent_instance: Any
    current_location: str = "default"
    state: Dict[str, Any] = field(default_factory=dict)
    last_action: Optional[str] = None


class SwarmOrchestrator:
    """
    Coordinates agent swarm using stigmergic communication.
    
    Agents interact through shared environment (stigmergy) rather than
    direct communication, enabling emergent behaviors.
    """
    
    def __init__(self, base_orchestrator: Optional[Orchestrator] = None):
        """
        Initialize swarm orchestrator.
        
        Args:
            base_orchestrator: Optional base orchestrator for agent management
        """
        self.base_orchestrator = base_orchestrator
        self.stigmergic_memory = StigmergicMemory()
        self.emergent_detector = EmergentBehaviorDetector()
        self.swarm_agents: Dict[str, SwarmAgent] = {}
        self.task_queue: List[Dict[str, Any]] = []
        self.logger = get_logger(__name__)
    
    def register_agent(self, agent_id: str, agent_instance: Any, initial_location: str = "default") -> None:
        """
        Register an agent in the swarm.
        
        Args:
            agent_id: Unique agent identifier
            agent_instance: Agent instance
            initial_location: Initial location
        """
        swarm_agent = SwarmAgent(
            agent_id=agent_id,
            agent_instance=agent_instance,
            current_location=initial_location
        )
        self.swarm_agents[agent_id] = swarm_agent
        self.logger.info(f"Registered swarm agent: {agent_id}")
    
    def execute_swarm(
        self,
        task: str,
        max_iterations: int = 10,
        use_stigmergy: bool = True
    ) -> Dict[str, Any]:
        """
        Execute task using swarm intelligence.
        
        Args:
            task: Task description
            max_iterations: Maximum swarm iterations
            use_stigmergy: Whether to use stigmergic communication
            
        Returns:
            Execution results
        """
        self.logger.info(f"Starting swarm execution: {task}")
        
        results = []
        iteration = 0
        
        # Use a thread pool so agents within each iteration run concurrently.
        # We snapshot the stigmergic environment BEFORE the iteration so every
        # agent sees the same traces (no ordering bias); traces are deposited
        # only AFTER all agents in the iteration have completed.
        _max_workers = max(1, min(len(self.swarm_agents), 10))

        while iteration < max_iterations and self.swarm_agents:
            iteration += 1

            # --- snapshot environment for this iteration ---
            env_snapshot: Dict[str, Any] = {}
            for swarm_agent in self.swarm_agents.values():
                if use_stigmergy:
                    env_snapshot[swarm_agent.agent_id] = self.stigmergic_memory.read_traces(
                        swarm_agent.current_location
                    )

            # --- parallel execution helper ---
            def _run_single(agent_id: str, swarm_agent: "SwarmAgent") -> Tuple[str, str, Any]:
                traces = env_snapshot.get(agent_id, [])
                action = (
                    self._agent_decide_action(swarm_agent, traces, task)
                    if use_stigmergy else "explore"
                )
                try:
                    if hasattr(swarm_agent.agent_instance, "run"):
                        result = swarm_agent.agent_instance.run({
                            "task": task,
                            "action": action,
                            "location": swarm_agent.current_location,
                            "context": swarm_agent.state,
                        })
                    else:
                        result = f"Agent {agent_id} executed {action}"
                except Exception as exc:
                    self.logger.error("Swarm agent %s failed: %s", agent_id, exc)
                    result = f"error: {exc}"
                return agent_id, action, result

            # --- fan-out all agents concurrently ---
            iteration_results = []
            with ThreadPoolExecutor(max_workers=_max_workers) as _pool:
                futures = {
                    _pool.submit(_run_single, aid, sa): (aid, sa)
                    for aid, sa in self.swarm_agents.items()
                }
                for future in as_completed(futures):
                    try:
                        agent_id, action, result = future.result()
                    except Exception as exc:
                        agent_id, sa = futures[future]
                        self.logger.error("Swarm future for %s raised: %s", agent_id, exc)
                        continue

                    swarm_agent = self.swarm_agents[agent_id]
                    swarm_agent.last_action = action
                    iteration_results.append({
                        "agent_id": agent_id,
                        "action": action,
                        "result": result,
                        "location": swarm_agent.current_location,
                    })

            # --- deposit traces AFTER all agents finished (no ordering bias) ---
            if use_stigmergy:
                for entry in iteration_results:
                    aid = entry["agent_id"]
                    swarm_agent = self.swarm_agents[aid]
                    trace_value = self._calculate_trace_value(entry["result"], entry["action"])
                    self.stigmergic_memory.deposit_trace(
                        agent_id=aid,
                        location=swarm_agent.current_location,
                        trace_type="pheromone",
                        value=trace_value,
                        metadata={"action": entry["action"], "result": entry["result"]},
                    )

            # --- emergent pattern observation ---
            for entry in iteration_results:
                swarm_agent = self.swarm_agents[entry["agent_id"]]
                self.emergent_detector.observe_action(
                    agent_id=entry["agent_id"],
                    action=entry["action"],
                    location=swarm_agent.current_location,
                    metadata={"result": entry["result"]},
                )

            results.append({
                "iteration": iteration,
                "results": iteration_results,
            })
            
            # Check for convergence (emergent consensus)
            if self._check_convergence():
                self.logger.info(f"Swarm converged at iteration {iteration}")
                break
        
        # Get emergent patterns
        emergent_patterns = self.emergent_detector.get_active_patterns()
        
        return {
            "task": task,
            "iterations": iteration,
            "results": results,
            "emergent_patterns": [
                {
                    "type": p.pattern_type,
                    "description": p.description,
                    "strength": p.strength
                }
                for p in emergent_patterns
            ],
            "swarm_statistics": {
                "num_agents": len(self.swarm_agents),
                "stigmergy_stats": self.stigmergic_memory.get_statistics(),
                "pattern_stats": self.emergent_detector.get_statistics()
            }
        }
    
    def _agent_decide_action(
        self,
        swarm_agent: SwarmAgent,
        traces: List,
        task: str
    ) -> str:
        """
        Agent decides action based on environment traces.
        
        Args:
            swarm_agent: Agent making decision
            traces: Traces in current location
            task: Current task
            
        Returns:
            Action to take
        """
        # Simple decision logic: follow strong trails or explore
        if traces:
            # Calculate weighted action preference from traces
            action_preferences = {}
            total_strength = 0.0
            
            for trace in traces:
                action = trace.metadata.get("action", "unknown")
                strength = trace.value
                
                if action not in action_preferences:
                    action_preferences[action] = 0.0
                action_preferences[action] += strength
                total_strength += strength
            
            if total_strength > 0:
                # Normalize
                for action in action_preferences:
                    action_preferences[action] /= total_strength
                
                # Choose action with highest preference
                best_action = max(action_preferences.items(), key=lambda x: x[1])[0]
                return best_action
        
        # Default: explore
        return "explore"
    
    def _calculate_trace_value(self, result: Any, action: str) -> float:
        """
        Calculate trace value based on result quality.
        
        Args:
            result: Action result
            action: Action taken
            
        Returns:
            Trace value (0.0-1.0)
        """
        # Simplified: positive results leave stronger traces
        if isinstance(result, str):
            # Check for success indicators
            success_keywords = ["success", "complete", "done", "finished"]
            if any(kw in result.lower() for kw in success_keywords):
                return 1.0
            elif "error" in result.lower() or "fail" in result.lower():
                return 0.1
            else:
                return 0.5
        
        return 0.5  # Default moderate value
    
    def _check_convergence(self) -> bool:
        """
        Check if swarm has converged (emergent consensus).
        
        Returns:
            True if converged
        """
        # Check for consensus patterns
        patterns = self.emergent_detector.get_active_patterns(min_strength=0.7)
        consensus_patterns = [p for p in patterns if p.pattern_type == "consensus"]
        
        return len(consensus_patterns) > 0

