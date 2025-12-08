
"""
CI/CD Integrator - Triggers and Manages CI/CD Pipeline Updates
===========================================================

Integrates with CI/CD systems to trigger automated deployments:
- GitHub Actions
- GitLab CI
- Jenkins
- CircleCI
- Internal CI/CD systems
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp

from .version_detector import VersionInfo
from .update_policy_engine import PolicyEvaluation, UpdateDecision

logger = logging.getLogger(__name__)


class CICDProvider(Enum):
    """Supported CI/CD providers"""
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    CIRCLECI = "circleci"
    INTERNAL = "internal"


class DeploymentStatus(Enum):
    """Status of CI/CD deployment"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CICDConfig:
    """Configuration for CI/CD provider"""
    provider: CICDProvider
    endpoint: str
    auth_token: str
    repository: str
    branch: str
    workflow_file: Optional[str]
    additional_params: Dict[str, Any]


@dataclass
class DeploymentTrigger:
    """Deployment trigger information"""
    trigger_id: str
    component: str
    version: str
    provider: CICDProvider
    triggered_at: datetime
    triggered_by: str  # 'system' or user ID
    policy_evaluation: PolicyEvaluation
    deployment_config: Dict[str, Any]


@dataclass
class DeploymentResult:
    """Result of CI/CD deployment"""
    trigger_id: str
    component: str
    version: str
    status: DeploymentStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: float
    pipeline_url: str
    logs_url: Optional[str]
    artifacts: Dict[str, str]
    errors: List[str]


