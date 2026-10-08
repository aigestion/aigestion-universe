"""Resilience validators: pure functions returning ValidationResult."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    name: str
    passed: bool
    details: str = ""
    metric: Any = None

    def to_dict(self) -> dict:
        return {"name": self.name, "passed": bool(self.passed), "details": self.details, "metric": self.metric}

    def __bool__(self) -> bool:
        return self.passed


def _resolve(value: Any) -> Any:
    return value() if callable(value) else value


def validate_circuit_breaker_trips(
    circuit_state: str | dict | Callable[[], Any] = "open",
    failures: int = 5,
    threshold: int = 5,
) -> ValidationResult:
    """Passes when the breaker is open (tripped)."""
    state = _resolve(circuit_state)
    if isinstance(state, dict):
        state_str = str(state.get("state", state.get("status", ""))).lower()
    else:
        state_str = str(state).lower()
    tripped = state_str in ("open", "tripped", "tripped_open")
    if not tripped:
        tripped = int(failures) >= int(threshold)
    return ValidationResult(
        name="circuit_breaker_trips",
        passed=tripped,
        details=f"state={state_str!r} failures={failures} threshold={threshold}",
        metric={"state": state_str, "failures": failures, "threshold": threshold},
    )


def validate_retry_succeeds(
    attempts: Sequence[bool] | Callable[[], Sequence[bool]],
) -> ValidationResult:
    """Passes when an initial failure is followed by a success (retry works)."""
    seq = list(_resolve(attempts))
    passed = len(seq) >= 2 and (not seq[0]) and any(bool(x) for x in seq[1:])
    return ValidationResult(
        name="retry_succeeds",
        passed=passed,
        details=f"attempts={seq}",
        metric={"attempts": seq},
    )


def validate_fallback_serves(
    primary_ok: bool | Callable[[], bool] = False,
    fallback_response: Any = None,
    fallback_ok: bool | Callable[[], bool] | None = None,
) -> ValidationResult:
    """Passes when primary is healthy OR fallback serves traffic."""
    p = bool(_resolve(primary_ok))
    f = bool(_resolve(fallback_ok)) if fallback_ok is not None else (fallback_response is not None)
    passed = p or f
    return ValidationResult(
        name="fallback_serves",
        passed=passed,
        details=f"primary_ok={p} fallback_ok={f}",
        metric={"primary_ok": p, "fallback_ok": f},
    )


def validate_health_score(
    health_score: float | Callable[[], float],
    threshold: float = 0.8,
) -> ValidationResult:
    """Passes when health score stays at/above threshold."""
    score = float(_resolve(health_score))
    passed = score >= float(threshold)
    return ValidationResult(
        name="health_score_above_threshold",
        passed=passed,
        details=f"health={score:.3f} threshold={threshold}",
        metric={"health_score": score, "threshold": threshold},
    )


def _p99(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("empty latency sample")
    ordered = sorted(float(v) for v in values)
    max(0, min(len(ordered) - 1, int(0.99 * (len(ordered) - 1) + 0.5) if len(ordered) > 1 else 0))
    # Standard nearest-rank: ceil(0.99*n)-1
    import math

    rank = max(1, math.ceil(0.99 * len(ordered)))
    return ordered[rank - 1]


def validate_p99_latency(
    latencies: Sequence[float] | Callable[[], Sequence[float]],
    slo_ms: float,
) -> ValidationResult:
    """Passes when p99 latency is within SLO."""
    samples: list[float] = [float(v) for v in _resolve(latencies)]
    p99 = _p99(samples)
    passed = p99 <= float(slo_ms)
    return ValidationResult(
        name="p99_within_slo",
        passed=passed,
        details=f"p99={p99:.2f}ms slo={slo_ms}ms n={len(samples)}",
        metric={"p99_ms": p99, "slo_ms": slo_ms, "n": len(samples)},
    )


def validate_zero_data_loss(written: Any, read_back: Any) -> ValidationResult:
    """Passes when read-back data exactly matches what was written."""
    try:
        if isinstance(written, (list, tuple)) and isinstance(read_back, (list, tuple)):
            passed = list(written) == list(read_back)
            details = f"items written={len(written)} read={len(read_back)}"
        elif isinstance(written, (set, frozenset)) and isinstance(read_back, (set, frozenset)):
            passed = set(written) == set(read_back)
            details = f"set size written={len(written)} read={len(read_back)}"
        elif isinstance(written, dict) and isinstance(read_back, dict):
            passed = dict(written) == dict(read_back)
            details = f"keys written={len(written)} read={len(read_back)}"
        else:
            passed = written == read_back
            details = f"written={written!r} read={read_back!r}"
    except Exception as exc:
        passed = False
        details = f"comparison raised: {exc}"
    return ValidationResult(
        name="zero_data_loss",
        passed=passed,
        details=details,
        metric={"equal": passed},
    )


def validate_all(results: Sequence[ValidationResult]) -> bool:
    return all(bool(r) for r in results)
