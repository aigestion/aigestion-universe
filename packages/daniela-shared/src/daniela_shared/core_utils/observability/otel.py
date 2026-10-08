"""
OpenTelemetry instrumentation for aig.

Unified traces, metrics, and logs across all 19 federated engines.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from opentelemetry import context, metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# ─── Resource ───

def create_resource(service_name: str, service_version: str = "1.0.0") -> Resource:
    """Create OTel resource with service metadata."""
    return Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "deployment.environment": os.getenv("DEPLOYMENT_ENV", "development"),
        "service.instance.id": os.getenv("HOSTNAME", "unknown"),
    })


# ─── Traces ───

def setup_traces(
    service_name: str,
    endpoint: str = "http://localhost:4317",
    sample_rate: float = 1.0,
) -> TracerProvider:
    """Initialize trace provider with OTLP exporter."""
    resource = create_resource(service_name)

    tracer_provider = TracerProvider(
        resource=resource,
        sampler=trace.sampling.TraceIdRatioBased(sample_rate),
    )

    span_exporter = OTLPSpanExporter(endpoint=endpoint)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))

    trace.set_tracer_provider(tracer_provider)
    return tracer_provider


# ─── Metrics ───

def setup_metrics(
    service_name: str,
    endpoint: str = "http://localhost:4317",
    export_interval: int = 60,
) -> MeterProvider:
    """Initialize metrics provider with OTLP exporter."""
    resource = create_resource(service_name)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint),
        export_interval_millis=export_interval * 1000,
    )

    metrics_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )

    metrics.set_meter_provider(metrics_provider)
    return metrics_provider


# ─── Combined Setup ───

def setup_otel(
    service_name: str,
    endpoint: str = "http://localhost:4317",
    sample_rate: float = 1.0,
    export_interval: int = 60,
) -> tuple[TracerProvider, MeterProvider]:
    """Initialize OpenTelemetry for a service."""
    tracer_provider = setup_traces(service_name, endpoint, sample_rate)
    metrics_provider = setup_metrics(service_name, endpoint, export_interval)
    return tracer_provider, metrics_provider


# ─── Tracing Helpers ───

def get_tracer(name: str = __name__):
    """Get tracer for current module."""
    return trace.get_tracer(name)


def start_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """Start a new span with optional attributes."""
    tracer = get_tracer()
    span = tracer.start_span(name, kind=kind)
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    return span


def trace_function(
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
):
    """Decorator to trace function execution."""
    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__

        def wrapper(*args, **kwargs):
            with start_span(span_name, attributes or {}) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("status", "ok")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


# ─── Context Propagation ───

def inject_context(headers: dict[str, str]) -> None:
    """Inject trace context into outgoing request headers."""
    inject(headers)


def extract_context(headers: dict[str, str]) -> context.Context:
    """Extract trace context from incoming request headers."""
    return extract(headers)


# ─── Metrics Helpers ───

def get_meter(name: str = __name__):
    """Get meter for current module."""
    return metrics.get_meter(name)


def create_counter(name: str, description: str = "", unit: str = "1"):
    """Create a counter metric."""
    meter = get_meter()
    return meter.create_counter(name, description=description, unit=unit)


def create_histogram(name: str, description: str = "", unit: str = "ms"):
    """Create a histogram metric."""
    meter = get_meter()
    return meter.create_histogram(name, description=description, unit=unit)


def create_gauge(name: str, description: str = "", unit: str = "1"):
    """Create an observable gauge metric."""
    meter = get_meter()
    return meter.create_observable_gauge(name, description=description, unit=unit)


# ─── Request Tracing ───

def trace_request(
    method: str,
    route: str,
    status_code: int,
    duration_ms: float,
    attributes: dict[str, Any] | None = None,
):
    """Record a standard HTTP request span."""
    span_attrs = {
        "http.method": method,
        "http.route": route,
        "http.status_code": status_code,
        "http.duration_ms": duration_ms,
    }
    if attributes:
        span_attrs.update(attributes)

    with start_span(f"{method} {route}", span_attrs, trace.SpanKind.SERVER):
        pass


# ─── Database Tracing ───

def trace_db_query(
    operation: str,
    table: str,
    duration_ms: float,
    row_count: int | None = None,
):
    """Record a database query span."""
    attrs = {
        "db.operation": operation,
        "db.table": table,
        "db.duration_ms": duration_ms,
    }
    if row_count is not None:
        attrs["db.row_count"] = row_count

    with start_span(f"db.{operation}", attrs, trace.SpanKind.CLIENT):
        pass


# ─── Messaging Tracing ───

def trace_message(
    operation: str,
    destination: str,
    duration_ms: float,
    message_id: str | None = None,
):
    """Record a messaging span."""
    attrs = {
        "messaging.operation": operation,
        "messaging.destination": destination,
        "messaging.duration_ms": duration_ms,
    }
    if message_id:
        attrs["messaging.message_id"] = message_id

    with start_span(f"messaging.{operation}", attrs, trace.SpanKind.PRODUCER):
        pass


# ─── Flask Middleware ───

class FlaskOTelMiddleware:
    """Flask middleware for automatic request tracing."""

    def __init__(self, app, service_name: str = "flask-app"):
        self.app = app
        self.service_name = service_name
        self._setup()

    def _setup(self):
        """Setup auto-instrumentation."""
        try:
            from opentelemetry.instrumentation.flask import FlaskInstrumentor
            FlaskInstrumentor().instrument_app(self.app)
        except ImportError:
            pass

    def __call__(self, environ, start_response):
        return self.app(environ, start_response)


# ─── FastAPI Middleware ───

class FastAPIOTelMiddleware:
    """FastAPI middleware for automatic request tracing."""

    def __init__(self, app, service_name: str = "fastapi-app"):
        self.app = app
        self.service_name = service_name
        self._setup()

    def _setup(self):
        """Setup auto-instrumentation."""
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(self.app)
        except ImportError:
            pass

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)


# ─── Sampling Configuration ───

def get_sample_rate() -> float:
    """Get sample rate based on environment."""
    env = os.getenv("DEPLOYMENT_ENV", "development")
    rates = {
        "development": 1.0,
        "staging": 0.5,
        "production": 0.1,
    }
    return rates.get(env, 1.0)


# ─── Global Instances ───

_tracer_provider: TracerProvider | None = None
_metrics_provider: MeterProvider | None = None


def init_otel(service_name: str) -> tuple[TracerProvider, MeterProvider]:
    """Initialize global OTel instances."""
    global _tracer_provider, _metrics_provider

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    sample_rate = get_sample_rate()
    export_interval = int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "60"))

    _tracer_provider, _metrics_provider = setup_otel(
        service_name=service_name,
        endpoint=endpoint,
        sample_rate=sample_rate,
        export_interval=export_interval,
    )

    return _tracer_provider, _metrics_provider


def shutdown_otel() -> None:
    """Shutdown OTel providers."""
    global _tracer_provider, _metrics_provider

    if _tracer_provider:
        _tracer_provider.shutdown()
        _tracer_provider = None

    if _metrics_provider:
        _metrics_provider.shutdown()
        _metrics_provider = None
