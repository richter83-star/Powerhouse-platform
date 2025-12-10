
"""
Usage Tracking and Billing
Tracks API usage, resource consumption, and generates billing data.
Includes real-time enforcement of usage limits.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class LimitType(str, Enum):
    """Type of usage limit"""
    HARD = "hard"  # Block when exceeded
    SOFT = "soft"  # Warn but allow


class LimitStatus:
    """Status of a usage limit check"""
    def __init__(
        self,
        allowed: bool,
        current: float,
        limit: float,
        percentage: float,
        limit_type: LimitType,
        message: Optional[str] = None
    ):
        self.allowed = allowed
        self.current = current
        self.limit = limit
        self.percentage = percentage
        self.limit_type = limit_type
        self.message = message or self._generate_message()
    
    def _generate_message(self) -> str:
        if self.percentage >= 100:
            return f"Limit exceeded: {self.current:.0f} / {self.limit:.0f}"
        elif self.percentage >= 95:
            return f"Critical: {self.percentage:.1f}% of limit used ({self.current:.0f} / {self.limit:.0f})"
        elif self.percentage >= 90:
            return f"Warning: {self.percentage:.1f}% of limit used ({self.current:.0f} / {self.limit:.0f})"
        elif self.percentage >= 80:
            return f"Approaching limit: {self.percentage:.1f}% used ({self.current:.0f} / {self.limit:.0f})"
        else:
            return f"Usage: {self.current:.0f} / {self.limit:.0f} ({self.percentage:.1f}%)"

@dataclass
class UsageRecord:
    """Single usage record"""
    tenant_id: str
    timestamp: datetime
    resource_type: str  # api_call, agent_execution, workflow_run, storage
    quantity: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UsageSummary:
    """Usage summary for a tenant over a period"""
    tenant_id: str
    start_date: datetime
    end_date: datetime
    api_calls: int = 0
    agent_executions: int = 0
    workflow_runs: int = 0
    storage_gb: float = 0.0
    compute_hours: float = 0.0
    total_cost: float = 0.0
    breakdown: Dict[str, float] = field(default_factory=dict)

class UsageTracker:
    """
    Tracks resource usage and generates billing data.
    Includes real-time enforcement of usage limits.
    """
    
    def __init__(self):
        self._usage_records: List[UsageRecord] = []
        self._pricing = {
            "api_call": 0.001,  # $0.001 per call
            "agent_execution": 0.01,  # $0.01 per execution
            "workflow_run": 0.05,  # $0.05 per run
            "storage_gb": 0.10,  # $0.10 per GB per month
            "compute_hour": 1.00  # $1.00 per hour
        }
        
        # Real-time usage counters (in-memory, should be backed by Redis in production)
        self._current_usage: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._usage_windows: Dict[str, Dict[str, datetime]] = defaultdict(dict)  # For time-windowed limits
    
    def record_usage(
        self,
        tenant_id: str,
        resource_type: str,
        quantity: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        sync_to_stripe: bool = False,
        stripe_customer_id: Optional[str] = None,
        stripe_meter_ids: Optional[Dict[str, str]] = None
    ) -> UsageRecord:
        """
        Record a usage event.
        
        Args:
            tenant_id: Tenant ID
            resource_type: Type of resource (api_call, agent_execution, etc.)
            quantity: Usage quantity
            metadata: Additional metadata
            sync_to_stripe: If True, sync to Stripe Meter
            stripe_customer_id: Stripe customer ID for syncing
            stripe_meter_ids: Dict mapping resource_type to Stripe meter_id
        """
        record = UsageRecord(
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            resource_type=resource_type,
            quantity=quantity,
            metadata=metadata or {}
        )
        self._usage_records.append(record)
        
        # Sync to Stripe if configured
        if sync_to_stripe and stripe_customer_id and stripe_meter_ids:
            meter_id = stripe_meter_ids.get(resource_type)
            if meter_id:
                try:
                    from core.commercial.stripe_service import get_stripe_service
                    stripe_service = get_stripe_service()
                    stripe_service.record_usage_event(
                        meter_id=meter_id,
                        identifier=stripe_customer_id,
                        value=quantity,
                        timestamp=int(record.timestamp.timestamp())
                    )
                    logger.debug(f"Synced usage to Stripe: {resource_type} = {quantity}")
                except Exception as e:
                    logger.warning(f"Failed to sync usage to Stripe: {e}")
        
        return record
    
    def get_usage_summary(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UsageSummary:
        """Get usage summary for a tenant"""
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Filter records for this tenant and time period
        records = [
            r for r in self._usage_records
            if r.tenant_id == tenant_id
            and start_date <= r.timestamp <= end_date
        ]
        
        # Aggregate usage
        summary = UsageSummary(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        for record in records:
            if record.resource_type == "api_call":
                summary.api_calls += int(record.quantity)
            elif record.resource_type == "agent_execution":
                summary.agent_executions += int(record.quantity)
            elif record.resource_type == "workflow_run":
                summary.workflow_runs += int(record.quantity)
            elif record.resource_type == "storage_gb":
                summary.storage_gb = max(summary.storage_gb, record.quantity)
            elif record.resource_type == "compute_hour":
                summary.compute_hours += record.quantity
            
            # Calculate cost
            cost = record.quantity * self._pricing.get(record.resource_type, 0)
            summary.total_cost += cost
            summary.breakdown[record.resource_type] = summary.breakdown.get(record.resource_type, 0) + cost
        
        return summary
    
    def get_current_month_usage(self, tenant_id: str) -> UsageSummary:
        """Get current month usage for a tenant"""
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        return self.get_usage_summary(tenant_id, start_of_month, now)
    
    def get_usage_trends(
        self,
        tenant_id: str,
        months: int = 6
    ) -> List[UsageSummary]:
        """Get usage trends over multiple months"""
        trends = []
        now = datetime.utcnow()
        
        for i in range(months):
            month_date = now - timedelta(days=30 * i)
            start_of_month = datetime(month_date.year, month_date.month, 1)
            
            if month_date.month == 12:
                end_of_month = datetime(month_date.year + 1, 1, 1) - timedelta(seconds=1)
            else:
                end_of_month = datetime(month_date.year, month_date.month + 1, 1) - timedelta(seconds=1)
            
            summary = self.get_usage_summary(tenant_id, start_of_month, end_of_month)
            trends.insert(0, summary)
        
        return trends
    
    def get_all_tenants_usage(self, start_date: datetime, end_date: datetime) -> Dict[str, UsageSummary]:
        """Get usage summary for all tenants"""
        tenant_ids = set(r.tenant_id for r in self._usage_records)
        return {
            tenant_id: self.get_usage_summary(tenant_id, start_date, end_date)
            for tenant_id in tenant_ids
        }
    
    def estimate_monthly_bill(self, tenant_id: str) -> Dict[str, Any]:
        """Estimate monthly bill based on current usage trends"""
        current_month = self.get_current_month_usage(tenant_id)
        now = datetime.utcnow()
        days_elapsed = now.day
        days_in_month = 30  # simplified
        
        projected_cost = (current_month.total_cost / days_elapsed) * days_in_month if days_elapsed > 0 else 0
        
        return {
            "tenant_id": tenant_id,
            "current_month_cost": current_month.total_cost,
            "projected_month_cost": projected_cost,
            "days_elapsed": days_elapsed,
            "breakdown": current_month.breakdown
        }
    
    def check_limit(
        self,
        tenant_id: str,
        resource_type: str,
        quantity: float = 1.0,
        limit: Optional[float] = None,
        window_seconds: Optional[int] = None,
        limit_type: LimitType = LimitType.HARD
    ) -> LimitStatus:
        """
        Check if usage is within limits before allowing operation.
        
        Args:
            tenant_id: Tenant ID
            resource_type: Type of resource (api_call, agent_execution, etc.)
            quantity: Quantity to check
            limit: Usage limit (if None, will check tenant tier limits)
            window_seconds: Time window for limit (e.g., 3600 for hourly)
            limit_type: Hard (block) or soft (warn) limit
            
        Returns:
            LimitStatus indicating if operation is allowed
        """
        # Get current usage
        if window_seconds:
            # Time-windowed limit (e.g., per hour)
            now = datetime.utcnow()
            window_key = f"{resource_type}_{window_seconds}"
            
            # Clean old windows
            if window_key in self._usage_windows[tenant_id]:
                window_start = self._usage_windows[tenant_id][window_key]
                if (now - window_start).total_seconds() > window_seconds:
                    # Reset window
                    self._current_usage[tenant_id][window_key] = 0.0
                    self._usage_windows[tenant_id][window_key] = now
            
            # Initialize window if needed
            if window_key not in self._usage_windows[tenant_id]:
                self._usage_windows[tenant_id][window_key] = now
                self._current_usage[tenant_id][window_key] = 0.0
            
            current = self._current_usage[tenant_id][window_key]
        else:
            # Monthly limit
            current_month = self.get_current_month_usage(tenant_id)
            if resource_type == "api_call":
                current = current_month.api_calls
            elif resource_type == "agent_execution":
                current = current_month.agent_executions
            elif resource_type == "workflow_run":
                current = current_month.workflow_runs
            elif resource_type == "storage_gb":
                current = current_month.storage_gb
            else:
                current = 0.0
        
        # Get limit from tenant tier if not provided
        if limit is None:
            try:
                from core.commercial.tenant_manager import TenantManager, TenantTier
                tenant_manager = TenantManager()
                tenant = tenant_manager.get_tenant(tenant_id)
                
                if tenant:
                    if resource_type == "api_call":
                        limit = tenant.max_api_calls_per_hour if window_seconds == 3600 else tenant.max_api_calls_per_hour * 24 * 30
                    elif resource_type == "agent_execution":
                        limit = tenant.max_agents * 100  # Estimate
                    elif resource_type == "workflow_run":
                        limit = tenant.max_workflows * 10  # Estimate
                    elif resource_type == "storage_gb":
                        limit = tenant.storage_limit_gb
                    else:
                        limit = float('inf')  # No limit
                else:
                    limit = float('inf')  # No tenant = no limit
            except Exception as e:
                logger.warning(f"Failed to get tenant limits: {e}")
                limit = float('inf')
        
        # Check limit
        new_usage = current + quantity
        percentage = (new_usage / limit * 100) if limit > 0 else 0
        
        if limit_type == LimitType.HARD:
            allowed = new_usage <= limit
        else:
            # Soft limit: always allow, but warn
            allowed = True
        
        return LimitStatus(
            allowed=allowed,
            current=new_usage,
            limit=limit,
            percentage=percentage,
            limit_type=limit_type
        )
    
    def record_usage_with_limit_check(
        self,
        tenant_id: str,
        resource_type: str,
        quantity: float = 1.0,
        limit: Optional[float] = None,
        window_seconds: Optional[int] = None,
        limit_type: LimitType = LimitType.HARD,
        metadata: Optional[Dict[str, Any]] = None,
        sync_to_stripe: bool = False,
        stripe_customer_id: Optional[str] = None,
        stripe_meter_ids: Optional[Dict[str, str]] = None
    ) -> Tuple[UsageRecord, LimitStatus]:
        """
        Check limit and record usage if allowed.
        
        Returns:
            Tuple of (UsageRecord, LimitStatus)
            
        Raises:
            ValueError: If hard limit is exceeded
        """
        # Check limit first
        limit_status = self.check_limit(
            tenant_id=tenant_id,
            resource_type=resource_type,
            quantity=quantity,
            limit=limit,
            window_seconds=window_seconds,
            limit_type=limit_type
        )
        
        # Enforce hard limits
        if limit_type == LimitType.HARD and not limit_status.allowed:
            raise ValueError(f"Usage limit exceeded: {limit_status.message}")
        
        # Record usage
        record = self.record_usage(
            tenant_id=tenant_id,
            resource_type=resource_type,
            quantity=quantity,
            metadata=metadata,
            sync_to_stripe=sync_to_stripe,
            stripe_customer_id=stripe_customer_id,
            stripe_meter_ids=stripe_meter_ids
        )
        
        # Update real-time counter
        if window_seconds:
            window_key = f"{resource_type}_{window_seconds}"
            self._current_usage[tenant_id][window_key] += quantity
        
        return record, limit_status
    
    def get_current_usage_status(
        self,
        tenant_id: str,
        resource_types: Optional[List[str]] = None
    ) -> Dict[str, LimitStatus]:
        """
        Get current usage status for all resource types.
        
        Returns:
            Dict mapping resource_type to LimitStatus
        """
        if resource_types is None:
            resource_types = ["api_call", "agent_execution", "workflow_run", "storage_gb"]
        
        statuses = {}
        for resource_type in resource_types:
            try:
                limit_status = self.check_limit(
                    tenant_id=tenant_id,
                    resource_type=resource_type,
                    quantity=0,  # Just check current, don't add
                    limit_type=LimitType.SOFT  # Don't block, just report
                )
                statuses[resource_type] = limit_status
            except Exception as e:
                logger.warning(f"Failed to get usage status for {resource_type}: {e}")
        
        return statuses
    
    def get_usage_projections(
        self,
        tenant_id: str,
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """
        Project future usage based on current trends.
        
        Returns:
            Dict with projections for each resource type
        """
        current_month = self.get_current_month_usage(tenant_id)
        now = datetime.utcnow()
        days_elapsed = now.day
        days_in_month = 30
        
        if days_elapsed == 0:
            return {
                "projected_api_calls": 0,
                "projected_agent_executions": 0,
                "projected_workflow_runs": 0,
                "projected_storage_gb": 0,
                "projected_cost": 0
            }
        
        # Calculate daily averages
        daily_api_calls = current_month.api_calls / days_elapsed
        daily_agent_executions = current_month.agent_executions / days_elapsed
        daily_workflow_runs = current_month.workflow_runs / days_elapsed
        daily_cost = current_month.total_cost / days_elapsed
        
        # Project for specified days
        projected = {
            "projected_api_calls": int(daily_api_calls * days_ahead),
            "projected_agent_executions": int(daily_agent_executions * days_ahead),
            "projected_workflow_runs": int(daily_workflow_runs * days_ahead),
            "projected_storage_gb": current_month.storage_gb,  # Storage doesn't scale linearly
            "projected_cost": daily_cost * days_ahead,
            "current_daily_average": {
                "api_calls": daily_api_calls,
                "agent_executions": daily_agent_executions,
                "workflow_runs": daily_workflow_runs,
                "cost": daily_cost
            }
        }
        
        return projected

# Singleton instance
_usage_tracker = UsageTracker()

def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance"""
    return _usage_tracker
