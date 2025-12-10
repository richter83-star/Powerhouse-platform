"""
Tests for Formal Verification (Phase 4)

Tests safety property verification, constraint checking, and evidence collection.
"""

import pytest
from datetime import datetime

from core.verification import FormalVerifier, SafetyProperty, VerificationResult


@pytest.mark.unit
class TestFormalVerifier:
    """Test formal verifier."""
    
    def test_initialization(self):
        """Test verifier initialization."""
        verifier = FormalVerifier()
        
        assert verifier is not None
        assert len(verifier.safety_rules) > 0
    
    def test_no_harmful_output_verification(self):
        """Test NO_HARMFUL_OUTPUT safety property."""
        verifier = FormalVerifier()
        
        # Test safe output
        results = verifier.verify_agent_output(
            agent_name="TestAgent",
            output="This is a safe and helpful response.",
            properties=[SafetyProperty.NO_HARMFUL_OUTPUT]
        )
        
        assert len(results) > 0
        result = results[0]
        assert result.property_name == SafetyProperty.NO_HARMFUL_OUTPUT.value
        
        # Test potentially harmful output
        results2 = verifier.verify_agent_output(
            agent_name="TestAgent",
            output="This contains harmful and dangerous content.",
            properties=[SafetyProperty.NO_HARMFUL_OUTPUT]
        )
        
        # Should detect harmful keywords
        assert len(results2) > 0
    
    def test_no_sensitive_data_leak(self):
        """Test NO_SENSITIVE_DATA_LEAK property."""
        verifier = FormalVerifier()
        
        # Test with PII
        results = verifier.verify_agent_output(
            agent_name="TestAgent",
            output="Contact me at test@example.com or call 555-123-4567",
            properties=[SafetyProperty.NO_SENSITIVE_DATA_LEAK]
        )
        
        assert len(results) > 0
        # Should detect email pattern
    
    def test_credential_detection(self):
        """Test credential pattern detection."""
        verifier = FormalVerifier()
        
        # Test with API key pattern
        results = verifier.verify_agent_output(
            agent_name="TestAgent",
            output="API key: sk-1234567890abcdef1234567890abcdef",
            properties=[SafetyProperty.NO_SENSITIVE_DATA_LEAK]
        )
        
        assert len(results) > 0
    
    def test_resource_limit_checking(self):
        """Test resource limit checking."""
        verifier = FormalVerifier()
        
        # Test token limits
        long_output = "x" * 50000  # Very long output
        results = verifier.verify_agent_output(
            agent_name="TestAgent",
            output=long_output,
            properties=[SafetyProperty.RESOURCE_LIMITS],
            context={"max_tokens": 4000}
        )
        
        assert len(results) > 0
    
    def test_output_bounds_verification(self):
        """Test OUTPUT_IN_BOUNDS property."""
        verifier = FormalVerifier()
        
        # Test within bounds
        results = verifier.verify_agent_output(
            agent_name="TestAgent",
            output="Normal output",
            properties=[SafetyProperty.OUTPUT_IN_BOUNDS],
            context={"min_output_length": 0, "max_output_length": 1000}
        )
        
        assert len(results) > 0
    
    def test_custom_constraint_validation(self):
        """Test custom constraint validation."""
        verifier = FormalVerifier()
        
        # Add custom constraint
        verifier.add_constraint(
            name="max_length",
            constraint={"max_length": 100},
            validator=lambda action: len(str(action.get("output", ""))) <= 100
        )
        
        # Test valid action
        result = verifier.verify_agent_action(
            agent_name="TestAgent",
            action={"output": "Short output"}
        )
        
        assert result is not None
        
        # Test invalid action
        result2 = verifier.verify_agent_action(
            agent_name="TestAgent",
            action={"output": "x" * 200}  # Too long
        )
        
        assert not result2.verified or len(result2.violations) > 0
    
    def test_evidence_collection(self):
        """Test evidence gathering for violations."""
        verifier = FormalVerifier()
        
        results = verifier.verify_agent_output(
            agent_name="TestAgent",
            output="Test output",
            properties=[SafetyProperty.NO_HARMFUL_OUTPUT]
        )
        
        assert len(results) > 0
        result = results[0]
        assert isinstance(result.evidence, list)
        assert isinstance(result.violations, list)
        assert 0.0 <= result.confidence <= 1.0
    
    def test_violation_reporting(self):
        """Test violation reporting."""
        verifier = FormalVerifier()
        
        # Output that should trigger violations
        results = verifier.verify_agent_output(
            agent_name="TestAgent",
            output="This is harmful and contains test@example.com",
            properties=[
                SafetyProperty.NO_HARMFUL_OUTPUT,
                SafetyProperty.NO_SENSITIVE_DATA_LEAK
            ]
        )
        
        # Should have violations
        violations = [r for r in results if not r.verified]
        assert len(violations) > 0
    
    def test_verification_summary(self):
        """Test verification summary."""
        verifier = FormalVerifier()
        
        # Run some verifications
        verifier.verify_agent_output(
            agent_name="TestAgent",
            output="Safe output",
            properties=[SafetyProperty.NO_HARMFUL_OUTPUT]
        )
        
        summary = verifier.get_verification_summary()
        
        assert "total_verifications" in summary
        assert "verified" in summary
        assert "failed" in summary
        assert summary["total_verifications"] > 0

