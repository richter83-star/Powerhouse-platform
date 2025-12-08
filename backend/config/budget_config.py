
"""
Budget and Rate Limiting Configuration for Auto Loop Agents
Prevents runaway costs from autonomous agents with daily spending limits
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

class BudgetLimits(BaseModel):
    """Daily budget limits for autonomous agents"""
    
    # Daily spending limits
    daily_max_dollars: float = Field(
        default=100.0,
        description="Maximum daily spending in dollars"
    )
    
    # Auto Loop Agent specific limits
    auto_loop_max_iterations: int = Field(
        default=50,
        description="Maximum iterations per day for auto loop agents"
    )
    auto_loop_max_concurrent: int = Field(
        default=3,
        description="Maximum concurrent auto loop agents"
    )
    auto_loop_iteration_cost: float = Field(
        default=0.25,
        description="Estimated cost per iteration in dollars"
    )
    
    # General rate limits
    max_llm_calls_per_hour: int = Field(
        default=1000,
        description="Maximum LLM API calls per hour"
    )
    max_llm_calls_per_day: int = Field(
        default=10000,
        description="Maximum LLM API calls per day"
    )
    
    # Cost tracking
    warning_threshold_percent: float = Field(
        default=75.0,
        description="Send warning when reaching this % of daily budget"
    )
    
    # Emergency stop
    emergency_stop_enabled: bool = Field(
        default=True,
        description="Automatically stop all auto loop agents when budget exceeded"
    )


class UsageTracker:
    """Track daily usage and costs"""
    
    def __init__(self, storage_path: str = "data/usage_tracking"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.usage_file = self.storage_path / "daily_usage.json"
        self.load_usage()
    
    def load_usage(self):
        """Load usage data from file"""
        if self.usage_file.exists():
            with open(self.usage_file, 'r') as f:
                data = json.load(f)
                self.current_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
                self.total_spent = data.get('total_spent', 0.0)
                self.llm_calls = data.get('llm_calls', 0)
                self.auto_loop_iterations = data.get('auto_loop_iterations', 0)
                self.agent_costs = data.get('agent_costs', {})
        else:
            self.reset_daily_usage()
    
    def save_usage(self):
        """Save usage data to file"""
        data = {
            'date': self.current_date,
            'total_spent': self.total_spent,
            'llm_calls': self.llm_calls,
            'auto_loop_iterations': self.auto_loop_iterations,
            'agent_costs': self.agent_costs,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.usage_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def reset_daily_usage(self):
        """Reset usage for a new day"""
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.total_spent = 0.0
        self.llm_calls = 0
        self.auto_loop_iterations = 0
        self.agent_costs = {}
        self.save_usage()
    
    def check_and_reset_if_new_day(self):
        """Check if it's a new day and reset if needed"""
        today = datetime.now().strftime('%Y-%m-%d')
        if today != self.current_date:
            self.reset_daily_usage()
    
    def record_cost(self, agent_name: str, cost: float, call_type: str = "llm"):
        """Record a cost"""
        self.check_and_reset_if_new_day()
        
        self.total_spent += cost
        if call_type == "llm":
            self.llm_calls += 1
        elif call_type == "auto_loop":
            self.auto_loop_iterations += 1
        
        # Track per-agent costs
        if agent_name not in self.agent_costs:
            self.agent_costs[agent_name] = 0.0
        self.agent_costs[agent_name] += cost
        
        self.save_usage()
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        self.check_and_reset_if_new_day()
        return {
            'date': self.current_date,
            'total_spent': round(self.total_spent, 2),
            'llm_calls': self.llm_calls,
            'auto_loop_iterations': self.auto_loop_iterations,
            'agent_costs': self.agent_costs
        }
    
    def check_budget_limit(self, limits: BudgetLimits) -> Dict:
        """
        Check if within budget limits
        
        Returns:
            Dict with 'allowed', 'reason', 'usage_percent', 'warning'
        """
        self.check_and_reset_if_new_day()
        
        usage_percent = (self.total_spent / limits.daily_max_dollars) * 100
        
        # Check if exceeded
        if self.total_spent >= limits.daily_max_dollars:
            return {
                'allowed': False,
                'reason': f'Daily budget limit reached (${self.total_spent:.2f} / ${limits.daily_max_dollars:.2f})',
                'usage_percent': usage_percent,
                'warning': True
            }
        
        # Check if approaching limit
        warning = usage_percent >= limits.warning_threshold_percent
        
        return {
            'allowed': True,
            'reason': 'Within budget',
            'usage_percent': round(usage_percent, 2),
            'warning': warning,
            'warning_message': f'Approaching budget limit ({usage_percent:.1f}% used)' if warning else None
        }
    
    def check_auto_loop_limit(self, limits: BudgetLimits) -> Dict:
        """
        Check if auto loop agent can run
        
        Returns:
            Dict with 'allowed' and 'reason'
        """
        self.check_and_reset_if_new_day()
        
        # Check iterations limit
        if self.auto_loop_iterations >= limits.auto_loop_max_iterations:
            return {
                'allowed': False,
                'reason': f'Auto loop iteration limit reached ({self.auto_loop_iterations} / {limits.auto_loop_max_iterations})'
            }
        
        # Check budget
        budget_check = self.check_budget_limit(limits)
        if not budget_check['allowed']:
            return {
                'allowed': False,
                'reason': budget_check['reason']
            }
        
        return {
            'allowed': True,
            'reason': 'Within limits'
        }


