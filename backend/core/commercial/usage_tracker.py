
"""
Usage Tracking and Billing
Tracks API usage, resource consumption, and generates billing data.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio

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
    """Tracks resource usage and generates billing data"""
    
    def __init__(self):
        self._usage_records: List[UsageRecord] = []
        self._pricing = {
            "api_call": 0.001,  # $0.001 per call
            "agent_execution": 0.01,  # $0.01 per execution
            "workflow_run": 0.05,  # $0.05 per run
            "storage_gb": 0.10,  # $0.10 per GB per month
            "compute_hour": 1.00  # $1.00 per hour
        }
    
    def record_usage(
        self,
        tenant_id: str,
        resource_type: str,
        quantity: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageRecord:
        """Record a usage event"""
        record = UsageRecord(
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            resource_type=resource_type,
            quantity=quantity,
            metadata=metadata or {}
        )
        self._usage_records.append(record)
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

# Singleton instance
_usage_tracker = UsageTracker()

def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance"""
    return _usage_tracker
