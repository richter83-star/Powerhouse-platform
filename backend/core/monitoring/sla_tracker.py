"""
SLA Monitoring & Reporting

Tracks uptime, response times, error rates, and SLA compliance.
Target: 99.9% uptime SLA
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class SLAStatus(str, Enum):
    """SLA compliance status"""
    COMPLIANT = "compliant"
    AT_RISK = "at_risk"
    BREACHED = "breached"


@dataclass
class SLAMetrics:
    """SLA metrics for a time period"""
    period_start: datetime
    period_end: datetime
    uptime_percentage: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float
    sla_target: float = 99.9
    sla_status: SLAStatus = SLAStatus.COMPLIANT


class SLATracker:
    """
    Tracks SLA metrics including uptime, response times, and error rates.
    
    Features:
    - Real-time uptime tracking
    - Response time monitoring (avg, p95, p99)
    - Error rate tracking
    - SLA breach detection
    - Historical reporting
    """
    
    def __init__(self, sla_target: float = 99.9):
        """
        Initialize SLA tracker.
        
        Args:
            sla_target: Target uptime percentage (default 99.9%)
        """
        self.sla_target = sla_target
        self.start_time = datetime.utcnow()
        
        # Request tracking (in-memory, should be backed by Redis/DB in production)
        self._request_times: deque = deque(maxlen=10000)  # Last 10k requests
        self._response_times: deque = deque(maxlen=10000)
        self._errors: deque = deque(maxlen=1000)  # Last 1k errors
        
        # Uptime tracking
        self._downtime_periods: List[Dict[str, datetime]] = []
        self._is_up: bool = True
        self._last_check: datetime = datetime.utcnow()
        
        # Service health
        self._service_health: Dict[str, bool] = defaultdict(lambda: True)
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
        error: Optional[str] = None
    ):
        """
        Record a request for SLA tracking.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
            error: Error message if request failed
        """
        timestamp = datetime.utcnow()
        
        self._request_times.append({
            "timestamp": timestamp,
            "endpoint": endpoint,
            "method": method,
            "response_time_ms": response_time_ms,
            "status_code": status_code,
            "error": error
        })
        
        self._response_times.append(response_time_ms)
        
        # Track errors
        if status_code >= 400 or error:
            self._errors.append({
                "timestamp": timestamp,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "error": error
            })
        
        # Update service health
        service_name = f"{method} {endpoint}"
        self._service_health[service_name] = status_code < 500
    
    def record_uptime_check(self, is_up: bool, service_name: str = "api"):
        """
        Record uptime check result.
        
        Args:
            is_up: Whether service is up
            service_name: Name of the service
        """
        now = datetime.utcnow()
        
        if not is_up and self._is_up:
            # Service went down
            self._downtime_periods.append({
                "start": now,
                "service": service_name
            })
            self._is_up = False
            logger.warning(f"Service {service_name} is DOWN at {now}")
        
        elif is_up and not self._is_up:
            # Service came back up
            if self._downtime_periods:
                self._downtime_periods[-1]["end"] = now
            self._is_up = True
            logger.info(f"Service {service_name} is UP at {now}")
        
        self._last_check = now
    
    def calculate_uptime(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> float:
        """
        Calculate uptime percentage for a time period.
        
        Args:
            start_date: Start of period (default: tracker start time)
            end_date: End of period (default: now)
            
        Returns:
            Uptime percentage (0-100)
        """
        if not start_date:
            start_date = self.start_time
        if not end_date:
            end_date = datetime.utcnow()
        
        total_time = (end_date - start_date).total_seconds()
        
        if total_time == 0:
            return 100.0
        
        # Calculate total downtime
        total_downtime = 0.0
        for period in self._downtime_periods:
            period_start = period.get("start", start_date)
            period_end = period.get("end", end_date)
            
            # Only count downtime within the requested period
            if period_start < end_date and (not period_end or period_end > start_date):
                period_start = max(period_start, start_date)
                period_end = min(period_end or end_date, end_date)
                total_downtime += (period_end - period_start).total_seconds()
        
        uptime_seconds = total_time - total_downtime
        uptime_percentage = (uptime_seconds / total_time) * 100
        
        return max(0.0, min(100.0, uptime_percentage))
    
    def calculate_response_time_metrics(self) -> Dict[str, float]:
        """
        Calculate response time metrics (avg, p95, p99).
        
        Returns:
            Dict with avg, p95, p99 response times in ms
        """
        if not self._response_times:
            return {
                "avg": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "min": 0.0,
                "max": 0.0
            }
        
        sorted_times = sorted(self._response_times)
        count = len(sorted_times)
        
        return {
            "avg": sum(sorted_times) / count,
            "p95": sorted_times[int(count * 0.95)] if count > 0 else 0.0,
            "p99": sorted_times[int(count * 0.99)] if count > 0 else 0.0,
            "min": sorted_times[0] if sorted_times else 0.0,
            "max": sorted_times[-1] if sorted_times else 0.0
        }
    
    def calculate_error_rate(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> float:
        """
        Calculate error rate for a time period.
        
        Args:
            start_date: Start of period
            end_date: End of period
            
        Returns:
            Error rate percentage (0-100)
        """
        if not start_date:
            start_date = self.start_time
        if not end_date:
            end_date = datetime.utcnow()
        
        # Filter requests in period
        period_requests = [
            r for r in self._request_times
            if start_date <= r["timestamp"] <= end_date
        ]
        
        if not period_requests:
            return 0.0
        
        error_count = sum(1 for r in period_requests if r["status_code"] >= 400)
        error_rate = (error_count / len(period_requests)) * 100
        
        return error_rate
    
    def get_sla_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> SLAMetrics:
        """
        Get comprehensive SLA metrics for a time period.
        
        Args:
            start_date: Start of period
            end_date: End of period
            
        Returns:
            SLAMetrics object
        """
        if not start_date:
            start_date = self.start_time
        if not end_date:
            end_date = datetime.utcnow()
        
        # Calculate metrics
        uptime = self.calculate_uptime(start_date, end_date)
        response_metrics = self.calculate_response_time_metrics()
        error_rate = self.calculate_error_rate(start_date, end_date)
        
        # Filter requests in period
        period_requests = [
            r for r in self._request_times
            if start_date <= r["timestamp"] <= end_date
        ]
        
        total_requests = len(period_requests)
        successful_requests = sum(1 for r in period_requests if r["status_code"] < 400)
        failed_requests = total_requests - successful_requests
        
        # Determine SLA status
        if uptime >= self.sla_target:
            sla_status = SLAStatus.COMPLIANT
        elif uptime >= self.sla_target - 0.5:  # Within 0.5% of target
            sla_status = SLAStatus.AT_RISK
        else:
            sla_status = SLAStatus.BREACHED
        
        return SLAMetrics(
            period_start=start_date,
            period_end=end_date,
            uptime_percentage=uptime,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time_ms=response_metrics["avg"],
            p95_response_time_ms=response_metrics["p95"],
            p99_response_time_ms=response_metrics["p99"],
            error_rate=error_rate,
            sla_target=self.sla_target,
            sla_status=sla_status
        )
    
    def check_sla_breach(self) -> Optional[Dict[str, Any]]:
        """
        Check if SLA is currently breached.
        
        Returns:
            Breach information if breached, None otherwise
        """
        metrics = self.get_sla_metrics()
        
        if metrics.sla_status == SLAStatus.BREACHED:
            return {
                "breached": True,
                "uptime": metrics.uptime_percentage,
                "target": metrics.sla_target,
                "gap": metrics.sla_target - metrics.uptime_percentage,
                "message": f"SLA breach: {metrics.uptime_percentage:.2f}% uptime (target: {metrics.sla_target}%)"
            }
        
        return None
    
    def get_service_health_summary(self) -> Dict[str, Any]:
        """Get summary of service health."""
        healthy_services = sum(1 for is_healthy in self._service_health.values() if is_healthy)
        total_services = len(self._service_health)
        
        return {
            "overall_health": "healthy" if self._is_up else "unhealthy",
            "is_up": self._is_up,
            "healthy_services": healthy_services,
            "total_services": total_services,
            "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 100.0,
            "last_check": self._last_check.isoformat(),
            "downtime_periods": len([p for p in self._downtime_periods if not p.get("end")])
        }


# Global SLA tracker instance
_sla_tracker: Optional[SLATracker] = None


def get_sla_tracker() -> SLATracker:
    """Get the global SLA tracker instance."""
    global _sla_tracker
    if _sla_tracker is None:
        _sla_tracker = SLATracker()
    return _sla_tracker