# Global instances
_budget_limits = BudgetLimits()
_usage_tracker = UsageTracker()


def get_budget_limits() -> BudgetLimits:
    """Get current budget limits"""
    return _budget_limits


def get_usage_tracker() -> UsageTracker:
    """Get usage tracker instance"""
    return _usage_tracker


def update_budget_limits(new_limits: Dict):
    """Update budget limits"""
    global _budget_limits
    _budget_limits = BudgetLimits(**new_limits)


def check_auto_loop_allowed() -> Dict:
    """
    Check if auto loop agent is allowed to run
    
    Returns:
        Dict with 'allowed', 'reason', and usage stats
    """
    limits = get_budget_limits()
    tracker = get_usage_tracker()
    
    # Check limits
    check = tracker.check_auto_loop_limit(limits)
    budget_check = tracker.check_budget_limit(limits)
    
    return {
        **check,
        'usage_stats': tracker.get_usage_stats(),
        'budget_status': budget_check
    }


def record_auto_loop_iteration(agent_name: str = "auto_loop"):
    """Record an auto loop iteration"""
    limits = get_budget_limits()
    tracker = get_usage_tracker()
    
    cost = limits.auto_loop_iteration_cost
    tracker.record_cost(agent_name, cost, "auto_loop")
    
    # Check if warning needed
    budget_check = tracker.check_budget_limit(limits)
    if budget_check.get('warning'):
        return {
            'recorded': True,
            'warning': True,
            'message': budget_check.get('warning_message')
        }
    
    return {
        'recorded': True,
        'warning': False
    }


def get_budget_dashboard() -> Dict:
    """
    Get budget dashboard data for frontend
    
    Returns:
        Dict with limits, usage, and status
    """
    limits = get_budget_limits()
    tracker = get_usage_tracker()
    budget_check = tracker.check_budget_limit(limits)
    usage_stats = tracker.get_usage_stats()
    
    return {
        'limits': {
            'daily_max_dollars': limits.daily_max_dollars,
            'auto_loop_max_iterations': limits.auto_loop_max_iterations,
            'auto_loop_max_concurrent': limits.auto_loop_max_concurrent,
            'max_llm_calls_per_hour': limits.max_llm_calls_per_hour,
            'max_llm_calls_per_day': limits.max_llm_calls_per_day,
            'warning_threshold_percent': limits.warning_threshold_percent,
        },
        'usage': usage_stats,
        'status': {
            'budget_remaining': round(limits.daily_max_dollars - usage_stats['total_spent'], 2),
            'usage_percent': budget_check['usage_percent'],
            'iterations_remaining': limits.auto_loop_max_iterations - usage_stats['auto_loop_iterations'],
            'warning': budget_check['warning'],
            'allowed': budget_check['allowed']
        },
        'emergency_stop_enabled': limits.emergency_stop_enabled
    }
