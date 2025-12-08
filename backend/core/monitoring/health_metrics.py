"""
Health and system metrics collection.
"""
import psutil
import logging
from typing import Dict, Any
from datetime import datetime

from core.monitoring.metrics import (
    system_cpu_usage,
    system_memory_usage,
    system_disk_usage
)

logger = logging.getLogger(__name__)


def collect_system_metrics() -> Dict[str, Any]:
    """
    Collect system metrics (CPU, memory, disk).
    
    Returns:
        Dictionary of system metrics
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_total = memory.total
        memory_used = memory.used
        memory_percent = memory.percent
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_total = disk.total
        disk_used = disk.used
        disk_percent = disk.percent
        
        # Update Prometheus metrics
        system_cpu_usage.set(cpu_percent)
        system_memory_usage.set(memory_used)
        system_disk_usage.labels(mount_point='/').set(disk_used)
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count
            },
            "memory": {
                "total_bytes": memory_total,
                "used_bytes": memory_used,
                "percent": memory_percent,
                "available_bytes": memory.available
            },
            "disk": {
                "total_bytes": disk_total,
                "used_bytes": disk_used,
                "percent": disk_percent,
                "free_bytes": disk.free
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def get_health_metrics() -> Dict[str, Any]:
    """
    Get comprehensive health metrics.
    
    Returns:
        Dictionary of health metrics
    """
    system_metrics = collect_system_metrics()
    
    return {
        "system": system_metrics,
        "timestamp": datetime.utcnow().isoformat()
    }

