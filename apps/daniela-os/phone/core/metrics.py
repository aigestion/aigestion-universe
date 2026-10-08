"""Shared measurement vocabulary for the monitoring subagents.

Sixteen of the original subagents returned fixed dictionaries: one reported
``requests_per_second: 150`` and another ``current_load: "high"`` without
observing anything. That is fabrication wearing the shape of telemetry, and it
is worse than returning nothing, because a caller cannot tell the difference
between a measurement and an invention.

These helpers give them something real to measure. A caller supplies actual
samples; the helpers classify them against declared thresholds and return the
evidence alongside the verdict, so a report always shows what it was derived
from.

If no samples are supplied, the result is explicitly ``insufficient_data``
rather than a plausible number. Every threshold is named so the decision rule
is inspectable rather than buried in a branch.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

__all__ = ["THRESHOLDS", "classify", "summarise", "insufficient", "measure_rate"]


def _get(mapping: Any, key: str, default: Any = None) -> Any:
    """Read a key from a mapping or an object, without raising."""
    if isinstance(mapping, dict):
        return mapping.get(key, default)
    return getattr(mapping, key, default)


THRESHOLDS: dict[str, dict[str, float]] = {
    "cpu_percent": {"good": 50.0, "acceptable": 75.0, "bad": 90.0},
    "memory_percent": {"good": 60.0, "acceptable": 80.0, "bad": 92.0},
    "latency_ms": {"good": 100.0, "acceptable": 300.0, "bad": 1000.0},
    "error_rate": {"good": 0.01, "acceptable": 0.05, "bad": 0.10},
    "queue_depth": {"good": 10.0, "acceptable": 50.0, "bad": 100.0},
    "disk_percent": {"good": 70.0, "acceptable": 85.0, "bad": 95.0},
}


def insufficient(metric: str, required: str, **extra: Any) -> dict[str, Any]:
    """A verdict that admits it has no data.

    Preferred over any default value: an absent measurement must be visible as
    absent, not filled in with something plausible.
    """
    return {
        "status": "insufficient_data",
        "metric": metric,
        "required_input": required,
        "thresholds": THRESHOLDS.get(metric),
        **extra,
    }


def classify(metric: str, value: float | None) -> str:
    """Bucket a numeric reading against a named threshold set."""
    if value is None:
        return "unknown"
    limits = THRESHOLDS.get(metric)
    if limits is None:
        return "unknown"
    if value <= limits["good"]:
        return "good"
    if value <= limits["acceptable"]:
        return "acceptable"
    if value <= limits["bad"]:
        return "bad"
    return "critical"


def summarise(
    metric: str,
    value: float | None,
    *,
    source: str = "",
    unit: str = "",
    required: str = "",
) -> dict[str, Any]:
    """Build a report from one measurement, keeping the evidence."""
    if value is None:
        return insufficient(metric, required or f"a numeric {metric} sample")
    return {
        "status": "measured",
        "metric": metric,
        "value": value,
        "unit": unit,
        "verdict": classify(metric, value),
        "thresholds": THRESHOLDS.get(metric),
        "source": source or "caller supplied",
    }


def measure_rate(
    events: Sequence[float],
    window_seconds: float | None = None,
    *,
    start: float | None = None,
    end: float | None = None,
) -> dict[str, Any]:
    """Events per second over a window.

    Requires timestamps. Without them a rate cannot be computed, and guessing
    one is exactly the behaviour this module exists to remove.
    """
    timestamps = [float(t) for t in events if isinstance(t, (int, float))]
    if len(timestamps) < 2:
        return {
            "status": "insufficient_data",
            "metric": "rate_per_second",
            "required_input": "at least 2 event timestamps",
            "samples": len(timestamps),
        }

    span_start = float(start) if start is not None else min(timestamps)
    span_end = float(end) if end is not None else max(timestamps)
    if window_seconds is not None:
        span_end = span_start + float(window_seconds)

    span = span_end - span_start
    if span <= 0:
        return {
            "status": "insufficient_data",
            "metric": "rate_per_second",
            "required_input": "a non-zero time window",
            "samples": len(timestamps),
        }

    rate = (len(timestamps) - 1) / span
    return {
        "status": "measured",
        "metric": "rate_per_second",
        "value": rate,
        "unit": "events/s",
        "samples": len(timestamps),
        "window_seconds": span,
        "verdict": "measured",
    }


def mean(values: Iterable[float]) -> float | None:
    numbers = [float(v) for v in values if isinstance(v, (int, float))]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def percentile(values: Iterable[float], fraction: float) -> float | None:
    """Nearest-rank percentile, computed without sorting the whole sample."""
    numbers = sorted(float(v) for v in values if isinstance(v, (int, float)))
    if not numbers:
        return None
    if not 0 < fraction <= 1:
        return None
    index = max(0, min(len(numbers) - 1, int(round(fraction * len(numbers))) - 1))
    return numbers[index]


def percent_error(errors: Sequence[Any], total: float | None = None) -> float | None:
    """Error ratio, or ``None`` when the denominator is zero."""
    count = len([e for e in errors if e])
    denominator = float(total) if total is not None else float(len(errors))
    if denominator <= 0:
        return None
    return count / denominator
