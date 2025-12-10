"""
Prometheus metrics collection for monitoring and observability.
"""
import time
import logging
from typing import Optional, Dict, Any
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, REGISTRY
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)

# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
)

http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000, 1000000]
)

# Database Metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table']
)

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Idle database connections'
)

# Cache Metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['cache_type', 'operation']
)

# Business Metrics
workflows_started_total = Counter(
    'workflows_started_total',
    'Total workflows started',
    ['workflow_type', 'tenant_id']
)

workflows_completed_total = Counter(
    'workflows_completed_total',
    'Total workflows completed',
    ['workflow_type', 'status', 'tenant_id']
)

workflow_duration_seconds = Histogram(
    'workflow_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_type'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0]
)

agents_executed_total = Counter(
    'agents_executed_total',
    'Total agents executed',
    ['agent_type', 'status', 'tenant_id']
)

agent_execution_duration_seconds = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_type'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

# System Metrics
system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes'
)

system_disk_usage = Gauge(
    'system_disk_usage_bytes',
    'System disk usage in bytes',
    ['mount_point']
)

# Error Metrics
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

# Authentication Metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['method', 'status']
)

auth_failures_total = Counter(
    'auth_failures_total',
    'Total authentication failures',
    ['reason']
)

# Business Metrics - Tenant & Usage
tenant_active_users = Gauge(
    'tenant_active_users',
    'Number of active users per tenant',
    ['tenant_id']
)

tenant_workflows_active = Gauge(
    'tenant_workflows_active',
    'Number of active workflows per tenant',
    ['tenant_id']
)

tenant_api_usage_total = Counter(
    'tenant_api_usage_total',
    'Total API usage per tenant',
    ['tenant_id', 'endpoint']
)

tenant_cost_total = Counter(
    'tenant_cost_total',
    'Total cost per tenant (USD)',
    ['tenant_id']
)

# Business Metrics - Marketplace
marketplace_listings_total = Gauge(
    'marketplace_listings_total',
    'Total marketplace listings',
    ['category', 'status']
)

marketplace_purchases_total = Counter(
    'marketplace_purchases_total',
    'Total marketplace purchases',
    ['category', 'status']
)

marketplace_revenue_total = Counter(
    'marketplace_revenue_total',
    'Total marketplace revenue (USD)',
    ['category']
)

# Business Metrics - Subscriptions
subscriptions_active = Gauge(
    'subscriptions_active',
    'Number of active subscriptions',
    ['plan_id', 'status']
)

subscriptions_revenue_monthly = Gauge(
    'subscriptions_revenue_monthly',
    'Monthly recurring revenue (USD)',
    ['plan_id']
)

# Business Metrics - SLA
sla_uptime_percentage = Gauge(
    'sla_uptime_percentage',
    'SLA uptime percentage',
    ['tenant_id', 'period']
)

sla_response_time_p95 = Gauge(
    'sla_response_time_p95',
    'SLA 95th percentile response time (ms)',
    ['tenant_id']
)

sla_breaches_total = Counter(
    'sla_breaches_total',
    'Total SLA breaches',
    ['tenant_id', 'sla_type']
)


def track_request_metrics(func):
    """Decorator to track HTTP request metrics."""
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        method = request.method
        endpoint = request.url.path
        
        start_time = time.time()
        try:
            response = await func(request, *args, **kwargs)
            status_code = response.status_code
            
            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
        except Exception as e:
            # Record error
            errors_total.labels(
                error_type=type(e).__name__,
                endpoint=endpoint
            ).inc()
            raise
    
    return wrapper


def get_metrics() -> str:
    """
    Get Prometheus metrics in OpenMetrics format.
    
    Returns:
        Metrics in OpenMetrics format
    """
    return generate_latest(REGISTRY).decode('utf-8')


def get_metrics_content_type() -> str:
    """Get content type for metrics endpoint."""
    return CONTENT_TYPE_LATEST

