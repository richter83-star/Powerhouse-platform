
"""
Version Detector - Monitors for New Versions and Updates
=====================================================

Detects available updates from various sources including:
- Git repositories
- Package registries
- Container registries
- Internal artifact repositories
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class UpdateSource(Enum):
    """Sources for update detection"""
    GIT_REPOSITORY = "git"
    PACKAGE_REGISTRY = "package"
    CONTAINER_REGISTRY = "container"
    ARTIFACT_REPOSITORY = "artifact"
    API_ENDPOINT = "api"


class UpdatePriority(Enum):
    """Priority levels for updates"""
    CRITICAL = "critical"  # Security patches, critical bugs
    HIGH = "high"  # Important features, performance improvements
    MEDIUM = "medium"  # Regular updates
    LOW = "low"  # Minor updates, cosmetic changes


@dataclass
class VersionInfo:
    """Version information"""
    version: str
    component: str
    source: UpdateSource
    priority: UpdatePriority
    release_date: datetime
    changelog: str
    download_url: str
    checksum: str
    dependencies: List[str]
    breaking_changes: bool
    metadata: Dict[str, Any]


@dataclass
class VersionComparison:
    """Comparison between current and available version"""
    current_version: str
    available_version: str
    component: str
    is_update_available: bool
    version_distance: int  # Number of versions behind
    priority: UpdatePriority
    recommendation: str


class VersionDetector:
    """Detects and tracks available updates"""
    
    def __init__(
        self,
        check_interval: int = 3600,  # 1 hour
        sources: Optional[List[UpdateSource]] = None
    ):
        self.check_interval = check_interval
        self.sources = sources or [
            UpdateSource.GIT_REPOSITORY,
            UpdateSource.PACKAGE_REGISTRY,
            UpdateSource.ARTIFACT_REPOSITORY
        ]
        
        self.current_versions: Dict[str, str] = {}
        self.available_versions: Dict[str, List[VersionInfo]] = {}
        self.last_check: Optional[datetime] = None
        self.version_history: List[Dict[str, Any]] = []
        
        self._running = False
        self._check_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start version detection"""
        if self._running:
            logger.warning("Version detector already running")
            return
        
        self._running = True
        self._check_task = asyncio.create_task(self._check_loop())
        logger.info("Version detector started")
    
    async def stop(self):
        """Stop version detection"""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info("Version detector stopped")
    
    async def _check_loop(self):
        """Main loop for checking versions"""
        while self._running:
            try:
                await self.check_for_updates()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in version check loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def check_for_updates(self) -> Dict[str, List[VersionInfo]]:
        """Check all sources for updates"""
        logger.info("Checking for updates...")
        
        updates = {}
        for source in self.sources:
            try:
                source_updates = await self._check_source(source)
                updates.update(source_updates)
            except Exception as e:
                logger.error(f"Error checking source {source}: {e}")
        
        self.available_versions = updates
        self.last_check = datetime.utcnow()
        
        # Log version check history
        self.version_history.append({
            "timestamp": self.last_check.isoformat(),
            "updates_found": len(updates),
            "components": list(updates.keys())
        })
        
        logger.info(f"Found {len(updates)} components with updates")
        return updates
    
    async def _check_source(self, source: UpdateSource) -> Dict[str, List[VersionInfo]]:
        """Check a specific source for updates"""
        if source == UpdateSource.GIT_REPOSITORY:
            return await self._check_git_repository()
        elif source == UpdateSource.PACKAGE_REGISTRY:
            return await self._check_package_registry()
        elif source == UpdateSource.CONTAINER_REGISTRY:
            return await self._check_container_registry()
        elif source == UpdateSource.ARTIFACT_REPOSITORY:
            return await self._check_artifact_repository()
        elif source == UpdateSource.API_ENDPOINT:
            return await self._check_api_endpoint()
        else:
            return {}
    
    async def _check_git_repository(self) -> Dict[str, List[VersionInfo]]:
        """Check Git repository for updates"""
        # Simulate checking Git tags/releases
        # In production, use GitPython or API calls
        
        await asyncio.sleep(0.1)  # Simulate network delay
        
        return {
            "core_orchestrator": [
                VersionInfo(
                    version="2.1.0",
                    component="core_orchestrator",
                    source=UpdateSource.GIT_REPOSITORY,
                    priority=UpdatePriority.HIGH,
                    release_date=datetime.utcnow(),
                    changelog="Performance improvements and bug fixes",
                    download_url="https://github.com/org/repo/releases/tag/v2.1.0",
                    checksum="abc123def456",
                    dependencies=["python>=3.8"],
                    breaking_changes=False,
                    metadata={"author": "dev-team"}
                )
            ]
        }
    
    async def _check_package_registry(self) -> Dict[str, List[VersionInfo]]:
        """Check package registry (PyPI, npm, etc.) for updates"""
        # Simulate checking package registry
        await asyncio.sleep(0.1)
        
        return {
            "performance_monitor": [
                VersionInfo(
                    version="1.5.0",
                    component="performance_monitor",
                    source=UpdateSource.PACKAGE_REGISTRY,
                    priority=UpdatePriority.MEDIUM,
                    release_date=datetime.utcnow(),
                    changelog="Added new metrics and improved alerting",
                    download_url="https://pypi.org/project/performance-monitor/1.5.0/",
                    checksum="def789ghi012",
                    dependencies=["numpy>=1.20"],
                    breaking_changes=False,
                    metadata={"downloads": 1000}
                )
            ]
        }
    
    async def _check_container_registry(self) -> Dict[str, List[VersionInfo]]:
        """Check container registry for image updates"""
        await asyncio.sleep(0.1)
        
        return {}
    
    async def _check_artifact_repository(self) -> Dict[str, List[VersionInfo]]:
        """Check internal artifact repository"""
        await asyncio.sleep(0.1)
        
        return {
            "dynamic_config_manager": [
                VersionInfo(
                    version="1.3.0",
                    component="dynamic_config_manager",
                    source=UpdateSource.ARTIFACT_REPOSITORY,
                    priority=UpdatePriority.MEDIUM,
                    release_date=datetime.utcnow(),
                    changelog="Enhanced configuration validation",
                    download_url="https://artifacts.internal/config-manager/1.3.0",
                    checksum="ghi345jkl678",
                    dependencies=[],
                    breaking_changes=False,
                    metadata={"internal": True}
                )
            ]
        }
    
    async def _check_api_endpoint(self) -> Dict[str, List[VersionInfo]]:
        """Check API endpoint for version information"""
        await asyncio.sleep(0.1)
        
        return {}
    
    def register_current_version(self, component: str, version: str):
        """Register current version of a component"""
        self.current_versions[component] = version
        logger.info(f"Registered {component} version {version}")
    
    def compare_versions(self, component: str) -> Optional[VersionComparison]:
        """Compare current and available versions"""
        if component not in self.current_versions:
            logger.warning(f"No current version registered for {component}")
            return None
        
        if component not in self.available_versions:
            return VersionComparison(
                current_version=self.current_versions[component],
                available_version=self.current_versions[component],
                component=component,
                is_update_available=False,
                version_distance=0,
                priority=UpdatePriority.LOW,
                recommendation="No updates available"
            )
        
        current = self.current_versions[component]
        available_list = self.available_versions[component]
        
        if not available_list:
            return None
        
        # Get latest version
        latest = max(available_list, key=lambda v: v.version)
        
        # Simple version comparison (in production, use semver)
        is_update_available = latest.version > current
        version_distance = self._calculate_version_distance(current, latest.version)
        
        recommendation = self._generate_recommendation(
            is_update_available,
            version_distance,
            latest.priority,
            latest.breaking_changes
        )
        
        return VersionComparison(
            current_version=current,
            available_version=latest.version,
            component=component,
            is_update_available=is_update_available,
            version_distance=version_distance,
            priority=latest.priority,
            recommendation=recommendation
        )
    
    def _calculate_version_distance(self, current: str, latest: str) -> int:
        """Calculate distance between versions"""
        # Simple implementation - count version number differences
        try:
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            
            distance = 0
            for c, l in zip(current_parts, latest_parts):
                if l > c:
                    distance += (l - c)
            
            return distance
        except:
            return 0
    
    def _generate_recommendation(
        self,
        is_update_available: bool,
        version_distance: int,
        priority: UpdatePriority,
        breaking_changes: bool
    ) -> str:
        """Generate update recommendation"""
        if not is_update_available:
            return "Component is up to date"
        
        if priority == UpdatePriority.CRITICAL:
            return "URGENT: Update immediately - critical security/bug fix"
        
        if breaking_changes:
            return "Update available with breaking changes - review before updating"
        
        if version_distance > 5:
            return "Multiple versions behind - consider updating soon"
        
        if priority == UpdatePriority.HIGH:
            return "Important update available - recommended to update"
        
        return "Update available - consider updating when convenient"
    
    def get_all_comparisons(self) -> List[VersionComparison]:
        """Get comparisons for all components"""
        comparisons = []
        for component in self.current_versions.keys():
            comparison = self.compare_versions(component)
            if comparison:
                comparisons.append(comparison)
        return comparisons
    
    def get_critical_updates(self) -> List[VersionComparison]:
        """Get only critical updates"""
        all_comparisons = self.get_all_comparisons()
        return [
            c for c in all_comparisons
            if c.is_update_available and c.priority == UpdatePriority.CRITICAL
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get version detection statistics"""
        return {
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "registered_components": len(self.current_versions),
            "components_with_updates": len(self.available_versions),
            "total_checks": len(self.version_history),
            "sources": [s.value for s in self.sources]
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export detector state"""
        return {
            "current_versions": self.current_versions,
            "available_versions": {
                k: [asdict(v) for v in versions]
                for k, versions in self.available_versions.items()
            },
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "version_history": self.version_history[-10:],  # Last 10 checks
            "statistics": self.get_statistics()
        }
