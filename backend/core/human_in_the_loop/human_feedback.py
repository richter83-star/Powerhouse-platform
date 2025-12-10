"""
Human-in-the-Loop Integration

Enables human feedback, interactive training, preference learning,
and human oversight for agent decisions.
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import asyncio
import uuid

from utils.logging import get_logger

logger = get_logger(__name__)


class FeedbackType(str, Enum):
    """Types of human feedback."""
    APPROVAL = "approval"
    REJECTION = "rejection"
    CORRECTION = "correction"
    PREFERENCE = "preference"
    RATING = "rating"
    FLAG = "flag"


@dataclass
class HumanFeedback:
    """Human feedback record."""
    feedback_id: str
    feedback_type: FeedbackType
    agent_name: str
    decision_id: str
    feedback: str  # Human's feedback text
    rating: Optional[float] = None  # 0.0-1.0 or 1-5 scale
    corrections: Optional[Dict[str, Any]] = None
    preferences: Optional[List[str]] = None
    human_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        result["feedback_type"] = self.feedback_type.value
        return result


@dataclass
class FeedbackRequest:
    """Request for human feedback."""
    request_id: str
    agent_name: str
    decision: str
    context: Dict[str, Any]
    question: str
    options: Optional[List[str]] = None
    required: bool = False
    timeout_seconds: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


class HumanInTheLoop:
    """
    Human-in-the-loop integration system.
    
    Features:
    - Request human feedback
    - Collect and process feedback
    - Learn from human corrections
    - Preference learning
    - Active learning (ask when uncertain)
    - Human oversight dashboards
    """
    
    def __init__(
        self,
        enable_active_learning: bool = True,
        uncertainty_threshold: float = 0.7,
        feedback_collector: Optional[Callable] = None
    ):
        """
        Initialize human-in-the-loop system.
        
        Args:
            enable_active_learning: Enable active learning (ask when uncertain)
            uncertainty_threshold: Threshold for requesting feedback
            feedback_collector: Callback for collecting feedback
        """
        self.enable_active_learning = enable_active_learning
        self.uncertainty_threshold = uncertainty_threshold
        self.feedback_collector = feedback_collector
        
        # Feedback storage
        self.pending_requests: Dict[str, FeedbackRequest] = {}
        self.feedback_history: List[HumanFeedback] = []
        
        # Learning from feedback
        self.feedback_patterns: Dict[str, Dict[str, Any]] = {}
        self.correction_history: List[Dict[str, Any]] = []
        
        logger.info("HumanInTheLoop initialized")
    
    def request_feedback(
        self,
        agent_name: str,
        decision: str,
        context: Dict[str, Any],
        question: str,
        options: Optional[List[str]] = None,
        required: bool = False,
        timeout_seconds: Optional[float] = None
    ) -> str:
        """
        Request human feedback.
        
        Args:
            agent_name: Name of the agent
            decision: Decision or output to get feedback on
            context: Execution context
            question: Question to ask human
            options: Optional multiple choice options
            required: Whether feedback is required (blocking)
            timeout_seconds: Timeout for feedback
            
        Returns:
            Request ID
        """
        import uuid
        request_id = str(uuid.uuid4())
        
        request = FeedbackRequest(
            request_id=request_id,
            agent_name=agent_name,
            decision=decision,
            context=self._sanitize_context(context),
            question=question,
            options=options,
            required=required,
            timeout_seconds=timeout_seconds
        )
        
        self.pending_requests[request_id] = request
        
        logger.info(f"Requesting human feedback: {request_id} - {question}")
        
        # If feedback collector is set, use it
        if self.feedback_collector:
            try:
                feedback = self.feedback_collector(request)
                if feedback:
                    self.submit_feedback(request_id, feedback)
            except Exception as e:
                logger.error(f"Feedback collector failed: {e}", exc_info=True)
        
        return request_id
    
    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize context for feedback request."""
        # Remove sensitive information
        sanitized = {}
        allowed_keys = ["task", "run_id", "timestamp"]
        
        for key in allowed_keys:
            if key in context:
                sanitized[key] = context[key]
        
        return sanitized
    
    def should_request_feedback(
        self,
        confidence: float,
        decision_importance: float = 0.5
    ) -> bool:
        """
        Determine if feedback should be requested (active learning).
        
        Args:
            confidence: Confidence in decision (0.0-1.0)
            decision_importance: Importance of decision (0.0-1.0)
            
        Returns:
            Whether to request feedback
        """
        if not self.enable_active_learning:
            return False
        
        # Request feedback if:
        # 1. Confidence is below threshold, OR
        # 2. Decision is important but confidence is moderate
        should_request = (
            confidence < self.uncertainty_threshold or
            (decision_importance > 0.7 and confidence < 0.85)
        )
        
        return should_request
    
    def submit_feedback(
        self,
        request_id: str,
        feedback_data: Dict[str, Any]
    ) -> Optional[HumanFeedback]:
        """
        Submit human feedback.
        
        Args:
            request_id: Request ID
            feedback_data: Feedback data
            
        Returns:
            Feedback record
        """
        if request_id not in self.pending_requests:
            logger.warning(f"Unknown feedback request: {request_id}")
            return None
        
        request = self.pending_requests[request_id]
        
        # Determine feedback type
        feedback_type = FeedbackType.APPROVAL
        if feedback_data.get("approved") is False:
            feedback_type = FeedbackType.REJECTION
        if feedback_data.get("correction"):
            feedback_type = FeedbackType.CORRECTION
        if feedback_data.get("preference"):
            feedback_type = FeedbackType.PREFERENCE
        if feedback_data.get("rating") is not None:
            feedback_type = FeedbackType.RATING
        
        feedback = HumanFeedback(
            feedback_id=str(uuid.uuid4()),
            feedback_type=feedback_type,
            agent_name=request.agent_name,
            decision_id=request_id,
            feedback=feedback_data.get("feedback", ""),
            rating=feedback_data.get("rating"),
            corrections=feedback_data.get("corrections"),
            preferences=feedback_data.get("preferences"),
            human_id=feedback_data.get("human_id")
        )
        
        self.feedback_history.append(feedback)
        del self.pending_requests[request_id]
        
        # Learn from feedback
        self._learn_from_feedback(feedback, request)
        
        logger.info(f"Feedback submitted: {feedback.feedback_id} - {feedback_type.value}")
        
        return feedback
    
    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get all pending feedback requests."""
        return [req.to_dict() for req in self.pending_requests.values()]
    
    def get_feedback_for_agent(
        self,
        agent_name: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get feedback history for an agent."""
        agent_feedback = [
            f for f in self.feedback_history
            if f.agent_name == agent_name
        ][-limit:]
        
        return [f.to_dict() for f in agent_feedback]
    
    def learn_preferences(
        self,
        human_id: str,
        preferences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Learn human preferences.
        
        Args:
            human_id: Human identifier
            preferences: List of preference examples
            
        Returns:
            Learned preference model
        """
        if human_id not in self.feedback_patterns:
            self.feedback_patterns[human_id] = {
                "preferences": [],
                "patterns": {},
                "learned_at": datetime.now()
            }
        
        self.feedback_patterns[human_id]["preferences"].extend(preferences)
        
        # Analyze preference patterns
        patterns = self._analyze_preference_patterns(preferences)
        self.feedback_patterns[human_id]["patterns"].update(patterns)
        
        logger.info(f"Learned preferences for human: {human_id}")
        
        return self.feedback_patterns[human_id]
    
    def predict_human_preference(
        self,
        human_id: str,
        decision: str,
        options: List[str]
    ) -> Dict[str, float]:
        """
        Predict human preference among options.
        
        Args:
            human_id: Human identifier
            decision: Decision context
            options: Options to rank
            
        Returns:
            Dictionary of option -> preference score
        """
        if human_id not in self.feedback_patterns:
            # No prior preferences, uniform distribution
            return {opt: 1.0 / len(options) for opt in options}
        
        patterns = self.feedback_patterns[human_id]["patterns"]
        
        # Simple prediction based on patterns
        # In production, would use ML model
        scores = {}
        for option in options:
            # Check if option matches any preferred patterns
            score = 0.5  # Default
            for pattern_key, pattern_value in patterns.items():
                if pattern_key.lower() in option.lower():
                    score = max(score, pattern_value)
            scores[option] = score
        
        # Normalize
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        
        return scores
    
    def apply_corrections(
        self,
        agent_name: str,
        corrections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply human corrections to agent behavior.
        
        Args:
            agent_name: Agent name
            corrections: Corrections to apply
            
        Returns:
            Applied corrections summary
        """
        correction_record = {
            "agent_name": agent_name,
            "corrections": corrections,
            "applied_at": datetime.now(),
            "applied": True
        }
        
        self.correction_history.append(correction_record)
        
        logger.info(f"Applied corrections to {agent_name}")
        
        return correction_record
    
    def _learn_from_feedback(
        self,
        feedback: HumanFeedback,
        request: FeedbackRequest
    ):
        """Learn from human feedback."""
        # Update feedback patterns
        if feedback.human_id:
            if feedback.human_id not in self.feedback_patterns:
                self.feedback_patterns[feedback.human_id] = {
                    "preferences": [],
                    "patterns": {},
                    "learned_at": datetime.now()
                }
            
            # Extract patterns from feedback
            if feedback.feedback_type == FeedbackType.CORRECTION and feedback.corrections:
                # Learn what was wrong
                for key, value in feedback.corrections.items():
                    pattern_key = f"avoid_{key}"
                    self.feedback_patterns[feedback.human_id]["patterns"][pattern_key] = -0.5
            
            if feedback.rating is not None:
                # Learn quality preferences
                if feedback.rating > 0.7:
                    self.feedback_patterns[feedback.human_id]["patterns"]["prefers_quality"] = 0.8
                elif feedback.rating < 0.4:
                    self.feedback_patterns[feedback.human_id]["patterns"]["prefers_quality"] = 0.2
    
    def _analyze_preference_patterns(
        self,
        preferences: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Analyze patterns in preferences."""
        patterns = {}
        
        # Simple pattern extraction
        # In production, would use more sophisticated analysis
        
        for pref in preferences:
            if "preferred" in pref:
                preferred = pref["preferred"]
                if isinstance(preferred, str):
                    # Extract keywords
                    keywords = preferred.lower().split()
                    for keyword in keywords:
                        if len(keyword) > 3:  # Skip short words
                            patterns[f"prefers_{keyword}"] = patterns.get(
                                f"prefers_{keyword}", 0.0
                            ) + 0.1
        
        # Normalize
        if patterns:
            max_val = max(abs(v) for v in patterns.values())
            if max_val > 0:
                patterns = {k: v / max_val for k, v in patterns.items()}
        
        return patterns
    
    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize context for feedback request."""
        # Remove sensitive information
        sanitized = {}
        allowed_keys = ["task", "run_id", "timestamp"]
        
        for key in allowed_keys:
            if key in context:
                sanitized[key] = context[key]
        
        return sanitized
    
    def _analyze_preference_patterns(
        self,
        preferences: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Analyze patterns in preferences."""
        patterns = {}
        
        # Simple pattern extraction
        # In production, would use more sophisticated analysis
        
        for pref in preferences:
            if "preferred" in pref:
                preferred = pref["preferred"]
                if isinstance(preferred, str):
                    # Extract keywords
                    keywords = preferred.lower().split()
                    for keyword in keywords:
                        if len(keyword) > 3:  # Skip short words
                            patterns[f"prefers_{keyword}"] = patterns.get(
                                f"prefers_{keyword}", 0.0
                            ) + 0.1
        
        # Normalize
        if patterns:
            max_val = max(abs(v) for v in patterns.values())
            if max_val > 0:
                patterns = {k: v / max_val for k, v in patterns.items()}
        
        return patterns
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get human-in-the-loop statistics."""
        total_feedback = len(self.feedback_history)
        
        feedback_by_type = {}
        for feedback in self.feedback_history:
            ftype = feedback.feedback_type.value
            feedback_by_type[ftype] = feedback_by_type.get(ftype, 0) + 1
        
        return {
            "total_feedback_requests": len(self.pending_requests),
            "total_feedback_received": total_feedback,
            "feedback_by_type": feedback_by_type,
            "humans_with_preferences": len(self.feedback_patterns),
            "total_corrections": len(self.correction_history),
            "active_learning_enabled": self.enable_active_learning
        }

