
"""
OpenTelemetry Instrumentation
Provides distributed tracing, metrics, and observability for the multi-agent platform.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class Span:
    """
    Simplified span for distributed tracing.
    Compatible with OpenTelemetry concepts but self-contained.
    """
    
    def __init__(
        self,
        name: str,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str] = None
    ):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {}
        self.events: list = []
        self.status = "OK"
        self.error: Optional[str] = None
    
    def set_attribute(self, key: str, value: Any):
        """Set a span attribute"""
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to the span"""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        })
    
    def set_status(self, status: str, error: Optional[str] = None):
        """Set span status"""
        self.status = status
        self.error = error
    
    def end(self):
        """End the span"""
        self.end_time = time.time()
    
    def duration_ms(self) -> float:
        """Get span duration in milliseconds"""
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms(),
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status,
            "error": self.error
        }


class Tracer:
    """
    Distributed tracing manager.
    Tracks request flows across agents and services.
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.spans: Dict[str, Span] = {}
        self.active_spans: Dict[str, str] = {}  # thread_id -> span_id
        self._lock = threading.Lock()
        self._span_counter = 0
    
    def _generate_span_id(self) -> str:
        """Generate unique span ID"""
        with self._lock:
            self._span_counter += 1
            return f"{self.service_name}_{self._span_counter}_{int(time.time() * 1000000)}"
    
    def start_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Span:
        """
        Start a new span.
        
        Args:
            name: Span name
            trace_id: Trace ID (generated if not provided)
            parent_span_id: Parent span ID
            attributes: Initial attributes
            
        Returns:
            New span
        """
        if trace_id is None:
            trace_id = f"trace_{int(time.time() * 1000000)}"
        
        span_id = self._generate_span_id()
        
        span = Span(
            name=name,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id
        )
        
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        span.set_attribute("service.name", self.service_name)
        
        with self._lock:
            self.spans[span_id] = span
            thread_id = str(threading.get_ident())
            self.active_spans[thread_id] = span_id
        
        logger.debug(f"Started span: {name} (trace_id={trace_id}, span_id={span_id})")
        return span
    
    def end_span(self, span: Span):
        """End a span"""
        span.end()
        
        thread_id = str(threading.get_ident())
        with self._lock:
            if thread_id in self.active_spans:
                if self.active_spans[thread_id] == span.span_id:
                    del self.active_spans[thread_id]
        
        logger.debug(f"Ended span: {span.name} (duration={span.duration_ms():.2f}ms)")
    
    def get_active_span(self) -> Optional[Span]:
        """Get the currently active span for this thread"""
        thread_id = str(threading.get_ident())
        with self._lock:
            span_id = self.active_spans.get(thread_id)
            return self.spans.get(span_id) if span_id else None
    
    def get_spans_by_trace(self, trace_id: str) -> list:
        """Get all spans for a trace ID"""
        with self._lock:
            return [
                span.to_dict() for span in self.spans.values()
                if span.trace_id == trace_id
            ]
    
    def clear_old_spans(self, max_age_seconds: float = 3600):
        """Clear spans older than max_age_seconds"""
        now = time.time()
        with self._lock:
            to_remove = [
                span_id for span_id, span in self.spans.items()
                if span.end_time and (now - span.end_time) > max_age_seconds
            ]
            for span_id in to_remove:
                del self.spans[span_id]
        
        if to_remove:
            logger.info(f"Cleared {len(to_remove)} old spans")


class MetricsCollector:
    """
    Metrics collection for system observability.
    Tracks counters, gauges, and histograms.
    """
    
    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
    
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        key = self._make_key(name, labels)
        with self._lock:
            self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        key = self._make_key(name, labels)
        with self._lock:
            self.gauges[key] = value
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram value"""
        key = self._make_key(name, labels)
        with self._lock:
            self.histograms[key].append(value)
            # Keep only last 1000 values to prevent memory issues
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create metric key with labels"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        with self._lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {
                    name: {
                        "count": len(values),
                        "sum": sum(values),
                        "avg": sum(values) / len(values) if values else 0,
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0
                    }
                    for name, values in self.histograms.items()
                }
            }
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()


class TelemetryManager:
    """
    Central telemetry manager integrating tracing and metrics.
    """
    
    def __init__(self, service_name: str = "powerhouse-platform"):
        self.service_name = service_name
        self.tracer = Tracer(service_name)
        self.metrics = MetricsCollector()
        logger.info(f"Initialized telemetry for service: {service_name}")
    
    def trace(
        self,
        operation_name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Decorator for tracing function execution.
        
        Usage:
            @telemetry.trace("process_workflow")
            def process_workflow(workflow_id):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get parent span if exists
                parent_span = self.tracer.get_active_span()
                parent_span_id = parent_span.span_id if parent_span else None
                trace_id = parent_span.trace_id if parent_span else None
                
                # Start new span
                span = self.tracer.start_span(
                    name=operation_name,
                    trace_id=trace_id,
                    parent_span_id=parent_span_id,
                    attributes=attributes
                )
                
                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Record success
                    span.set_status("OK")
                    self.metrics.increment_counter(
                        f"{operation_name}.success",
                        labels={"service": self.service_name}
                    )
                    
                    return result
                    
                except Exception as e:
                    # Record error
                    span.set_status("ERROR", str(e))
                    span.add_event("exception", {
                        "exception.type": type(e).__name__,
                        "exception.message": str(e)
                    })
                    
                    self.metrics.increment_counter(
                        f"{operation_name}.error",
                        labels={"service": self.service_name, "error_type": type(e).__name__}
                    )
                    
                    raise
                    
                finally:
                    # End span and record duration
                    self.tracer.end_span(span)
                    self.metrics.record_histogram(
                        f"{operation_name}.duration_ms",
                        span.duration_ms(),
                        labels={"service": self.service_name}
                    )
            
            return wrapper
        return decorator
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary of a trace"""
        spans = self.tracer.get_spans_by_trace(trace_id)
        
        if not spans:
            return {"error": "Trace not found"}
        
        total_duration = max(s["end_time"] for s in spans if s["end_time"]) - \
                        min(s["start_time"] for s in spans)
        
        return {
            "trace_id": trace_id,
            "span_count": len(spans),
            "total_duration_ms": total_duration * 1000,
            "spans": spans,
            "error_count": sum(1 for s in spans if s["status"] == "ERROR")
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return self.metrics.get_metrics()


# Global telemetry instance
telemetry = TelemetryManager()
