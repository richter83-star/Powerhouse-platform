
"""
Update Policy Engine - Policy-Driven Update Decisions
=================================================

Makes intelligent decisions about updates based on:
- Business policies
- Risk assessment
- Performance requirements
- Compliance rules
"""

import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .version_detector import VersionInfo, VersionComparison, UpdatePriority
from .update_simulator import SimulationResult, SimulationStatus

logger = logging.getLogger(__name__)


class UpdateDecision(Enum):
    """Update decision types"""
    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"
    MANUAL_REVIEW = "manual_review"


class RiskLevel(Enum):
    """Risk levels for updates"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class UpdatePolicy:
    """Policy for update decisions"""
    name: str
    enabled: bool
    priority: int  # Higher priority evaluated first
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    description: str


@dataclass
class PolicyEvaluation:
    """Result of policy evaluation"""
    decision: UpdateDecision
    risk_level: RiskLevel
    approved_policies: List[str]
    rejected_policies: List[str]
    reasons: List[str]
    conditions_met: Dict[str, bool]
    recommended_action: str
    deployment_window: Optional[Dict[str, str]]


class UpdatePolicyEngine:
    """Evaluates update policies and makes decisions"""
    
    def __init__(self):
        self.policies: List[UpdatePolicy] = []
        self._init_default_policies()
        
        self.evaluation_history: List[Dict[str, Any]] = []
    
    def _init_default_policies(self):
        """Initialize default policies"""
        self.policies = [
            # Critical security updates - always approve immediately
            UpdatePolicy(
                name="critical_security_updates",
                enabled=True,
                priority=100,
                conditions={
                    "priority": UpdatePriority.CRITICAL.value,
                    "simulation_success": True
                },
                actions={
                    "decision": UpdateDecision.APPROVE.value,
                    "immediate": True
                },
                description="Approve critical security updates immediately"
            ),
            
            # Breaking changes require manual review
            UpdatePolicy(
                name="breaking_changes_review",
                enabled=True,
                priority=90,
                conditions={
                    "breaking_changes": True
                },
                actions={
                    "decision": UpdateDecision.MANUAL_REVIEW.value,
                    "notify": ["dev-team", "ops-team"]
                },
                description="Breaking changes require manual review"
            ),
            
            # Failed simulations - reject
            UpdatePolicy(
                name="failed_simulation_reject",
                enabled=True,
                priority=85,
                conditions={
                    "simulation_status": SimulationStatus.FAILED.value
                },
                actions={
                    "decision": UpdateDecision.REJECT.value,
                    "reason": "Simulation failed validation"
                },
                description="Reject updates that fail simulation"
            ),
            
            # Business hours deployment
            UpdatePolicy(
                name="business_hours_only",
                enabled=True,
                priority=80,
                conditions={
                    "priority": [UpdatePriority.HIGH.value, UpdatePriority.MEDIUM.value],
                    "business_hours": True
                },
                actions={
                    "decision": UpdateDecision.DEFER.value,
                    "defer_until": "next_business_hours"
                },
                description="Deploy non-critical updates only during business hours"
            ),
            
            # Maintenance window policy
            UpdatePolicy(
                name="maintenance_window",
                enabled=True,
                priority=75,
                conditions={
                    "in_maintenance_window": False,
                    "priority": [UpdatePriority.MEDIUM.value, UpdatePriority.LOW.value]
                },
                actions={
                    "decision": UpdateDecision.DEFER.value,
                    "defer_until": "next_maintenance_window"
                },
                description="Deploy low-priority updates during maintenance windows"
            ),
            
            # High success rate approval
            UpdatePolicy(
                name="high_success_rate_approval",
                enabled=True,
                priority=70,
                conditions={
                    "simulation_success_rate": 0.95,
                    "no_breaking_changes": True
                },
                actions={
                    "decision": UpdateDecision.APPROVE.value,
                    "schedule": "next_deployment_slot"
                },
                description="Approve updates with high simulation success rate"
            ),
            
            # Performance degradation rejection
            UpdatePolicy(
                name="performance_degradation_reject",
                enabled=True,
                priority=80,
                conditions={
                    "performance_degradation": True,
                    "degradation_threshold": 0.1  # 10%
                },
                actions={
                    "decision": UpdateDecision.REJECT.value,
                    "reason": "Unacceptable performance degradation"
                },
                description="Reject updates with significant performance degradation"
            )
        ]
        
        # Sort by priority
        self.policies.sort(key=lambda p: p.priority, reverse=True)
    
    def evaluate_update(
        self,
        version_info: VersionInfo,
        comparison: VersionComparison,
        simulation_result: Optional[SimulationResult] = None
    ) -> PolicyEvaluation:
        """Evaluate whether to approve an update"""
        logger.info(f"Evaluating update for {version_info.component} v{version_info.version}")
        
        # Collect context for policy evaluation
        context = self._build_evaluation_context(version_info, comparison, simulation_result)
        
        # Evaluate all policies
        approved_policies = []
        rejected_policies = []
        reasons = []
        conditions_met = {}
        
        decision = UpdateDecision.DEFER  # Default
        risk_level = RiskLevel.MEDIUM
        
        for policy in self.policies:
            if not policy.enabled:
                continue
            
            is_applicable, conditions_result = self._evaluate_policy_conditions(
                policy,
                context
            )
            
            if is_applicable:
                policy_decision = UpdateDecision(policy.actions.get("decision", "defer"))
                
                if policy_decision == UpdateDecision.APPROVE:
                    approved_policies.append(policy.name)
                    decision = UpdateDecision.APPROVE
                    reasons.append(f"Approved by policy: {policy.name}")
                    break  # First approval wins
                
                elif policy_decision == UpdateDecision.REJECT:
                    rejected_policies.append(policy.name)
                    decision = UpdateDecision.REJECT
                    reason = policy.actions.get("reason", policy.description)
                    reasons.append(f"Rejected by policy: {policy.name} - {reason}")
                    break  # First rejection wins
                
                elif policy_decision == UpdateDecision.MANUAL_REVIEW:
                    decision = UpdateDecision.MANUAL_REVIEW
                    reasons.append(f"Manual review required: {policy.name}")
                    break
                
                elif policy_decision == UpdateDecision.DEFER:
                    reasons.append(f"Deferred by policy: {policy.name}")
                
                conditions_met.update(conditions_result)
        
        # Assess risk
        risk_level = self._assess_risk(version_info, simulation_result)
        
        # Generate recommendation
        recommended_action = self._generate_recommendation(
            decision,
            risk_level,
            reasons
        )
        
        # Determine deployment window
        deployment_window = self._determine_deployment_window(
            decision,
            version_info.priority
        )
        
        # Create evaluation result
        evaluation = PolicyEvaluation(
            decision=decision,
            risk_level=risk_level,
            approved_policies=approved_policies,
            rejected_policies=rejected_policies,
            reasons=reasons,
            conditions_met=conditions_met,
            recommended_action=recommended_action,
            deployment_window=deployment_window
        )
        
        # Record evaluation
        self.evaluation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "component": version_info.component,
            "version": version_info.version,
            "decision": decision.value,
            "risk_level": risk_level.value,
            "reasons": reasons
        })
        
        logger.info(f"Policy evaluation complete: {decision.value} (Risk: {risk_level.value})")
        return evaluation
    
    def _build_evaluation_context(
        self,
        version_info: VersionInfo,
        comparison: VersionComparison,
        simulation_result: Optional[SimulationResult]
    ) -> Dict[str, Any]:
        """Build context for policy evaluation"""
        context = {
            "component": version_info.component,
            "version": version_info.version,
            "priority": version_info.priority.value,
            "breaking_changes": version_info.breaking_changes,
            "no_breaking_changes": not version_info.breaking_changes,
            "update_available": comparison.is_update_available,
            "version_distance": comparison.version_distance,
            "current_time": datetime.utcnow(),
            "business_hours": self._is_business_hours(),
            "in_maintenance_window": self._is_maintenance_window()
        }
        
        if simulation_result:
            success_rate = (
                simulation_result.tests_passed / simulation_result.tests_run
                if simulation_result.tests_run > 0 else 0
            )
            
            context.update({
                "simulation_status": simulation_result.status.value,
                "simulation_success": simulation_result.status == SimulationStatus.SUCCESS,
                "simulation_success_rate": success_rate,
                "tests_passed": simulation_result.tests_passed,
                "tests_failed": simulation_result.tests_failed,
                "performance_metrics": simulation_result.performance_metrics,
                "performance_degradation": len(simulation_result.warnings) > 0
            })
        
        return context
    
    def _evaluate_policy_conditions(
        self,
        policy: UpdatePolicy,
        context: Dict[str, Any]
    ) -> tuple[bool, Dict[str, bool]]:
        """Evaluate if policy conditions are met"""
        conditions_result = {}
        all_met = True
        
        for condition_key, condition_value in policy.conditions.items():
            if condition_key not in context:
                conditions_result[condition_key] = False
                all_met = False
                continue
            
            context_value = context[condition_key]
            
            # Handle different condition types
            if isinstance(condition_value, list):
                # Check if context value is in list
                met = context_value in condition_value
            elif isinstance(condition_value, (int, float)):
                # Check if context value meets threshold
                met = context_value >= condition_value
            elif isinstance(condition_value, bool):
                # Check boolean match
                met = context_value == condition_value
            else:
                # Check exact match
                met = context_value == condition_value
            
            conditions_result[condition_key] = met
            if not met:
                all_met = False
        
        return all_met, conditions_result
    
    def _assess_risk(
        self,
        version_info: VersionInfo,
        simulation_result: Optional[SimulationResult]
    ) -> RiskLevel:
        """Assess risk level of update"""
        risk_score = 0
        
        # Version factors
        if version_info.breaking_changes:
            risk_score += 3
        
        if version_info.priority == UpdatePriority.CRITICAL:
            risk_score += 1  # Critical but necessary
        
        # Simulation factors
        if simulation_result:
            if simulation_result.status == SimulationStatus.FAILED:
                risk_score += 5
            
            if simulation_result.tests_failed > 0:
                risk_score += 2
            
            if len(simulation_result.errors) > 0:
                risk_score += 2
            
            if len(simulation_result.warnings) > 3:
                risk_score += 1
        
        # Determine risk level
        if risk_score >= 7:
            return RiskLevel.CRITICAL
        elif risk_score >= 5:
            return RiskLevel.HIGH
        elif risk_score >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_recommendation(
        self,
        decision: UpdateDecision,
        risk_level: RiskLevel,
        reasons: List[str]
    ) -> str:
        """Generate recommended action"""
        if decision == UpdateDecision.APPROVE:
            if risk_level == RiskLevel.LOW:
                return "Approved for immediate deployment"
            else:
                return f"Approved for deployment with {risk_level.value} risk - monitor closely"
        
        elif decision == UpdateDecision.REJECT:
            return f"Rejected - {'; '.join(reasons)}"
        
        elif decision == UpdateDecision.MANUAL_REVIEW:
            return "Manual review required before deployment"
        
        else:  # DEFER
            return "Deferred to appropriate deployment window"
    
    def _determine_deployment_window(
        self,
        decision: UpdateDecision,
        priority: UpdatePriority
    ) -> Optional[Dict[str, str]]:
        """Determine when update should be deployed"""
        if decision != UpdateDecision.APPROVE:
            return None
        
        now = datetime.utcnow()
        
        if priority == UpdatePriority.CRITICAL:
            # Deploy immediately
            return {
                "start": now.isoformat(),
                "end": (now + timedelta(hours=1)).isoformat(),
                "type": "immediate"
            }
        
        elif priority == UpdatePriority.HIGH:
            # Deploy in next business hours
            next_window = self._next_business_hours(now)
            return {
                "start": next_window.isoformat(),
                "end": (next_window + timedelta(hours=2)).isoformat(),
                "type": "business_hours"
            }
        
        else:
            # Deploy in next maintenance window
            next_window = self._next_maintenance_window(now)
            return {
                "start": next_window.isoformat(),
                "end": (next_window + timedelta(hours=4)).isoformat(),
                "type": "maintenance_window"
            }
    
    def _is_business_hours(self) -> bool:
        """Check if current time is business hours"""
        now = datetime.utcnow()
        # Business hours: Monday-Friday, 9 AM - 5 PM UTC
        return (
            now.weekday() < 5 and  # Monday = 0, Friday = 4
            time(9, 0) <= now.time() <= time(17, 0)
        )
    
    def _is_maintenance_window(self) -> bool:
        """Check if current time is in maintenance window"""
        now = datetime.utcnow()
        # Maintenance window: Sunday 2 AM - 6 AM UTC
        return (
            now.weekday() == 6 and  # Sunday = 6
            time(2, 0) <= now.time() <= time(6, 0)
        )
    
    def _next_business_hours(self, from_time: datetime) -> datetime:
        """Get next business hours start time"""
        next_time = from_time
        
        # Move to next day if after hours
        if next_time.time() > time(17, 0):
            next_time = next_time.replace(
                hour=9, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)
        
        # Skip weekends
        while next_time.weekday() >= 5:
            next_time += timedelta(days=1)
        
        # Set to 9 AM if before
        if next_time.time() < time(9, 0):
            next_time = next_time.replace(hour=9, minute=0, second=0, microsecond=0)
        
        return next_time
    
    def _next_maintenance_window(self, from_time: datetime) -> datetime:
        """Get next maintenance window start time"""
        next_time = from_time
        
        # Move to next Sunday
        days_until_sunday = (6 - next_time.weekday()) % 7
        if days_until_sunday == 0 and next_time.time() > time(6, 0):
            days_until_sunday = 7
        
        next_time += timedelta(days=days_until_sunday)
        next_time = next_time.replace(hour=2, minute=0, second=0, microsecond=0)
        
        return next_time
    
    def add_policy(self, policy: UpdatePolicy):
        """Add custom policy"""
        self.policies.append(policy)
        self.policies.sort(key=lambda p: p.priority, reverse=True)
        logger.info(f"Added policy: {policy.name}")
    
    def remove_policy(self, policy_name: str) -> bool:
        """Remove policy by name"""
        initial_count = len(self.policies)
        self.policies = [p for p in self.policies if p.name != policy_name]
        removed = len(self.policies) < initial_count
        if removed:
            logger.info(f"Removed policy: {policy_name}")
        return removed
    
    def get_policy(self, policy_name: str) -> Optional[UpdatePolicy]:
        """Get policy by name"""
        for policy in self.policies:
            if policy.name == policy_name:
                return policy
        return None
    
    def update_policy(self, policy_name: str, updates: Dict[str, Any]) -> bool:
        """Update existing policy"""
        policy = self.get_policy(policy_name)
        if not policy:
            return False
        
        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        logger.info(f"Updated policy: {policy_name}")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get policy engine statistics"""
        total_evaluations = len(self.evaluation_history)
        
        if total_evaluations == 0:
            return {
                "total_evaluations": 0,
                "total_policies": len(self.policies),
                "enabled_policies": len([p for p in self.policies if p.enabled])
            }
        
        decisions = [e["decision"] for e in self.evaluation_history]
        
        return {
            "total_evaluations": total_evaluations,
            "total_policies": len(self.policies),
            "enabled_policies": len([p for p in self.policies if p.enabled]),
            "approved": decisions.count(UpdateDecision.APPROVE.value),
            "rejected": decisions.count(UpdateDecision.REJECT.value),
            "deferred": decisions.count(UpdateDecision.DEFER.value),
            "manual_review": decisions.count(UpdateDecision.MANUAL_REVIEW.value),
            "recent_evaluations": self.evaluation_history[-10:]
        }
