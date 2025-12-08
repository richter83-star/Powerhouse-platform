
"""
Self-Update Orchestrator - Autonomous Update Management
====================================================

Coordinates the entire self-triggered update process:
1. Version detection
2. Simulation and validation
3. Policy evaluation
4. CI/CD triggering
5. Controlled rollout
6. Monitoring and rollback
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .version_detector import (
    VersionDetector,
    VersionInfo,
    VersionComparison,
    UpdatePriority,
    UpdateSource
)
from .update_simulator import (
    UpdateSimulator,
    SimulationResult,
    SimulationConfig,
    TestType,
    SimulationStatus
)
from .update_policy_engine import (
    UpdatePolicyEngine,
    PolicyEvaluation,
    UpdateDecision,
    RiskLevel
)
from .cicd_integrator import (
    CICDIntegrator,
    DeploymentTrigger,
    DeploymentResult,
    CICDConfig
)
from .rollout_controller import (
    RolloutController,
    RolloutConfig,
    RolloutStatus,
    RolloutStrategy
)

logger = logging.getLogger(__name__)


@dataclass
class UpdateWorkflow:
    """Represents a complete update workflow"""
    workflow_id: str
    component: str
    version: str
    started_at: datetime
    completed_at: Optional[datetime]
    
    # Stage results
    version_comparison: Optional[VersionComparison]
    simulation_result: Optional[SimulationResult]
    policy_evaluation: Optional[PolicyEvaluation]
    deployment_trigger: Optional[DeploymentTrigger]
    rollout_status: Optional[RolloutStatus]
    
    # Status
    current_stage: str
    success: bool
    errors: List[str]
    

class SelfUpdateOrchestrator:
    """Orchestrates autonomous self-updates"""
    
    def __init__(
        self,
        check_interval: int = 3600,  # 1 hour
        auto_update_enabled: bool = True,
        cicd_config: Optional[CICDConfig] = None
    ):
        self.check_interval = check_interval
        self.auto_update_enabled = auto_update_enabled
        
        # Initialize components
        self.version_detector = VersionDetector(check_interval=check_interval)
        self.update_simulator = UpdateSimulator()
        self.policy_engine = UpdatePolicyEngine()
        self.cicd_integrator = CICDIntegrator(config=cicd_config)
        self.rollout_controller = RolloutController()
        
        # Workflow tracking
        self.active_workflows: Dict[str, UpdateWorkflow] = {}
        self.completed_workflows: List[UpdateWorkflow] = []
        self.workflow_counter = 0
        
        # State
        self._running = False
        self._update_check_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the orchestrator"""
        if self._running:
            logger.warning("Self-update orchestrator already running")
            return
        
        self._running = True
        
        # Start all components
        await self.version_detector.start()
        await self.cicd_integrator.start()
        await self.rollout_controller.start()
        
        # Start update check loop
        self._update_check_task = asyncio.create_task(self._update_check_loop())
        
        logger.info("Self-update orchestrator started")
    
    async def stop(self):
        """Stop the orchestrator"""
        self._running = False
        
        # Stop components
        await self.version_detector.stop()
        await self.cicd_integrator.stop()
        await self.rollout_controller.stop()
        
        # Stop update check loop
        if self._update_check_task:
            self._update_check_task.cancel()
            try:
                await self._update_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Self-update orchestrator stopped")
    
    async def _update_check_loop(self):
        """Main loop for checking and processing updates"""
        while self._running:
            try:
                if self.auto_update_enabled:
                    await self.check_and_process_updates()
                
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in update check loop: {e}")
                await asyncio.sleep(60)
    
    async def check_and_process_updates(self):
        """Check for updates and process them if found"""
        logger.info("Checking for available updates...")
        
        # Check for updates
        await self.version_detector.check_for_updates()
        
        # Get all comparisons
        comparisons = self.version_detector.get_all_comparisons()
        
        # Process each update
        for comparison in comparisons:
            if not comparison.is_update_available:
                continue
            
            logger.info(
                f"Update available for {comparison.component}: "
                f"{comparison.current_version} -> {comparison.available_version}"
            )
            
            # Get version info
            version_infos = self.version_detector.available_versions.get(
                comparison.component, []
            )
            
            if not version_infos:
                continue
            
            version_info = max(version_infos, key=lambda v: v.version)
            
            # Start workflow
            await self.process_update(version_info)
    
    async def process_update(
        self,
        version_info: VersionInfo,
        manual: bool = False
    ) -> UpdateWorkflow:
        """Process a single update through the complete workflow"""
        workflow_id = f"workflow_{self.workflow_counter}_{datetime.utcnow().timestamp()}"
        self.workflow_counter += 1
        
        workflow = UpdateWorkflow(
            workflow_id=workflow_id,
            component=version_info.component,
            version=version_info.version,
            started_at=datetime.utcnow(),
            completed_at=None,
            version_comparison=None,
            simulation_result=None,
            policy_evaluation=None,
            deployment_trigger=None,
            rollout_status=None,
            current_stage="initiated",
            success=False,
            errors=[]
        )
        
        self.active_workflows[workflow_id] = workflow
        
        try:
            # Stage 1: Version comparison
            workflow.current_stage = "version_comparison"
            comparison = self.version_detector.compare_versions(version_info.component)
            workflow.version_comparison = comparison
            
            if not comparison or not comparison.is_update_available:
                workflow.errors.append("No update available")
                raise Exception("No update available")
            
            logger.info(f"[{workflow_id}] Stage 1: Version comparison complete")
            
            # Stage 2: Simulation
            workflow.current_stage = "simulation"
            simulation_config = SimulationConfig(
                component=version_info.component,
                version=version_info.version,
                test_types=[
                    TestType.UNIT_TESTS,
                    TestType.INTEGRATION_TESTS,
                    TestType.PERFORMANCE_TESTS,
                    TestType.REGRESSION_TESTS
                ],
                timeout_seconds=600,
                performance_baseline={
                    "avg_response_time_ms": 150,
                    "throughput_rps": 1000
                },
                compatibility_requirements={},
                test_data_path=None
            )
            
            simulation_result = await self.update_simulator.simulate_update(
                version_info,
                simulation_config
            )
            workflow.simulation_result = simulation_result
            
            if simulation_result.status != SimulationStatus.SUCCESS:
                workflow.errors.append(f"Simulation failed: {simulation_result.errors}")
                raise Exception("Simulation failed")
            
            logger.info(f"[{workflow_id}] Stage 2: Simulation complete - {simulation_result.status.value}")
            
            # Stage 3: Policy evaluation
            workflow.current_stage = "policy_evaluation"
            policy_evaluation = self.policy_engine.evaluate_update(
                version_info,
                comparison,
                simulation_result
            )
            workflow.policy_evaluation = policy_evaluation
            
            if policy_evaluation.decision != UpdateDecision.APPROVE:
                workflow.errors.append(
                    f"Policy rejected: {policy_evaluation.decision.value} - {policy_evaluation.reasons}"
                )
                
                if not manual:
                    raise Exception(f"Policy decision: {policy_evaluation.decision.value}")
            
            logger.info(
                f"[{workflow_id}] Stage 3: Policy evaluation complete - "
                f"{policy_evaluation.decision.value} (Risk: {policy_evaluation.risk_level.value})"
            )
            
            # Stage 4: CI/CD trigger (if approved)
            if policy_evaluation.decision == UpdateDecision.APPROVE:
                workflow.current_stage = "cicd_trigger"
                
                deployment_trigger = await self.cicd_integrator.trigger_deployment(
                    version_info,
                    policy_evaluation,
                    triggered_by="system" if not manual else "manual"
                )
                workflow.deployment_trigger = deployment_trigger
                
                logger.info(f"[{workflow_id}] Stage 4: CI/CD triggered - {deployment_trigger.trigger_id}")
                
                # Stage 5: Controlled rollout
                workflow.current_stage = "rollout"
                
                rollout_config = self._get_rollout_config(
                    version_info.priority,
                    policy_evaluation.risk_level
                )
                
                rollout_status = await self.rollout_controller.start_rollout(
                    version_info.component,
                    version_info.version,
                    rollout_config
                )
                workflow.rollout_status = rollout_status
                
                logger.info(
                    f"[{workflow_id}] Stage 5: Rollout started - "
                    f"{rollout_status.rollout_id} ({rollout_config.strategy.value})"
                )
                
                # Wait for rollout completion
                await self._wait_for_rollout(rollout_status.rollout_id, workflow)
                
                workflow.success = True
                workflow.current_stage = "completed"
            else:
                workflow.current_stage = "awaiting_approval"
        
        except Exception as e:
            logger.error(f"[{workflow_id}] Workflow failed: {e}")
            workflow.errors.append(str(e))
            workflow.current_stage = "failed"
        
        finally:
            workflow.completed_at = datetime.utcnow()
            
            # Move to completed
            self.active_workflows.pop(workflow_id, None)
            self.completed_workflows.append(workflow)
            
            if len(self.completed_workflows) > 100:
                self.completed_workflows = self.completed_workflows[-100:]
        
        logger.info(
            f"[{workflow_id}] Workflow completed - "
            f"Success: {workflow.success}, Stage: {workflow.current_stage}"
        )
        
        return workflow
    
    def _get_rollout_config(
        self,
        priority: UpdatePriority,
        risk_level: RiskLevel
    ) -> RolloutConfig:
        """Get rollout configuration based on priority and risk"""
        
        # Critical updates with low risk - fast rollout
        if priority == UpdatePriority.CRITICAL and risk_level == RiskLevel.LOW:
            return RolloutConfig(
                strategy=RolloutStrategy.BLUE_GREEN,
                canary_percentage=10,
                monitoring_duration_seconds=60,
                health_check_interval=10,
                error_threshold=0.01,
                auto_rollback_enabled=True,
                progressive_steps=[100]
            )
        
        # High risk updates - careful canary
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return RolloutConfig(
                strategy=RolloutStrategy.CANARY,
                canary_percentage=5,
                monitoring_duration_seconds=300,
                health_check_interval=30,
                error_threshold=0.005,
                auto_rollback_enabled=True,
                progressive_steps=[5, 25, 50, 100]
            )
        
        # Normal updates - rolling
        return RolloutConfig(
            strategy=RolloutStrategy.ROLLING,
            canary_percentage=10,
            monitoring_duration_seconds=120,
            health_check_interval=20,
            error_threshold=0.01,
            auto_rollback_enabled=True,
            progressive_steps=[10, 25, 50, 75, 100]
        )
    
    async def _wait_for_rollout(self, rollout_id: str, workflow: UpdateWorkflow):
        """Wait for rollout to complete"""
        while True:
            await asyncio.sleep(10)
            
            status = self.rollout_controller.get_rollout_status(rollout_id)
            if not status:
                workflow.errors.append("Rollout status not found")
                break
            
            workflow.rollout_status = status
            
            if status.phase.value in ["complete", "failed"]:
                break
    
    def register_component_version(self, component: str, version: str):
        """Register current version of a component"""
        self.version_detector.register_current_version(component, version)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[UpdateWorkflow]:
        """Get workflow status"""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        
        for workflow in self.completed_workflows:
            if workflow.workflow_id == workflow_id:
                return workflow
        
        return None
    
    def get_pending_approvals(self) -> List[UpdateWorkflow]:
        """Get workflows awaiting manual approval"""
        pending = []
        
        for workflow in self.completed_workflows[-50:]:  # Last 50
            if workflow.current_stage == "awaiting_approval":
                pending.append(workflow)
        
        return pending
    
    async def approve_workflow(self, workflow_id: str) -> UpdateWorkflow:
        """Manually approve a workflow"""
        workflow = self.get_workflow_status(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if workflow.current_stage != "awaiting_approval":
            raise ValueError(f"Workflow {workflow_id} is not awaiting approval")
        
        # Resume workflow
        version_info = VersionInfo(
            version=workflow.version,
            component=workflow.component,
            source=UpdateSource.ARTIFACT_REPOSITORY,
            priority=UpdatePriority.HIGH,
            release_date=datetime.utcnow(),
            changelog="Manual approval",
            download_url="",
            checksum="",
            dependencies=[],
            breaking_changes=False,
            metadata={}
        )
        
        return await self.process_update(version_info, manual=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        total_workflows = len(self.completed_workflows)
        successful = len([w for w in self.completed_workflows if w.success])
        
        return {
            "orchestrator": {
                "running": self._running,
                "auto_update_enabled": self.auto_update_enabled,
                "check_interval_seconds": self.check_interval
            },
            "workflows": {
                "active": len(self.active_workflows),
                "total_completed": total_workflows,
                "successful": successful,
                "failed": total_workflows - successful,
                "success_rate": successful / total_workflows if total_workflows > 0 else 0,
                "awaiting_approval": len(self.get_pending_approvals())
            },
            "components": {
                "version_detector": self.version_detector.get_statistics(),
                "simulator": self.update_simulator.get_statistics(),
                "policy_engine": self.policy_engine.get_statistics(),
                "cicd_integrator": self.cicd_integrator.get_statistics(),
                "rollout_controller": self.rollout_controller.get_statistics()
            }
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export complete orchestrator state"""
        return {
            "configuration": {
                "check_interval": self.check_interval,
                "auto_update_enabled": self.auto_update_enabled
            },
            "active_workflows": {
                wid: asdict(w) for wid, w in self.active_workflows.items()
            },
            "recent_workflows": [
                asdict(w) for w in self.completed_workflows[-20:]
            ],
            "statistics": self.get_statistics(),
            "version_detector_state": self.version_detector.export_state()
        }
