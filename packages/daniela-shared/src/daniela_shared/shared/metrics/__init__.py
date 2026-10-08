"""Metrics collection for all aig services."""

from typing import Any

try:
    from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

class MetricsRegistry:
    """Wrapper for Prometheus metrics with fallback."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._counters: dict[str, Any] = {}
        self._histograms: dict[str, Any] = {}
        self._gauges: dict[str, Any] = {}
        self._registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None

    def counter(self, name: str, description: str, labels: list[str] = None) -> Any:
        """Create or get a counter."""
        key = f"counter_{name}"
        if key not in self._counters:
            if PROMETHEUS_AVAILABLE:
                self._counters[key] = Counter(
                    f"{self.service_name}_{name}", description, labels or [], registry=self._registry
                )
            else:
                self._counters[key] = _DummyMetric()
        return self._counters[key]

    def histogram(self, name: str, description: str, labels: list[str] = None, buckets: list[float] = None) -> Any:
        """Create or get a histogram."""
        key = f"histogram_{name}"
        if key not in self._histograms:
            if PROMETHEUS_AVAILABLE:
                self._histograms[key] = Histogram(
                    f"{self.service_name}_{name}", description, labels or [], buckets=buckets, registry=self._registry
                )
            else:
                self._histograms[key] = _DummyMetric()
        return self._histograms[key]

    def gauge(self, name: str, description: str, labels: list[str] = None) -> Any:
        """Create or get a gauge."""
        key = f"gauge_{name}"
        if key not in self._gauges:
            if PROMETHEUS_AVAILABLE:
                self._gauges[key] = Gauge(
                    f"{self.service_name}_{name}", description, labels or [], registry=self._registry
                )
            else:
                self._gauges[key] = _DummyMetric()
        return self._gauges[key]

    def get_metrics(self) -> bytes:
        """Get Prometheus metrics output."""
        if PROMETHEUS_AVAILABLE:
            from prometheus_client import generate_latest
            return generate_latest(self._registry)
        return b""

class _DummyMetric:
    """Fallback when Prometheus is not available."""
    def labels(self, *args, **kwargs):
        return self
    def inc(self, *args, **kwargs):
        pass
    def observe(self, *args, **kwargs):
        pass
    def set(self, *args, **kwargs):
        pass

# Global metrics registry
_metrics_registry: MetricsRegistry | None = None

def get_metrics_registry(service_name: str) -> MetricsRegistry:
    """Get or create metrics registry for a service."""
    global _metrics_registry
    if _metrics_registry is None:
        _metrics_registry = MetricsRegistry(service_name)
    return _metrics_registry
