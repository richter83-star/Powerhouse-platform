"""
Emergent Behavior Detector: Identifies patterns emerging from agent interactions.

Detects emergent behaviors that arise from local agent rules without central control.
"""

import numpy as np
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EmergentPattern:
    """
    Represents an emergent pattern detected in agent behavior.
    """
    pattern_type: str
    description: str
    agents_involved: Set[str]
    frequency: float  # How often pattern occurs
    strength: float  # Pattern strength/coherence
    first_observed: datetime
    last_observed: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmergentBehaviorDetector:
    """
    Detects emergent behaviors and patterns from agent interactions.
    
    Monitors agent actions and identifies:
    - Swarm behaviors (flocking, clustering)
    - Collective decisions (consensus patterns)
    - Self-organization (spatial patterns)
    - Emergent strategies (cooperative behaviors)
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize emergent behavior detector.
        
        Args:
            window_size: Number of recent observations to analyze
        """
        self.window_size = window_size
        self.action_history: deque = deque(maxlen=window_size)
        self.patterns: Dict[str, EmergentPattern] = {}
        self.logger = get_logger(__name__)
    
    def observe_action(
        self,
        agent_id: str,
        action: str,
        location: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Observe an agent action.
        
        Args:
            agent_id: ID of agent
            action: Action taken
            location: Optional location
            metadata: Optional action metadata
        """
        observation = {
            "agent_id": agent_id,
            "action": action,
            "location": location,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        
        self.action_history.append(observation)
        
        # Trigger pattern detection
        self._detect_patterns()
    
    def _detect_patterns(self) -> None:
        """Detect patterns in recent actions."""
        if len(self.action_history) < 10:
            return  # Need enough data
        
        # Detect clustering (agents converging on same location)
        self._detect_clustering()
        
        # Detect synchronization (agents doing same action)
        self._detect_synchronization()
        
        # Detect consensus (agents agreeing)
        self._detect_consensus()
        
        # Detect division of labor (agents specializing)
        self._detect_division_of_labor()
    
    def _detect_clustering(self) -> None:
        """Detect spatial clustering of agents."""
        # Group by location
        location_groups = defaultdict(set)
        for obs in self.action_history:
            if obs["location"]:
                location_groups[obs["location"]].add(obs["agent_id"])
        
        # Find locations with multiple agents
        for location, agents in location_groups.items():
            if len(agents) >= 3:  # Threshold for clustering
                pattern_id = f"clustering_{location}"
                
                if pattern_id not in self.patterns:
                    pattern = EmergentPattern(
                        pattern_type="clustering",
                        description=f"Agents clustering at {location}",
                        agents_involved=agents,
                        frequency=1.0,
                        strength=len(agents) / 10.0,  # Normalized
                        first_observed=datetime.now()
                    )
                    self.patterns[pattern_id] = pattern
                else:
                    pattern = self.patterns[pattern_id]
                    pattern.agents_involved.update(agents)
                    pattern.last_observed = datetime.now()
                    pattern.strength = min(1.0, len(agents) / 10.0)
    
    def _detect_synchronization(self) -> None:
        """Detect synchronized actions."""
        # Group by action and time window
        action_windows = defaultdict(lambda: defaultdict(set))
        
        for obs in self.action_history:
            # Round to nearest second for windowing
            time_window = obs["timestamp"].replace(microsecond=0)
            action_windows[obs["action"]][time_window].add(obs["agent_id"])
        
        # Find actions with multiple agents in same time window
        for action, windows in action_windows.items():
            for time_window, agents in windows.items():
                if len(agents) >= 2:  # At least 2 agents synchronized
                    pattern_id = f"sync_{action}_{time_window}"
                    
                    if pattern_id not in self.patterns:
                        pattern = EmergentPattern(
                            pattern_type="synchronization",
                            description=f"Agents synchronized on action: {action}",
                            agents_involved=agents,
                            frequency=1.0,
                            strength=len(agents) / 5.0,
                            first_observed=datetime.now()
                        )
                        self.patterns[pattern_id] = pattern
    
    def _detect_consensus(self) -> None:
        """Detect consensus patterns (agents agreeing on decisions)."""
        # Look for decision-like actions with high agreement
        decision_actions = defaultdict(lambda: {"yes": set(), "no": set()})
        
        for obs in self.action_history:
            action = obs["action"].lower()
            if "agree" in action or "approve" in action:
                decision_actions[obs.get("metadata", {}).get("decision_id", "unknown")]["yes"].add(obs["agent_id"])
            elif "disagree" in action or "reject" in action:
                decision_actions[obs.get("metadata", {}).get("decision_id", "unknown")]["no"].add(obs["agent_id"])
        
        # Find high-consensus decisions
        for decision_id, votes in decision_actions.items():
            total_votes = len(votes["yes"]) + len(votes["no"])
            if total_votes >= 3:
                majority_size = max(len(votes["yes"]), len(votes["no"]))
                consensus_strength = majority_size / total_votes
                
                if consensus_strength >= 0.7:  # 70% agreement
                    pattern_id = f"consensus_{decision_id}"
                    pattern = EmergentPattern(
                        pattern_type="consensus",
                        description=f"Consensus reached on decision {decision_id}",
                        agents_involved=votes["yes"] | votes["no"],
                        frequency=consensus_strength,
                        strength=consensus_strength,
                        first_observed=datetime.now()
                    )
                    self.patterns[pattern_id] = pattern
    
    def _detect_division_of_labor(self) -> None:
        """Detect division of labor (agents specializing in tasks)."""
        # Track which agents do which actions
        agent_specializations = defaultdict(lambda: defaultdict(int))
        
        for obs in self.action_history:
            agent_specializations[obs["agent_id"]][obs["action"]] += 1
        
        # Find agents that specialize (do one action much more than others)
        for agent_id, actions in agent_specializations.items():
            total_actions = sum(actions.values())
            if total_actions < 5:
                continue  # Need enough data
            
            max_action = max(actions.items(), key=lambda x: x[1])
            specialization_ratio = max_action[1] / total_actions
            
            if specialization_ratio >= 0.7:  # 70% of actions are one type
                pattern_id = f"specialization_{agent_id}_{max_action[0]}"
                
                if pattern_id not in self.patterns:
                    pattern = EmergentPattern(
                        pattern_type="division_of_labor",
                        description=f"Agent {agent_id} specializes in {max_action[0]}",
                        agents_involved={agent_id},
                        frequency=specialization_ratio,
                        strength=specialization_ratio,
                        first_observed=datetime.now()
                    )
                    self.patterns[pattern_id] = pattern
    
    def get_active_patterns(self, min_strength: float = 0.3) -> List[EmergentPattern]:
        """
        Get currently active emergent patterns.
        
        Args:
            min_strength: Minimum pattern strength
            
        Returns:
            List of active patterns
        """
        # Clean old patterns (not observed recently)
        cutoff_time = datetime.now() - timedelta(minutes=5)
        active_patterns = [
            pattern for pattern in self.patterns.values()
            if pattern.last_observed > cutoff_time and pattern.strength >= min_strength
        ]
        
        return sorted(active_patterns, key=lambda p: p.strength, reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected patterns."""
        active_patterns = self.get_active_patterns()
        
        pattern_types = defaultdict(int)
        for pattern in active_patterns:
            pattern_types[pattern.pattern_type] += 1
        
        return {
            "total_patterns": len(self.patterns),
            "active_patterns": len(active_patterns),
            "pattern_types": dict(pattern_types),
            "total_agents_involved": len(
                set().union(*[p.agents_involved for p in active_patterns])
            ) if active_patterns else 0
        }

