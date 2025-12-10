"""
Formal Verification System for Agent Behavior

Provides formal methods to verify agent behavior, safety properties,
and compliance with specified constraints.
"""

from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re

from utils.logging import get_logger

logger = get_logger(__name__)


class SafetyProperty(str, Enum):
    """Types of safety properties to verify."""
    NO_HARMFUL_OUTPUT = "no_harmful_output"
    NO_SENSITIVE_DATA_LEAK = "no_sensitive_data_leak"
    NO_UNAUTHORIZED_ACTION = "no_unauthorized_action"
    OUTPUT_IN_BOUNDS = "output_in_bounds"
    RESOURCE_LIMITS = "resource_limits"
    DEADLINE_MET = "deadline_met"
    CONSISTENCY = "consistency"


@dataclass
class VerificationResult:
    """Result of a verification check."""
    property_name: str
    verified: bool
    evidence: List[str]
    confidence: float  # 0.0-1.0
    violations: List[str]
    timestamp: datetime
    verification_method: str


class FormalVerifier:
    """
    Formal verification system for agent behavior.
    
    Uses multiple verification methods:
    - Pattern-based verification
    - Property checking
    - Constraint satisfaction
    - Runtime monitoring
    """
    
    def __init__(self):
        """Initialize formal verifier."""
        self.safety_rules: Dict[SafetyProperty, List[Callable]] = {}
        self.constraints: List[Dict[str, Any]] = []
        self.verification_history: List[VerificationResult] = []
        
        # Initialize default safety rules
        self._initialize_default_rules()
        
        logger.info("FormalVerifier initialized")
    
    def _initialize_default_rules(self):
        """Initialize default safety verification rules."""
        # No harmful output
        self.safety_rules[SafetyProperty.NO_HARMFUL_OUTPUT] = [
            self._check_harmful_keywords,
            self._check_violence,
            self._check_hate_speech
        ]
        
        # No sensitive data leak
        self.safety_rules[SafetyProperty.NO_SENSITIVE_DATA_LEAK] = [
            self._check_pii_patterns,
            self._check_credentials,
            self._check_api_keys
        ]
        
        # Resource limits
        self.safety_rules[SafetyProperty.RESOURCE_LIMITS] = [
            self._check_token_limits,
            self._check_execution_time,
            self._check_memory_usage
        ]
        
        # Output bounds
        self.safety_rules[SafetyProperty.OUTPUT_IN_BOUNDS] = [
            self._check_output_length,
            self._check_output_format
        ]
    
    def verify_agent_output(
        self,
        agent_name: str,
        output: Any,
        properties: Optional[List[SafetyProperty]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[VerificationResult]:
        """
        Verify agent output against safety properties.
        
        Args:
            agent_name: Name of the agent
            output: Agent output to verify
            properties: Properties to check (None = all)
            context: Execution context
            
        Returns:
            List of verification results
        """
        if properties is None:
            properties = list(SafetyProperty)
        
        results = []
        output_str = str(output) if not isinstance(output, str) else output
        
        for property_type in properties:
            result = self._verify_property(
                property_type,
                agent_name,
                output_str,
                context or {}
            )
            results.append(result)
            
            # Log violations
            if not result.verified:
                logger.warning(
                    f"Verification failed: {agent_name} - {property_type.value} "
                    f"- Violations: {result.violations}"
                )
        
        self.verification_history.extend(results)
        
        return results
    
    def verify_agent_action(
        self,
        agent_name: str,
        action: Dict[str, Any],
        constraints: Optional[List[Dict[str, Any]]] = None
    ) -> VerificationResult:
        """
        Verify agent action against constraints.
        
        Args:
            agent_name: Name of the agent
            action: Action to verify
            constraints: Constraints to check
            
        Returns:
            Verification result
        """
        constraints = constraints or self.constraints
        
        violations = []
        evidence = []
        
        for constraint in constraints:
            if not self._check_constraint(action, constraint):
                violations.append(
                    f"Violated constraint: {constraint.get('name', 'Unknown')}"
                )
            else:
                evidence.append(f"Satisfied constraint: {constraint.get('name')}")
        
        verified = len(violations) == 0
        confidence = 1.0 if verified else max(0.0, 1.0 - len(violations) / len(constraints))
        
        result = VerificationResult(
            property_name="action_constraints",
            verified=verified,
            evidence=evidence,
            confidence=confidence,
            violations=violations,
            timestamp=datetime.now(),
            verification_method="constraint_satisfaction"
        )
        
        self.verification_history.append(result)
        
        return result
    
    def add_safety_rule(
        self,
        property_type: SafetyProperty,
        rule: Callable[[str, Dict[str, Any]], Tuple[bool, str]]
    ):
        """
        Add custom safety rule.
        
        Args:
            property_type: Property to add rule for
            rule: Rule function that returns (verified, message)
        """
        if property_type not in self.safety_rules:
            self.safety_rules[property_type] = []
        self.safety_rules[property_type].append(rule)
    
    def add_constraint(
        self,
        name: str,
        constraint: Dict[str, Any],
        validator: Callable[[Dict[str, Any]], bool]
    ):
        """
        Add constraint with validator.
        
        Args:
            name: Constraint name
            constraint: Constraint definition
            validator: Validation function
        """
        constraint["name"] = name
        constraint["validator"] = validator
        self.constraints.append(constraint)
    
    def _verify_property(
        self,
        property_type: SafetyProperty,
        agent_name: str,
        output: str,
        context: Dict[str, Any]
    ) -> VerificationResult:
        """Verify a specific safety property."""
        rules = self.safety_rules.get(property_type, [])
        
        violations = []
        evidence = []
        all_passed = True
        
        for rule in rules:
            try:
                passed, message = rule(output, context)
                if passed:
                    evidence.append(message)
                else:
                    violations.append(message)
                    all_passed = False
            except Exception as e:
                logger.error(f"Safety rule failed: {e}", exc_info=True)
                violations.append(f"Rule execution error: {str(e)}")
                all_passed = False
        
        confidence = len(evidence) / len(rules) if rules else 0.0
        
        return VerificationResult(
            property_name=property_type.value,
            verified=all_passed,
            evidence=evidence,
            confidence=confidence,
            violations=violations,
            timestamp=datetime.now(),
            verification_method="pattern_matching"
        )
    
    # Safety rule implementations
    
    def _check_harmful_keywords(self, output: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for harmful keywords."""
        harmful_keywords = [
            "harmful", "dangerous", "illegal", "violence", "attack"
        ]
        
        output_lower = output.lower()
        found = [kw for kw in harmful_keywords if kw in output_lower]
        
        if found:
            return False, f"Found potentially harmful keywords: {', '.join(found)}"
        return True, "No harmful keywords detected"
    
    def _check_violence(self, output: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for violent content."""
        violence_patterns = [
            r'\b(kill|murder|assassinate|destroy|harm|hurt)\b',
            r'\b(attack|violence|assault)\b'
        ]
        
        for pattern in violence_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return False, f"Violence pattern detected: {pattern}"
        
        return True, "No violence detected"
    
    def _check_hate_speech(self, output: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for hate speech patterns."""
        # Simplified - in production would use more sophisticated detection
        hate_keywords = [
            "hate", "discriminate", "racist", "sexist"
        ]
        
        output_lower = output.lower()
        found = [kw for kw in hate_keywords if kw in output_lower]
        
        if found:
            return False, f"Potential hate speech keywords: {', '.join(found)}"
        return True, "No hate speech detected"
    
    def _check_pii_patterns(self, output: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for personally identifiable information."""
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        # SSN pattern
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        # Credit card pattern
        cc_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        
        patterns = {
            "email": email_pattern,
            "ssn": ssn_pattern,
            "credit_card": cc_pattern
        }
        
        found_pii = []
        for pii_type, pattern in patterns.items():
            if re.search(pattern, output):
                found_pii.append(pii_type)
        
        if found_pii:
            return False, f"PII detected: {', '.join(found_pii)}"
        return True, "No PII detected"
    
    def _check_credentials(self, output: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for credentials like API keys, passwords."""
        # API key patterns
        api_key_patterns = [
            r'sk-[A-Za-z0-9]{32,}',  # OpenAI
            r'AKIA[0-9A-Z]{16}',  # AWS
            r'ghp_[A-Za-z0-9]{36}',  # GitHub
        ]
        
        # Password patterns (simplified)
        password_indicators = ["password", "passwd", "pwd", "secret", "key"]
        
        for pattern in api_key_patterns:
            if re.search(pattern, output):
                return False, "API key pattern detected"
        
        output_lower = output.lower()
        if any(indicator in output_lower for indicator in password_indicators):
            # Check if followed by value
            if re.search(r'(?:password|passwd|pwd|secret|key)[:=]\s*\S+', output_lower):
                return False, "Potential credential leak detected"
        
        return True, "No credentials detected"
    
    def _check_api_keys(self, output: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for API keys."""
        # Same as credentials check
        return self._check_credentials(output, context)
    
    def _check_token_limits(self, output: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if output exceeds token limits."""
        # Rough estimate: 1 token ≈ 4 characters
        token_estimate = len(output) / 4
        max_tokens = context.get("max_tokens", 4000)
        
        if token_estimate > max_tokens:
            return False, f"Token limit exceeded: {token_estimate:.0f} > {max_tokens}"
        return True, f"Token usage: {token_estimate:.0f} <= {max_tokens}"
    
    def _check_execution_time(self, output: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if execution time exceeds limits."""
        execution_time = context.get("execution_time_ms", 0)
        max_time = context.get("max_execution_time_ms", 60000)  # 60s default
        
        if execution_time > max_time:
            return False, f"Execution time exceeded: {execution_time}ms > {max_time}ms"
        return True, f"Execution time: {execution_time}ms <= {max_time}ms"
    
    def _check_memory_usage(self, output: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check memory usage."""
        # Simplified - would use actual memory monitoring
        output_size = len(output.encode('utf-8'))
        max_size = context.get("max_output_size", 1000000)  # 1MB default
        
        if output_size > max_size:
            return False, f"Output size exceeded: {output_size} bytes > {max_size} bytes"
        return True, f"Output size: {output_size} bytes <= {max_size} bytes"
    
    def _check_output_length(self, output: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if output length is within bounds."""
        min_length = context.get("min_output_length", 0)
        max_length = context.get("max_output_length", 100000)
        
        output_len = len(output)
        
        if output_len < min_length:
            return False, f"Output too short: {output_len} < {min_length}"
        if output_len > max_length:
            return False, f"Output too long: {output_len} > {max_length}"
        
        return True, f"Output length in bounds: {min_length} <= {output_len} <= {max_length}"
    
    def _check_output_format(self, output: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if output matches expected format."""
        expected_format = context.get("expected_format")
        
        if expected_format == "json":
            try:
                import json
                json.loads(output)
                return True, "Valid JSON format"
            except:
                return False, "Invalid JSON format"
        
        if expected_format == "list":
            # Check if looks like a list
            if output.strip().startswith('[') and output.strip().endswith(']'):
                return True, "List format detected"
            return False, "Not in list format"
        
        # No format requirement
        return True, "No format requirement"
    
    def _check_constraint(
        self,
        action: Dict[str, Any],
        constraint: Dict[str, Any]
    ) -> bool:
        """Check if action satisfies constraint."""
        validator = constraint.get("validator")
        if validator:
            try:
                return validator(action)
            except Exception as e:
                logger.error(f"Constraint validation failed: {e}")
                return False
        return True
    
    def get_verification_summary(self) -> Dict[str, Any]:
        """Get summary of verification results."""
        total = len(self.verification_history)
        verified = sum(1 for r in self.verification_history if r.verified)
        
        property_stats = {}
        for result in self.verification_history:
            prop = result.property_name
            if prop not in property_stats:
                property_stats[prop] = {"total": 0, "verified": 0}
            property_stats[prop]["total"] += 1
            if result.verified:
                property_stats[prop]["verified"] += 1
        
        return {
            "total_verifications": total,
            "verified": verified,
            "failed": total - verified,
            "verification_rate": verified / total if total > 0 else 0.0,
            "by_property": {
                prop: {
                    "verified": stats["verified"],
                    "total": stats["total"],
                    "rate": stats["verified"] / stats["total"] if stats["total"] > 0 else 0.0
                }
                for prop, stats in property_stats.items()
            }
        }


