
"""
Health Checks and Readiness Probes
Comprehensive health monitoring for production deployments.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import asyncio
import psutil
import time

class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheck:
    """Comprehensive health check system"""
    
    def __init__(self):
        self._checks: Dict[str, callable] = {}
        self._last_check_time: Optional[datetime] = None
        self._last_results: Dict[str, Any] = {}
        
        # Register default checks
        self.register_check("system", self._check_system)
        self.register_check("memory", self._check_memory)
        self.register_check("disk", self._check_disk)
    
    def register_check(self, name: str, check_func: callable) -> None:
        """Register a custom health check"""
        self._checks[name] = check_func
    
    async def _check_system(self) -> Dict[str, Any]:
        """Check system resources"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        return {
            "status": HealthStatus.HEALTHY if cpu_percent < 80 else HealthStatus.DEGRADED,
            "cpu_percent": cpu_percent,
            "cpu_count": psutil.cpu_count()
        }
    
    async def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        memory = psutil.virtual_memory()
        status = HealthStatus.HEALTHY
        if memory.percent > 90:
            status = HealthStatus.UNHEALTHY
        elif memory.percent > 75:
            status = HealthStatus.DEGRADED
        
        return {
            "status": status,
            "percent": memory.percent,
            "available_gb": memory.available / (1024 ** 3),
            "total_gb": memory.total / (1024 ** 3)
        }
    
    async def _check_disk(self) -> Dict[str, Any]:
        """Check disk usage"""
        disk = psutil.disk_usage('/')
        status = HealthStatus.HEALTHY
        if disk.percent > 90:
            status = HealthStatus.UNHEALTHY
        elif disk.percent > 80:
            status = HealthStatus.DEGRADED
        
        return {
            "status": status,
            "percent": disk.percent,
            "free_gb": disk.free / (1024 ** 3),
            "total_gb": disk.total / (1024 ** 3)
        }
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for name, check_func in self._checks.items():
            try:
                result = await check_func()
                results[name] = result
                
                # Determine overall status
                check_status = result.get("status", HealthStatus.HEALTHY)
                if check_status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif check_status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
            except Exception as e:
                results[name] = {
                    "status": HealthStatus.UNHEALTHY,
                    "error": str(e)
                }
                overall_status = HealthStatus.UNHEALTHY
        
        self._last_check_time = datetime.utcnow()
        self._last_results = results
        
        return {
            "status": overall_status,
            "timestamp": self._last_check_time.isoformat(),
            "checks": results
        }
    
    async def get_readiness(self) -> Dict[str, Any]:
        """Check if system is ready to serve traffic"""
        # For now, readiness is same as health
        # In production, you might check additional dependencies
        health = await self.run_checks()
        return {
            "ready": health["status"] == HealthStatus.HEALTHY,
            "health": health
        }
    
    async def get_liveness(self) -> Dict[str, Any]:
        """Check if system is alive (for k8s liveness probes)"""
        return {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.process_time()
        }

# Singleton instance
_health_check = HealthCheck()

def get_health_check() -> HealthCheck:
    """Get the global health check instance"""
    return _health_check
