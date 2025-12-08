"""
Tests for Self-Triggered CI/CD Update System
=========================================
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from core.version_detector import (
    VersionDetector,
    VersionInfo,
    UpdateSource,
    UpdatePriority
)
from core.update_simulator import (
    UpdateSimulator,
    SimulationConfig,
    TestType
)
from core.update_policy_engine import (
    UpdatePolicyEngine,
    UpdatePolicy,
    UpdateDecision
)
from core.cicd_integrator import CICDIntegrator
from core.rollout_controller import (
    RolloutController,
    RolloutConfig,
    RolloutStrategy
)
from core.self_update_orchestrator import SelfUpdateOrchestrator


class TestVersionDetector:
    """Test version detection"""
    
    @pytest.mark.asyncio
    async def test_version_detection(self):
        """Test detecting versions"""
        detector = VersionDetector(check_interval=60)
        detector.register_current_version("test_component", "1.0.0")
        
        updates = await detector.check_for_updates()
        
        assert isinstance(updates, dict)
        assert detector.last_check is not None
    
    @pytest.mark.asyncio
    async def test_version_comparison(self):
        """Test version comparison"""
        detector = VersionDetector(check_interval=60)
        detector.register_current_version("test_component", "1.0.0")
        
        await detector.check_for_updates()
        
        comparison = detector.compare_versions("test_component")
        
        assert comparison is not None
        assert comparison.component == "test_component"
        assert comparison.current_version == "1.0.0"
    
    def test_critical_updates(self):
        """Test getting critical updates"""
        detector = VersionDetector(check_interval=60)
        detector.register_current_version("test_component", "1.0.0")
        
        critical = detector.get_critical_updates()
        
        assert isinstance(critical, list)


class TestUpdateSimulator:
    """Test update simulation"""
    
    @pytest.mark.asyncio
    async def test_simulation(self):
        """Test running simulation"""
        simulator = UpdateSimulator()
        
        version_info = VersionInfo(
            version="2.0.0",
            component="test_component",
            source=UpdateSource.GIT_REPOSITORY,
            priority=UpdatePriority.HIGH,
            release_date=datetime.utcnow(),
            changelog="Test update",
            download_url="https://example.com/v2.0.0",
            checksum="abc123",
            dependencies=[],
            breaking_changes=False,
            metadata={}
        )
        
        result = await simulator.simulate_update(version_info)
        
        assert result is not None
        assert result.component == "test_component"
        assert result.version == "2.0.0"
        assert result.tests_run > 0
    
    @pytest.mark.asyncio
    async def test_batch_simulation(self):
        """Test batch simulation"""
        simulator = UpdateSimulator()
        
        version_infos = [
            VersionInfo(
                version=f"2.{i}.0",
                component=f"component_{i}",
                source=UpdateSource.GIT_REPOSITORY,
                priority=UpdatePriority.MEDIUM,
                release_date=datetime.utcnow(),
                changelog=f"Update {i}",
                download_url=f"https://example.com/v2.{i}.0",
                checksum=f"abc{i}",
                dependencies=[],
                breaking_changes=False,
                metadata={}
            )
            for i in range(3)
        ]
        
        results = await simulator.batch_simulate(version_infos)
        
        assert len(results) == 3


class TestUpdatePolicyEngine:
    """Test policy engine"""
    
    def test_policy_evaluation(self):
        """Test evaluating policies"""
        engine = UpdatePolicyEngine()
        
        version_info = VersionInfo(
            version="2.0.0",
            component="test_component",
            source=UpdateSource.GIT_REPOSITORY,
            priority=UpdatePriority.HIGH,
            release_date=datetime.utcnow(),
            changelog="Test update",
            download_url="https://example.com/v2.0.0",
            checksum="abc123",
            dependencies=[],
            breaking_changes=False,
            metadata={}
        )
        
        from core.version_detector import VersionComparison
        comparison = VersionComparison(
            current_version="1.0.0",
            available_version="2.0.0",
            component="test_component",
            is_update_available=True,
            version_distance=1,
            priority=UpdatePriority.HIGH,
            recommendation="Update recommended"
        )
        
        evaluation = engine.evaluate_update(version_info, comparison, None)
        
        assert evaluation is not None
        assert evaluation.decision in [
            UpdateDecision.APPROVE,
            UpdateDecision.REJECT,
            UpdateDecision.DEFER,
            UpdateDecision.MANUAL_REVIEW
        ]
    
    def test_custom_policy(self):
        """Test adding custom policy"""
        engine = UpdatePolicyEngine()
        
        custom_policy = UpdatePolicy(
            name="test_policy",
            enabled=True,
            priority=100,
            conditions={"test": True},
            actions={"decision": "approve"},
            description="Test policy"
        )
        
        initial_count = len(engine.policies)
        engine.add_policy(custom_policy)
        
        assert len(engine.policies) == initial_count + 1


class TestCICDIntegrator:
    """Test CI/CD integration"""
    
    @pytest.mark.asyncio
    async def test_deployment_trigger(self):
        """Test triggering deployment"""
        integrator = CICDIntegrator()
        await integrator.start()
        
        version_info = VersionInfo(
            version="2.0.0",
            component="test_component",
            source=UpdateSource.GIT_REPOSITORY,
            priority=UpdatePriority.HIGH,
            release_date=datetime.utcnow(),
            changelog="Test update",
            download_url="https://example.com/v2.0.0",
            checksum="abc123",
            dependencies=[],
            breaking_changes=False,
            metadata={}
        )
        
        from core.update_policy_engine import PolicyEvaluation, RiskLevel
        evaluation = PolicyEvaluation(
            decision=UpdateDecision.APPROVE,
            risk_level=RiskLevel.LOW,
            approved_policies=["test"],
            rejected_policies=[],
            reasons=["Test"],
            conditions_met={},
            recommended_action="Deploy",
            deployment_window=None
        )
        
        trigger = await integrator.trigger_deployment(version_info, evaluation)
        
        assert trigger is not None
        assert trigger.component == "test_component"
        
        await integrator.stop()


class TestRolloutController:
    """Test rollout controller"""
    
    @pytest.mark.asyncio
    async def test_rollout(self):
        """Test starting rollout"""
        controller = RolloutController()
        await controller.start()
        
        config = RolloutConfig(
            strategy=RolloutStrategy.ROLLING,
            canary_percentage=10,
            monitoring_duration_seconds=5,
            health_check_interval=1,
            error_threshold=0.01,
            auto_rollback_enabled=True,
            progressive_steps=[25, 50, 100]
        )
        
        status = await controller.start_rollout(
            "test_component",
            "2.0.0",
            config
        )
        
        assert status is not None
        assert status.component == "test_component"
        
        await controller.stop()


class TestSelfUpdateOrchestrator:
    """Test self-update orchestrator"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_lifecycle(self):
        """Test orchestrator start/stop"""
        orchestrator = SelfUpdateOrchestrator(
            check_interval=60,
            auto_update_enabled=False
        )
        
        await orchestrator.start()
        assert orchestrator._running
        
        await orchestrator.stop()
        assert not orchestrator._running
    
    def test_component_registration(self):
        """Test registering components"""
        orchestrator = SelfUpdateOrchestrator(auto_update_enabled=False)
        
        orchestrator.register_component_version("test_component", "1.0.0")
        
        assert "test_component" in orchestrator.version_detector.current_versions
        assert orchestrator.version_detector.current_versions["test_component"] == "1.0.0"
    
    def test_statistics(self):
        """Test getting statistics"""
        orchestrator = SelfUpdateOrchestrator(auto_update_enabled=False)
        
        stats = orchestrator.get_statistics()
        
        assert "orchestrator" in stats
        assert "workflows" in stats
        assert "components" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
