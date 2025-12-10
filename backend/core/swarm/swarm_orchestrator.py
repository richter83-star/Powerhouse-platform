"""
Swarm Orchestrator: Coordinates agent swarm without central control.

Uses stigmergy and emergent behaviors for decentralized coordination.
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
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
        
        while iteration < max_iterations and self.swarm_agents:
            iteration += 1
            
            # Agents decide actions based on environment (stigmergy)
            iteration_results = []
            
            for agent_id, swarm_agent in self.swarm_agents.items():
                # Read environment (traces left by other agents)
                if use_stigmergy:
                    traces = self.stigmergic_memory.read_traces(swarm_agent.current_location)
                    
                    # Agent decides action based on traces
                    action = self._agent_decide_action(swarm_agent, traces, task)
                else:
                    action = "explore"  # Default action
                
                # Execute action
                try:
                    if hasattr(swarm_agent.agent_instance, 'run'):
                        result = swarm_agent.agent_instance.run({
                            "task": task,
                            "action": action,
                            "location": swarm_agent.current_location,
                            "context": swarm_agent.state
                        })
                    else:
                        result = f"Agent {agent_id} executed {action}"
                    
                    # Leave trace in environment
                    if use_stigmergy:
                        trace_value = self._calculate_trace_value(result, action)
                        self.stigmergic_memory.deposit_trace(
                            agent_id=agent_id,
                            location=swarm_agent.current_location,
                            trace_type="pheromone",
                            value=trace_value,
                            metadata={"action": action, "result": result}
                        )
                    
                    # Observe for emergent patterns
                    self.emergent_detector.observe_action(
                        agent_id=agent_id,
                        action=action,
                        location=swarm_agent.current_location,
                        metadata={"result": result}
                    )
                    
                    iteration_results.append({
                        "agent_id": agent_id,
                        "action": action,
                        "result": result,
                        "location": swarm_agent.current_location
                    })
                    
                    swarm_agent.last_action = action
                    
                except Exception as e:
                    self.logger.error(f"Agent {agent_id} execution failed: {e}")
            
            results.append({
                "iteration": iteration,
                "results": iteration_results
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

