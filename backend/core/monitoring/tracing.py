"""
OpenTelemetry Distributed Tracing for Powerhouse.

Provides a thin setup layer and a ``get_tracer()`` helper used throughout the
codebase.  All instrumentation is guarded by ``settings.otel_enabled`` so the
feature is a true no-op (zero overhead) when disabled.

Usage::

    # In lifespan startup (ph_server.py):
    from core.monitoring.tracing import setup_tracing
    setup_tracing(service_name=settings.otel_service_name,
                  otlp_endpoint=settings.otel_otlp_endpoint)

    # In any module that wants to emit spans:
    from core.monitoring.tracing import get_tracer
    _tracer = get_tracer(__name__)

    with _tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("key", "value")
        ...
"""

from __future__ import annotations

from typing import Optional

from utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_provider: Optional[Any] = None  # type: ignore[name-defined]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def setup_tracing(
    service_name: str = "powerhouse",
    otlp_endpoint: Optional[str] = None,
) -> None:
    """
    Initialise the global OpenTelemetry ``TracerProvider``.

    Call once at server startup.  Safe to call multiple times (subsequent
    calls are ignored).

    Args:
        service_name: Logical service name reported in every span.
        otlp_endpoint: gRPC endpoint of an OTLP-compatible collector such as
            Jaeger (e.g. ``"http://jaeger:4317"``).  When *None*, spans are
            printed to stdout (useful for local development).
    """
    global _provider

    if _provider is not None:
        logger.debug("OpenTelemetry already initialised – skipping setup_tracing()")
        return

    if not OTEL_AVAILABLE:
        logger.warning(
            "opentelemetry-sdk not installed – distributed tracing disabled. "
            "Install with: pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc"
        )
        return

    resource = Resource(attributes={"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(
                "OpenTelemetry tracing → OTLP endpoint %s (service=%s)",
                otlp_endpoint, service_name,
            )
        except Exception as exc:
            logger.warning("Failed to configure OTLP exporter: %s – falling back to console", exc)
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info(
            "OpenTelemetry tracing → console (no OTLP endpoint configured, service=%s)",
            service_name,
        )

    trace.set_tracer_provider(provider)
    _provider = provider

    # Auto-instrument FastAPI if available
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor().instrument()
        logger.info("FastAPI auto-instrumented for OpenTelemetry")
    except Exception as exc:
        logger.debug("FastAPI auto-instrumentation unavailable: %s", exc)


def get_tracer(name: str = "powerhouse") -> Any:  # type: ignore[name-defined]
    """
    Return an OpenTelemetry ``Tracer`` for *name*.

    Returns a no-op tracer when OpenTelemetry is unavailable or not yet
    initialised, so all call sites are safe without additional guards.
    """
    if not OTEL_AVAILABLE:
        return _NoOpTracer()
    return trace.get_tracer(name)


def shutdown_tracing() -> None:
    """
    Flush and shut down the tracer provider.

    Call from the server lifespan shutdown handler to ensure all in-flight
    spans are exported before the process exits.
    """
    global _provider
    if _provider is not None:
        try:
            _provider.shutdown()
            logger.info("OpenTelemetry TracerProvider shut down")
        except Exception as exc:
            logger.debug("Error shutting down TracerProvider: %s", exc)
        _provider = None


# ---------------------------------------------------------------------------
# No-op tracer (used when opentelemetry-sdk is not installed)
# ---------------------------------------------------------------------------

from contextlib import contextmanager
from typing import Any


class _NoOpSpan:
    """Minimal span stub that silently ignores all attribute/event calls."""

    def set_attribute(self, key: str, value: Any) -> None:  # noqa: D401
        pass

    def record_exception(self, exc: Exception) -> None:
        pass

    def __enter__(self) -> "_NoOpSpan":
        return self

    def __exit__(self, *args: Any) -> None:
        pass


class _NoOpTracer:
    """Minimal tracer stub that returns ``_NoOpSpan`` instances."""

    @contextmanager
    def start_as_current_span(self, name: str, **kwargs: Any):  # type: ignore[override]
        yield _NoOpSpan()
