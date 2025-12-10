"""
Tests for Human-in-the-Loop System (Phase 4)

Tests feedback collection, active learning, and preference learning.
"""

import pytest
from datetime import datetime

from core.human_in_the_loop import (
    HumanInTheLoop,
    HumanFeedback,
    FeedbackRequest,
    FeedbackType
)


@pytest.mark.unit
class TestHumanInTheLoop:
    """Test human-in-the-loop system."""
    
    def test_initialization(self):
        """Test system initialization."""
        human_loop = HumanInTheLoop(
            enable_active_learning=True,
            uncertainty_threshold=0.7
        )
        
        assert human_loop is not None
        assert human_loop.enable_active_learning is True
        assert human_loop.uncertainty_threshold == 0.7
    
    def test_feedback_request_creation(self):
        """Test feedback request creation."""
        human_loop = HumanInTheLoop()
        
        request_id = human_loop.request_feedback(
            agent_name="ReactAgent",
            decision="Use tool X",
            context={"task": "..."},
            question="Is this approach correct?",
            options=["Yes", "No", "Maybe"],
            required=False
        )
        
        assert request_id is not None
        assert request_id in human_loop.pending_requests
    
    def test_feedback_submission(self):
        """Test feedback submission."""
        human_loop = HumanInTheLoop()
        
        # Request feedback
        request_id = human_loop.request_feedback(
            agent_name="ReactAgent",
            decision="Test decision",
            context={},
            question="Is this correct?",
            options=["Yes", "No"]
        )
        
        # Submit feedback
        feedback = human_loop.submit_feedback(request_id, {
            "approved": True,
            "rating": 0.9,
            "feedback": "Good approach",
            "human_id": "user123"
        })
        
        assert feedback is not None
        assert feedback.feedback_type in [FeedbackType.APPROVAL, FeedbackType.RATING]
        assert request_id not in human_loop.pending_requests
    
    def test_feedback_type_handling(self):
        """Test feedback type handling."""
        human_loop = HumanInTheLoop()
        
        request_id = human_loop.request_feedback(
            agent_name="ReactAgent",
            decision="Test",
            context={},
            question="Test?"
        )
        
        # Test different feedback types
        feedback_types = [
            {"approved": True},  # Approval
            {"approved": False},  # Rejection
            {"correction": {"field": "value"}},  # Correction
            {"rating": 0.8},  # Rating
            {"preference": ["option1"]}  # Preference
        ]
        
        for feedback_data in feedback_types:
            request_id = human_loop.request_feedback(
                agent_name="ReactAgent",
                decision="Test",
                context={},
                question="Test?"
            )
            feedback = human_loop.submit_feedback(request_id, feedback_data)
            assert feedback is not None
    
    def test_active_learning_logic(self):
        """Test should_request_feedback() logic."""
        human_loop = HumanInTheLoop(
            enable_active_learning=True,
            uncertainty_threshold=0.7
        )
        
        # Low confidence should trigger feedback
        should_request = human_loop.should_request_feedback(
            confidence=0.5,
            decision_importance=0.8
        )
        assert should_request is True
        
        # High confidence should not trigger
        should_not_request = human_loop.should_request_feedback(
            confidence=0.9,
            decision_importance=0.5
        )
        assert should_not_request is False
    
    def test_confidence_threshold_behavior(self):
        """Test confidence threshold behavior."""
        human_loop = HumanInTheLoop(
            enable_active_learning=True,
            uncertainty_threshold=0.7
        )
        
        # Test at threshold
        at_threshold = human_loop.should_request_feedback(confidence=0.7, decision_importance=0.5)
        
        # Test below threshold
        below_threshold = human_loop.should_request_feedback(confidence=0.6, decision_importance=0.5)
        
        # Test above threshold
        above_threshold = human_loop.should_request_feedback(confidence=0.8, decision_importance=0.5)
        
        assert below_threshold is True  # Should request
        assert above_threshold is False  # Should not request
    
    def test_preference_learning(self):
        """Test preference pattern extraction."""
        human_loop = HumanInTheLoop()
        
        # Learn preferences
        preferences = [
            {"preferred": "concise responses"},
            {"preferred": "detailed explanations"},
            {"preferred": "step by step"}
        ]
        
        learned = human_loop.learn_preferences(
            human_id="user123",
            preferences=preferences
        )
        
        assert learned is not None
        assert "user123" in human_loop.feedback_patterns
    
    def test_preference_prediction(self):
        """Test preference prediction."""
        human_loop = HumanInTheLoop()
        
        # Learn some preferences first
        human_loop.learn_preferences(
            human_id="user123",
            preferences=[{"preferred": "detailed"}]
        )
        
        # Predict preference
        predictions = human_loop.predict_human_preference(
            human_id="user123",
            decision="Choose response style",
            options=["concise", "detailed", "medium"]
        )
        
        assert isinstance(predictions, dict)
        assert len(predictions) == 3
        assert all(0.0 <= score <= 1.0 for score in predictions.values())
    
    def test_correction_application(self):
        """Test correction recording and application."""
        human_loop = HumanInTheLoop()
        
        correction_record = human_loop.apply_corrections(
            agent_name="ReactAgent",
            corrections={"approach": "use_different_method", "parameter": 0.5}
        )
        
        assert correction_record is not None
        assert correction_record["agent_name"] == "ReactAgent"
        assert "corrections" in correction_record
        assert len(human_loop.correction_history) > 0
    
    def test_get_pending_requests(self):
        """Test getting pending feedback requests."""
        human_loop = HumanInTheLoop()
        
        # Create some requests
        request1 = human_loop.request_feedback(
            agent_name="Agent1",
            decision="Decision 1",
            context={},
            question="Q1?"
        )
        request2 = human_loop.request_feedback(
            agent_name="Agent2",
            decision="Decision 2",
            context={},
            question="Q2?"
        )
        
        pending = human_loop.get_pending_requests()
        assert len(pending) >= 2
    
    def test_feedback_statistics(self):
        """Test feedback statistics."""
        human_loop = HumanInTheLoop()
        
        # Add some feedback
        request_id = human_loop.request_feedback(
            agent_name="ReactAgent",
            decision="Test",
            context={},
            question="Test?"
        )
        human_loop.submit_feedback(request_id, {
            "approved": True,
            "rating": 0.9
        })
        
        stats = human_loop.get_statistics()
        
        assert "total_feedback_received" in stats
        assert stats["total_feedback_received"] > 0