class CICDIntegrator:
    """Integrates with CI/CD systems"""
    
    def __init__(self, config: Optional[CICDConfig] = None):
        self.config = config or self._get_default_config()
        
        self.active_deployments: Dict[str, DeploymentResult] = {}
        self.completed_deployments: List[DeploymentResult] = []
        self.deployment_queue: List[DeploymentTrigger] = []
        
        self._trigger_counter = 0
        self._running = False
        self._deployment_task: Optional[asyncio.Task] = None
    
    def _get_default_config(self) -> CICDConfig:
        """Get default CI/CD configuration"""
        return CICDConfig(
            provider=CICDProvider.INTERNAL,
            endpoint="http://internal-cicd.example.com/api",
            auth_token="mock-token",
            repository="powerhouse/platform",
            branch="main",
            workflow_file=".github/workflows/deploy.yml",
            additional_params={}
        )
    
    async def start(self):
        """Start deployment processor"""
        if self._running:
            logger.warning("CI/CD integrator already running")
            return
        
        self._running = True
        self._deployment_task = asyncio.create_task(self._process_deployment_queue())
        logger.info("CI/CD integrator started")
    
    async def stop(self):
        """Stop deployment processor"""
        self._running = False
        if self._deployment_task:
            self._deployment_task.cancel()
            try:
                await self._deployment_task
            except asyncio.CancelledError:
                pass
        logger.info("CI/CD integrator stopped")
    
    async def trigger_deployment(
        self,
        version_info: VersionInfo,
        policy_evaluation: PolicyEvaluation,
        triggered_by: str = "system"
    ) -> DeploymentTrigger:
        """Trigger a CI/CD deployment"""
        
        if policy_evaluation.decision != UpdateDecision.APPROVE:
            raise ValueError(f"Cannot trigger deployment - policy decision is {policy_evaluation.decision.value}")
        
        trigger_id = f"deploy_{self._trigger_counter}_{datetime.utcnow().timestamp()}"
        self._trigger_counter += 1
        
        # Create deployment configuration
        deployment_config = {
            "component": version_info.component,
            "version": version_info.version,
            "download_url": version_info.download_url,
            "checksum": version_info.checksum,
            "deployment_window": policy_evaluation.deployment_window,
            "rollback_enabled": True,
            "notifications_enabled": True
        }
        
        trigger = DeploymentTrigger(
            trigger_id=trigger_id,
            component=version_info.component,
            version=version_info.version,
            provider=self.config.provider,
            triggered_at=datetime.utcnow(),
            triggered_by=triggered_by,
            policy_evaluation=policy_evaluation,
            deployment_config=deployment_config
        )
        
        # Add to queue
        self.deployment_queue.append(trigger)
        
        logger.info(f"Deployment triggered: {trigger_id} for {version_info.component} v{version_info.version}")
        return trigger
    
    async def _process_deployment_queue(self):
        """Process deployment queue"""
        while self._running:
            try:
                if self.deployment_queue:
                    trigger = self.deployment_queue.pop(0)
                    await self._execute_deployment(trigger)
                else:
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error processing deployment queue: {e}")
                await asyncio.sleep(10)
    
    async def _execute_deployment(self, trigger: DeploymentTrigger):
        """Execute deployment via CI/CD"""
        result = DeploymentResult(
            trigger_id=trigger.trigger_id,
            component=trigger.component,
            version=trigger.version,
            status=DeploymentStatus.PENDING,
            started_at=datetime.utcnow(),
            completed_at=None,
            duration_seconds=0,
            pipeline_url="",
            logs_url=None,
            artifacts={},
            errors=[]
        )
        
        self.active_deployments[trigger.trigger_id] = result
        
        try:
            # Call CI/CD provider API
            if self.config.provider == CICDProvider.GITHUB_ACTIONS:
                await self._trigger_github_actions(trigger, result)
            elif self.config.provider == CICDProvider.GITLAB_CI:
                await self._trigger_gitlab_ci(trigger, result)
            elif self.config.provider == CICDProvider.JENKINS:
                await self._trigger_jenkins(trigger, result)
            elif self.config.provider == CICDProvider.CIRCLECI:
                await self._trigger_circleci(trigger, result)
            else:
                await self._trigger_internal_cicd(trigger, result)
            
            # Monitor deployment
            await self._monitor_deployment(trigger.trigger_id, result)
            
        except Exception as e:
            logger.error(f"Deployment {trigger.trigger_id} failed: {e}")
            result.status = DeploymentStatus.FAILED
            result.errors.append(str(e))
        finally:
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()
            
            # Move to completed
            self.active_deployments.pop(trigger.trigger_id, None)
            self.completed_deployments.append(result)
            
            # Keep only last 100
            if len(self.completed_deployments) > 100:
                self.completed_deployments = self.completed_deployments[-100:]
    
    async def _trigger_github_actions(
        self,
        trigger: DeploymentTrigger,
        result: DeploymentResult
    ):
        """Trigger GitHub Actions workflow"""
        url = f"https://api.github.com/repos/{self.config.repository}/actions/workflows/{self.config.workflow_file}/dispatches"
        
        headers = {
            "Authorization": f"token {self.config.auth_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        payload = {
            "ref": self.config.branch,
            "inputs": {
                "component": trigger.component,
                "version": trigger.version,
                "trigger_id": trigger.trigger_id,
                **trigger.deployment_config
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 204:
                    result.status = DeploymentStatus.QUEUED
                    result.pipeline_url = f"https://github.com/{self.config.repository}/actions"
                    logger.info(f"GitHub Actions workflow triggered for {trigger.trigger_id}")
                else:
                    raise Exception(f"GitHub Actions trigger failed: {response.status}")
    
    async def _trigger_gitlab_ci(
        self,
        trigger: DeploymentTrigger,
        result: DeploymentResult
    ):
        """Trigger GitLab CI pipeline"""
        # Simulate GitLab CI trigger
        await asyncio.sleep(0.5)
        result.status = DeploymentStatus.QUEUED
        result.pipeline_url = f"https://gitlab.com/{self.config.repository}/-/pipelines"
        logger.info(f"GitLab CI pipeline triggered for {trigger.trigger_id}")
    
    async def _trigger_jenkins(
        self,
        trigger: DeploymentTrigger,
        result: DeploymentResult
    ):
        """Trigger Jenkins build"""
        # Simulate Jenkins trigger
        await asyncio.sleep(0.5)
        result.status = DeploymentStatus.QUEUED
        result.pipeline_url = f"{self.config.endpoint}/job/{trigger.component}/build"
        logger.info(f"Jenkins build triggered for {trigger.trigger_id}")
    
    async def _trigger_circleci(
        self,
        trigger: DeploymentTrigger,
        result: DeploymentResult
    ):
        """Trigger CircleCI pipeline"""
        # Simulate CircleCI trigger
        await asyncio.sleep(0.5)
        result.status = DeploymentStatus.QUEUED
        result.pipeline_url = f"https://app.circleci.com/pipelines/github/{self.config.repository}"
        logger.info(f"CircleCI pipeline triggered for {trigger.trigger_id}")
    
    async def _trigger_internal_cicd(
        self,
        trigger: DeploymentTrigger,
        result: DeploymentResult
    ):
        """Trigger internal CI/CD system"""
        # Simulate internal CI/CD trigger
        await asyncio.sleep(0.5)
        result.status = DeploymentStatus.QUEUED
        result.pipeline_url = f"{self.config.endpoint}/deployments/{trigger.trigger_id}"
        logger.info(f"Internal CI/CD triggered for {trigger.trigger_id}")
    
    async def _monitor_deployment(self, trigger_id: str, result: DeploymentResult):
        """Monitor deployment progress"""
        result.status = DeploymentStatus.RUNNING
        
        # Simulate deployment monitoring
        for i in range(10):
            await asyncio.sleep(2)
            
            # Check status (in production, poll CI/CD API)
            if i >= 8:
                # Deployment complete
                result.status = DeploymentStatus.SUCCESS
                result.logs_url = f"{result.pipeline_url}/logs"
                result.artifacts["deployment_report"] = f"{result.pipeline_url}/artifacts"
                logger.info(f"Deployment {trigger_id} completed successfully")
                break
        
        if result.status == DeploymentStatus.RUNNING:
            result.status = DeploymentStatus.FAILED
            result.errors.append("Deployment timeout")
    
    async def cancel_deployment(self, trigger_id: str) -> bool:
        """Cancel an active deployment"""
        if trigger_id in self.active_deployments:
            result = self.active_deployments[trigger_id]
            result.status = DeploymentStatus.CANCELLED
            logger.info(f"Deployment {trigger_id} cancelled")
            return True
        
        # Remove from queue if pending
        initial_len = len(self.deployment_queue)
        self.deployment_queue = [
            t for t in self.deployment_queue
            if t.trigger_id != trigger_id
        ]
        
        return len(self.deployment_queue) < initial_len
    
    def get_deployment_status(self, trigger_id: str) -> Optional[DeploymentResult]:
        """Get deployment status"""
        if trigger_id in self.active_deployments:
            return self.active_deployments[trigger_id]
        
        for result in self.completed_deployments:
            if result.trigger_id == trigger_id:
                return result
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get CI/CD statistics"""
        total_completed = len(self.completed_deployments)
        successful = len([
            r for r in self.completed_deployments
            if r.status == DeploymentStatus.SUCCESS
        ])
        
        return {
            "provider": self.config.provider.value,
            "active_deployments": len(self.active_deployments),
            "queued_deployments": len(self.deployment_queue),
            "total_completed": total_completed,
            "successful": successful,
            "failed": total_completed - successful,
            "success_rate": successful / total_completed if total_completed > 0 else 0,
            "avg_duration_seconds": sum(
                r.duration_seconds for r in self.completed_deployments
            ) / total_completed if total_completed > 0 else 0
        }
