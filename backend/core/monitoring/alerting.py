"""
Alerting system for monitoring and observability.

Built-in notification handlers:
- ``log_alert_handler``          — always active; writes to Python logger
- ``SlackAlertHandler``          — POST to Slack Incoming Webhook URL
- ``EmailAlertHandler``          — send via SMTP or SendGrid

Wire additional handlers at startup:
    from core.monitoring.alerting import alert_manager, SlackAlertHandler
    alert_manager.register_handler(SlackAlertHandler(webhook_url="https://..."))
"""
import logging
import smtplib
from email.mime.text import MIMEText
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


# ---------------------------------------------------------------------------
# Slack notification handler
# ---------------------------------------------------------------------------

class SlackAlertHandler:
    """
    Sends alerts to a Slack channel via an Incoming Webhook URL.

    Args:
        webhook_url: Slack Incoming Webhook URL
            (``https://hooks.slack.com/services/...``).
        min_severity: Only send alerts at or above this severity.
            Defaults to ``AlertSeverity.ERROR``.
    """

    _SEVERITY_EMOJI = {
        AlertSeverity.INFO: ":information_source:",
        AlertSeverity.WARNING: ":warning:",
        AlertSeverity.ERROR: ":x:",
        AlertSeverity.CRITICAL: ":rotating_light:",
    }

    def __init__(self, webhook_url: str, min_severity: AlertSeverity = AlertSeverity.ERROR):
        self.webhook_url = webhook_url
        self.min_severity = min_severity

    def __call__(self, alert: Alert) -> None:
        _levels = [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL]
        if _levels.index(alert.severity) < _levels.index(self.min_severity):
            return
        try:
            import httpx
            emoji = self._SEVERITY_EMOJI.get(alert.severity, ":bell:")
            text = (
                f"{emoji} *[{alert.severity.value.upper()}]* {alert.title}\n"
                f">{alert.message}\n"
                f"_Source: {alert.source} | {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}_"
            )
            httpx.post(
                self.webhook_url,
                json={"text": text},
                timeout=5.0,
            )
        except Exception as exc:
            logger.warning("SlackAlertHandler failed: %s", exc)


# ---------------------------------------------------------------------------
# Email notification handler
# ---------------------------------------------------------------------------

class EmailAlertHandler:
    """
    Sends alert emails via SMTP.

    Uses ``settings.smtp_host`` / ``settings.smtp_port`` / credentials when
    available; falls back to a plain unauthenticated localhost relay if not.

    Args:
        recipient: Email address to send alerts to.
        min_severity: Only send alerts at or above this severity.
            Defaults to ``AlertSeverity.CRITICAL``.
    """

    def __init__(self, recipient: str, min_severity: AlertSeverity = AlertSeverity.CRITICAL):
        self.recipient = recipient
        self.min_severity = min_severity

    def __call__(self, alert: Alert) -> None:
        _levels = [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL]
        if _levels.index(alert.severity) < _levels.index(self.min_severity):
            return
        try:
            from config.settings import settings as _s
            smtp_host = getattr(_s, "smtp_host", "localhost")
            smtp_port = int(getattr(_s, "smtp_port", 587))
            smtp_user = getattr(_s, "smtp_user", None)
            smtp_pass = getattr(_s, "smtp_password", None)
            sender = getattr(_s, "email_from", "noreply@powerhouse.ai")

            subject = f"[{alert.severity.value.upper()}] Powerhouse Alert: {alert.title}"
            body = (
                f"Alert ID: {alert.id}\n"
                f"Severity: {alert.severity.value.upper()}\n"
                f"Source: {alert.source}\n"
                f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                f"{alert.message}\n\n"
                f"Metadata: {alert.metadata}"
            )
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = self.recipient

            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                if smtp_user and smtp_pass:
                    server.ehlo()
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                server.sendmail(sender, [self.recipient], msg.as_string())
        except Exception as exc:
            logger.warning("EmailAlertHandler failed: %s", exc)

