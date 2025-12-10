"""
Stigmergy: Indirect coordination through shared environment.

Agents communicate by modifying the environment, which other agents observe.
"""

import numpy as np
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StigmergicTrace:
    """
    Represents a trace left by an agent in the environment.
    """
    agent_id: str
    trace_type: str  # e.g., "pheromone", "marker", "information"
    location: str  # Location identifier
    value: float  # Trace strength/value
    timestamp: datetime = field(default_factory=datetime.now)
    decay_rate: float = 0.1  # How fast trace fades
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_strength(self, current_time: datetime) -> float:
        """Get current trace strength considering decay."""
        age_seconds = (current_time - self.timestamp).total_seconds()
        decay_factor = np.exp(-self.decay_rate * age_seconds)
        return self.value * decay_factor
    
    def is_expired(self, current_time: datetime, threshold: float = 0.01) -> bool:
        """Check if trace has decayed below threshold."""
        return self.get_strength(current_time) < threshold


class StigmergicMemory:
    """
    Shared environment for stigmergic communication.
    
    Agents leave traces (pheromones, markers, information) that other
    agents can observe and follow.
    """
    
    def __init__(self, decay_rate: float = 0.1):
        """
        Initialize stigmergic memory.
        
        Args:
            decay_rate: Default decay rate for traces
        """
        self.traces: List[StigmergicTrace] = []
        self.location_traces: Dict[str, List[StigmergicTrace]] = defaultdict(list)
        self.decay_rate = decay_rate
        self.logger = get_logger(__name__)
    
    def deposit_trace(
        self,
        agent_id: str,
        location: str,
        trace_type: str,
        value: float = 1.0,
        decay_rate: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StigmergicTrace:
        """
        Deposit a trace at a location.
        
        Args:
            agent_id: ID of agent leaving trace
            location: Location identifier
            trace_type: Type of trace
            value: Trace strength/value
            decay_rate: Optional decay rate (uses default if None)
            metadata: Optional metadata
            
        Returns:
            Created trace
        """
        trace = StigmergicTrace(
            agent_id=agent_id,
            trace_type=trace_type,
            location=location,
            value=value,
            decay_rate=decay_rate or self.decay_rate,
            metadata=metadata or {}
        )
        
        self.traces.append(trace)
        self.location_traces[location].append(trace)
        
        return trace
    
    def read_traces(
        self,
        location: str,
        trace_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        min_strength: float = 0.01
    ) -> List[StigmergicTrace]:
        """
        Read traces at a location.
        
        Args:
            location: Location to read from
            trace_type: Optional filter by trace type
            agent_id: Optional filter by agent ID
            min_strength: Minimum trace strength
            
        Returns:
            List of active traces
        """
        current_time = datetime.now()
        
        # Clean expired traces
        self._cleanup_expired(current_time)
        
        # Get traces at location
        traces = self.location_traces.get(location, [])
        
        # Filter
        active_traces = []
        for trace in traces:
            strength = trace.get_strength(current_time)
            
            if strength < min_strength:
                continue
            
            if trace_type and trace.trace_type != trace_type:
                continue
            
            if agent_id and trace.agent_id == agent_id:
                continue  # Skip own traces
            
            active_traces.append(trace)
        
        return active_traces
    
    def get_trace_strength(
        self,
        location: str,
        trace_type: Optional[str] = None
    ) -> float:
        """
        Get total trace strength at location.
        
        Args:
            location: Location to check
            trace_type: Optional filter by trace type
            
        Returns:
            Total strength (sum of all active traces)
        """
        traces = self.read_traces(location, trace_type)
        current_time = datetime.now()
        return sum(trace.get_strength(current_time) for trace in traces)
    
    def follow_trail(
        self,
        current_location: str,
        trace_type: str = "pheromone",
        neighbor_locations: List[str] = None
    ) -> Optional[str]:
        """
        Follow the strongest trail from current location.
        
        Args:
            current_location: Current location
            trace_type: Type of trail to follow
            neighbor_locations: Optional list of neighboring locations
            
        Returns:
            Location with strongest trail, or None
        """
        if neighbor_locations is None:
            # Default: all locations with traces
            neighbor_locations = list(self.location_traces.keys())
        
        best_location = None
        best_strength = 0.0
        
        for location in neighbor_locations:
            if location == current_location:
                continue
            
            strength = self.get_trace_strength(location, trace_type)
            if strength > best_strength:
                best_strength = strength
                best_location = location
        
        return best_location if best_strength > 0 else None
    
    def _cleanup_expired(self, current_time: datetime) -> None:
        """Remove expired traces."""
        expired_indices = []
        
        for i, trace in enumerate(self.traces):
            if trace.is_expired(current_time):
                expired_indices.append(i)
        
        # Remove in reverse order to maintain indices
        for i in reversed(expired_indices):
            trace = self.traces.pop(i)
            if trace.location in self.location_traces:
                self.location_traces[trace.location].remove(trace)
                if not self.location_traces[trace.location]:
                    del self.location_traces[trace.location]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about traces."""
        current_time = datetime.now()
        self._cleanup_expired(current_time)
        
        trace_types = defaultdict(int)
        agent_counts = defaultdict(int)
        
        for trace in self.traces:
            trace_types[trace.trace_type] += 1
            agent_counts[trace.agent_id] += 1
        
        return {
            "total_traces": len(self.traces),
            "locations": len(self.location_traces),
            "trace_types": dict(trace_types),
            "agents_with_traces": len(agent_counts),
            "total_strength": sum(
                trace.get_strength(current_time)
                for trace in self.traces
            )
        }

