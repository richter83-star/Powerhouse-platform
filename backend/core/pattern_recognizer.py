
"""
Pattern Recognition Module

Identifies recurring patterns in agent behavior and system performance:
- Recurring tasks and workflows
- User behavior patterns
- Seasonal trends (daily, weekly, monthly)
- Anomaly detection
- Correlation discovery
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, Counter
import numpy as np
import json

from utils.logging import get_logger

logger = get_logger(__name__)


class PatternType(str, Enum):
    """Types of patterns that can be detected."""
    RECURRING_TASK = "recurring_task"
    PERIODIC_SPIKE = "periodic_spike"
    SEASONAL_TREND = "seasonal_trend"
    USER_BEHAVIOR = "user_behavior"
    WORKFLOW_SEQUENCE = "workflow_sequence"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"


@dataclass
class Pattern:
    """Represents a detected pattern."""
    pattern_id: str
    pattern_type: PatternType
    description: str
    confidence: float
    frequency: str  # e.g., "daily", "weekly", "hourly"
    last_occurrence: datetime
    occurrences: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "confidence": self.confidence,
            "frequency": self.frequency,
            "last_occurrence": self.last_occurrence.isoformat(),
            "occurrences": self.occurrences,
            "metadata": self.metadata,
            "active": self.active
        }


@dataclass
class RecurringTask:
    """A recurring task pattern."""
    task_name: str
    schedule: str  # cron-like or human readable
    average_duration: float
    success_rate: float
    last_run: datetime
    next_expected: datetime
    resource_requirements: Dict[str, float]


class PatternRecognizer:
    """
    Main pattern recognition engine.
    
    Analyzes historical data to identify:
    - Recurring patterns
    - Seasonal trends
    - User behavior
    - Anomalies
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.patterns: Dict[str, Pattern] = {}  # pattern_id -> Pattern
        self.event_history: List[Dict[str, Any]] = []
        self.max_history_size = self.config.get("max_history_size", 10000)
        self.min_confidence_threshold = self.config.get("min_confidence_threshold", 0.7)
        
        # Pattern detection settings
        self.hourly_buckets = 24
        self.daily_buckets = 7
        self.weekly_buckets = 4
        
        logger.info(f"PatternRecognizer initialized with config: {self.config}")
    
    def add_event(
        self,
        event_type: str,
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add an event to the history for pattern analysis."""
        event = {
            "event_type": event_type,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        
        self.event_history.append(event)
        
        # Keep history size bounded
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
        
        logger.debug(f"Added event: {event_type} at {timestamp}")
    
    def analyze_patterns(self) -> List[Pattern]:
        """
        Analyze event history and detect patterns.
        
        Returns:
            List of detected patterns
        """
        if len(self.event_history) < 10:
            logger.warning("Insufficient event history for pattern analysis")
            return []
        
        patterns = []
        
        # Detect different types of patterns
        patterns.extend(self._detect_recurring_tasks())
        patterns.extend(self._detect_periodic_spikes())
        patterns.extend(self._detect_seasonal_trends())
        patterns.extend(self._detect_workflow_sequences())
        
        # Update internal pattern store
        for pattern in patterns:
            self.patterns[pattern.pattern_id] = pattern
        
        logger.info(f"Detected {len(patterns)} patterns")
        return patterns
    
    def _detect_recurring_tasks(self) -> List[Pattern]:
        """Detect tasks that occur at regular intervals."""
        patterns = []
        
        # Group events by type
        event_types = defaultdict(list)
        for event in self.event_history:
            event_types[event["event_type"]].append(event["timestamp"])
        
        # Analyze each event type for regularity
        for event_type, timestamps in event_types.items():
            if len(timestamps) < 3:
                continue
            
            # Calculate intervals between occurrences
            timestamps = sorted(timestamps)
            intervals = [
                (timestamps[i+1] - timestamps[i]).total_seconds()
                for i in range(len(timestamps) - 1)
            ]
            
            if not intervals:
                continue
            
            # Check for regularity
            mean_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            cv = std_interval / mean_interval if mean_interval > 0 else float('inf')
            
            # If coefficient of variation is low, it's a recurring pattern
            if cv < 0.3 and len(timestamps) >= 5:
                # Determine frequency
                if mean_interval < 3600:  # Less than 1 hour
                    frequency = f"Every {int(mean_interval / 60)} minutes"
                elif mean_interval < 86400:  # Less than 1 day
                    frequency = f"Every {int(mean_interval / 3600)} hours"
                else:
                    frequency = f"Every {int(mean_interval / 86400)} days"
                
                confidence = max(0.5, 1.0 - cv)
                
                pattern = Pattern(
                    pattern_id=f"recurring_{event_type}",
                    pattern_type=PatternType.RECURRING_TASK,
                    description=f"Recurring task: {event_type}",
                    confidence=confidence,
                    frequency=frequency,
                    last_occurrence=timestamps[-1],
                    occurrences=len(timestamps),
                    metadata={
                        "mean_interval_seconds": mean_interval,
                        "std_interval_seconds": std_interval,
                        "coefficient_of_variation": cv
                    }
                )
                patterns.append(pattern)
                
                logger.info(f"Detected recurring task: {event_type} with frequency {frequency}")
        
        return patterns
    
    def _detect_periodic_spikes(self) -> List[Pattern]:
        """Detect periodic spikes in activity."""
        patterns = []
        
        if len(self.event_history) < 50:
            return patterns
        
        # Group events into hourly buckets
        hourly_counts = [0] * self.hourly_buckets
        for event in self.event_history:
            hour = event["timestamp"].hour
            hourly_counts[hour] += 1
        
        # Find hours with significantly higher activity
        mean_count = np.mean(hourly_counts)
        std_count = np.std(hourly_counts)
        threshold = mean_count + 2 * std_count
        
        spike_hours = [i for i, count in enumerate(hourly_counts) if count > threshold]
        
        if spike_hours:
            pattern = Pattern(
                pattern_id="periodic_spike_hourly",
                pattern_type=PatternType.PERIODIC_SPIKE,
                description=f"Activity spikes at hours: {spike_hours}",
                confidence=0.8,
                frequency="daily",
                last_occurrence=datetime.now(),
                occurrences=len([h for h in spike_hours if hourly_counts[h] > threshold]),
                metadata={
                    "spike_hours": spike_hours,
                    "mean_activity": mean_count,
                    "threshold": threshold,
                    "hourly_counts": hourly_counts
                }
            )
            patterns.append(pattern)
            logger.info(f"Detected periodic spike pattern at hours: {spike_hours}")
        
        return patterns
    
    def _detect_seasonal_trends(self) -> List[Pattern]:
        """Detect seasonal trends (daily, weekly, monthly)."""
        patterns = []
        
        if len(self.event_history) < 100:
            return patterns
        
        # Group events by day of week
        daily_counts = [0] * self.daily_buckets
        for event in self.event_history:
            day_of_week = event["timestamp"].weekday()
            daily_counts[day_of_week] += 1
        
        # Check for significant variation across days
        if max(daily_counts) > 0:
            cv = np.std(daily_counts) / np.mean(daily_counts)
            
            if cv > 0.3:  # Significant variation
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                busiest_day = days[daily_counts.index(max(daily_counts))]
                quietest_day = days[daily_counts.index(min(daily_counts))]
                
                pattern = Pattern(
                    pattern_id="seasonal_trend_weekly",
                    pattern_type=PatternType.SEASONAL_TREND,
                    description=f"Weekly trend: busiest on {busiest_day}, quietest on {quietest_day}",
                    confidence=min(0.95, cv),
                    frequency="weekly",
                    last_occurrence=datetime.now(),
                    occurrences=len(self.event_history),
                    metadata={
                        "daily_counts": {days[i]: daily_counts[i] for i in range(7)},
                        "busiest_day": busiest_day,
                        "quietest_day": quietest_day,
                        "coefficient_of_variation": cv
                    }
                )
                patterns.append(pattern)
                logger.info(f"Detected weekly seasonal trend: busiest on {busiest_day}")
        
        return patterns
    
    def _detect_workflow_sequences(self) -> List[Pattern]:
        """Detect common sequences of events (workflows)."""
        patterns = []
        
        if len(self.event_history) < 20:
            return patterns
        
        # Find sequences of events that occur within 5 minutes
        sequences = []
        current_sequence = []
        last_timestamp = None
        
        for event in self.event_history:
            ts = event["timestamp"]
            
            if last_timestamp is None or (ts - last_timestamp).total_seconds() < 300:
                current_sequence.append(event["event_type"])
            else:
                if len(current_sequence) >= 2:
                    sequences.append(tuple(current_sequence))
                current_sequence = [event["event_type"]]
            
            last_timestamp = ts
        
        # Add last sequence
        if len(current_sequence) >= 2:
            sequences.append(tuple(current_sequence))
        
        # Count sequence occurrences
        sequence_counts = Counter(sequences)
        
        # Find common sequences
        for sequence, count in sequence_counts.items():
            if count >= 3:  # At least 3 occurrences
                confidence = min(0.95, count / len(sequences))
                
                pattern = Pattern(
                    pattern_id=f"workflow_{hash(sequence)}",
                    pattern_type=PatternType.WORKFLOW_SEQUENCE,
                    description=f"Common workflow: {' -> '.join(sequence)}",
                    confidence=confidence,
                    frequency=f"Occurred {count} times",
                    last_occurrence=datetime.now(),
                    occurrences=count,
                    metadata={
                        "sequence": list(sequence),
                        "sequence_length": len(sequence)
                    }
                )
                patterns.append(pattern)
                logger.info(f"Detected workflow sequence: {' -> '.join(sequence)}")
        
        return patterns
    
    def get_pattern(self, pattern_id: str) -> Optional[Pattern]:
        """Get a specific pattern by ID."""
        return self.patterns.get(pattern_id)
    
    def get_patterns_by_type(self, pattern_type: PatternType) -> List[Pattern]:
        """Get all patterns of a specific type."""
        return [p for p in self.patterns.values() if p.pattern_type == pattern_type]
    
    def get_all_patterns(self, active_only: bool = True) -> List[Pattern]:
        """Get all detected patterns."""
        patterns = list(self.patterns.values())
        if active_only:
            patterns = [p for p in patterns if p.active]
        return patterns
    
    def predict_next_occurrence(self, pattern_id: str) -> Optional[datetime]:
        """Predict when a pattern will next occur."""
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            return None
        
        if pattern.pattern_type == PatternType.RECURRING_TASK:
            mean_interval = pattern.metadata.get("mean_interval_seconds", 0)
            if mean_interval > 0:
                return pattern.last_occurrence + timedelta(seconds=mean_interval)
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Export pattern recognizer state."""
        return {
            "num_patterns": len(self.patterns),
            "num_events": len(self.event_history),
            "patterns": [p.to_dict() for p in self.patterns.values()],
            "config": self.config
        }
