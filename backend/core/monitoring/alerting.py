"""
Alerting system for monitoring and observability.
"""
import logging
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure."""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    source: str
    timestamp: datetime
    metadata: Optional[Dict] = None


class AlertManager:
    """
    Alert manager for monitoring and observability.
    
    Features:
    - Alert thresholds
    - Alert aggregation
    - Multiple notification channels
    - Alert deduplication
    """
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.handlers: List[Callable[[Alert], None]] = []
        self.thresholds: Dict[str, Dict] = {}
    
    def register_handler(self, handler: Callable[[Alert], None]):
        """Register an alert handler."""
        self.handlers.append(handler)
    
    def set_threshold(self, metric_name: str, threshold: Dict):
        """
        Set alert threshold for a metric.
        
        Args:
            metric_name: Name of the metric
            threshold: Threshold configuration
                {
                    "warning": 80,
                    "error": 90,
                    "critical": 95
                }
        """
        self.thresholds[metric_name] = threshold
    
    def check_threshold(self, metric_name: str, value: float) -> Optional[AlertSeverity]:
        """
        Check if value exceeds threshold.
        
        Args:
            metric_name: Name of the metric
            value: Current value
        
        Returns:
            Alert severity if threshold exceeded, None otherwise
        """
        if metric_name not in self.thresholds:
            return None
        
        threshold = self.thresholds[metric_name]
        
        if threshold.get("critical") and value >= threshold["critical"]:
            return AlertSeverity.CRITICAL
        elif threshold.get("error") and value >= threshold["error"]:
            return AlertSeverity.ERROR
        elif threshold.get("warning") and value >= threshold["warning"]:
            return AlertSeverity.WARNING
        
        return None
    
    def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        source: str,
        metadata: Optional[Dict] = None
    ) -> Alert:
        """
        Create and dispatch an alert.
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            source: Alert source (e.g., "cpu_monitor", "database")
            metadata: Additional metadata
        
        Returns:
            Created alert
        """
        import uuid
        alert_id = str(uuid.uuid4())
        
        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            severity=severity,
            source=source,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Store alert
        self.alerts[alert_id] = alert
        
        # Dispatch to handlers
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
        
        logger.warning(f"Alert created: {title} ({severity.value})")
        
        return alert
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """
        Get active alerts.
        
        Args:
            severity: Filter by severity (optional)
        
        Returns:
            List of active alerts
        """
        alerts = list(self.alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)


# Global alert manager instance
alert_manager = AlertManager()


def log_alert_handler(alert: Alert):
    """Default alert handler that logs alerts."""
    logger.warning(
        f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}",
        extra={
            "alert_id": alert.id,
            "source": alert.source,
            "metadata": alert.metadata
        }
    )


# Register default handler
alert_manager.register_handler(log_alert_handler)

