"""
Resilience Patterns (Ideas 31-40)
---------------------------------
Circuit breaker, bulkhead, retry with jitter, timeout cascade, fallback chain,
rate limiter (sliding window), adaptive concurrency, health checks, chaos injection,
graceful degradation.
"""

from __future__ import annotations

import logging
import random
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Idea 31 - Circuit breaker
# ---------------------------------------------------------------------------

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker with configurable failure threshold and reset timeout."""

    def __init__(self, name: str = "default", failure_threshold: int = 5,
                 reset_timeout: float = 30.0, half_open_max: int = 3,
                 success_threshold: int = 2):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max = half_open_max
        self.success_threshold = success_threshold
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time = 0.0
        self._lock = threading.Lock()
        self._total_calls = 0
        self._total_failures = 0
        self._total_rejected = 0

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time >= self.reset_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
            return self._state

    def call(self, fn: Callable, *args, **kwargs) -> Any:
        current = self.state
        if current == CircuitState.OPEN:
            self._total_rejected += 1
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")

        with self._lock:
            self._total_calls += 1
            if current == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls > self.half_open_max:
                    raise CircuitOpenError(f"Circuit '{self.name}' HALF_OPEN limit")

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        with self._lock:
            self._failure_count = 0
            self._success_count += 1
            if self._state == CircuitState.HALF_OPEN and self._success_count >= self.success_threshold:
                self._state = CircuitState.CLOSED
                self._success_count = 0
                logger.info("Circuit '%s' -> CLOSED", self.name)

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._success_count = 0
            self._total_failures += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning("Circuit '%s' -> OPEN after %d failures", self.name, self._failure_count)

    def reset(self):
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0

    def stats(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "total_rejected": self._total_rejected,
        }


class CircuitOpenError(Exception):
    pass


# ---------------------------------------------------------------------------
# Idea 32 - Bulkhead pattern (isolation)
# ---------------------------------------------------------------------------

class Bulkhead:
    """Isolate failures by limiting concurrent access per service."""

    def __init__(self, name: str, max_concurrent: int = 10, max_wait_sec: float = 5.0):
        self.name = name
        self.max_concurrent = max_concurrent
        self.max_wait_sec = max_wait_sec
        self._semaphore = threading.Semaphore(max_concurrent)
        self._active = 0
        self._total_calls = 0
        self._total_rejected = 0
        self._lock = threading.Lock()

    def execute(self, fn: Callable, *args, **kwargs) -> Any:
        acquired = self._semaphore.acquire(timeout=self.max_wait_sec)
        if not acquired:
            with self._lock:
                self._total_rejected += 1
            raise BulkheadFullError(f"Bulkhead '{self.name}' is full")

        with self._lock:
            self._active += 1
            self._total_calls += 1
        try:
            return fn(*args, **kwargs)
        finally:
            with self._lock:
                self._active -= 1
            self._semaphore.release()

    def stats(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "active": self._active,
            "max_concurrent": self.max_concurrent,
            "total_calls": self._total_calls,
            "total_rejected": self._total_rejected,
        }


class BulkheadFullError(Exception):
    pass


class BulkheadManager:
    """Manage multiple bulkheads."""

    def __init__(self):
        self._bulkheads: dict[str, Bulkhead] = {}

    def get(self, name: str, max_concurrent: int = 10) -> Bulkhead:
        if name not in self._bulkheads:
            self._bulkheads[name] = Bulkhead(name=name, max_concurrent=max_concurrent)
        return self._bulkheads[name]

    def stats(self) -> dict[str, Any]:
        return {name: bh.stats() for name, bh in self._bulkheads.items()}


# ---------------------------------------------------------------------------
# Idea 33 - Retry with jitter
# ---------------------------------------------------------------------------

class RetryStrategy(Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


class RetryWithJitter:
    """Retry with configurable backoff and jitter."""

    def __init__(self, max_retries: int = 3, strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
                 base_delay: float = 0.1, max_delay: float = 10.0, jitter_ratio: float = 0.3):
        self.max_retries = max_retries
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_ratio = jitter_ratio

    def _compute_delay(self, attempt: int) -> float:
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** attempt)
        else:  # LINEAR
            delay = self.base_delay * (attempt + 1)

        delay = min(delay, self.max_delay)
        jitter = delay * self.jitter_ratio * random.random()
        return delay + jitter

    def execute(self, fn: Callable, *args, **kwargs) -> Any:
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    delay = self._compute_delay(attempt)
                    time.sleep(delay)
                    logger.debug("Retry %d/%d after %.3fs", attempt + 1, self.max_retries, delay)
        raise last_exc


# ---------------------------------------------------------------------------
# Idea 34 - Timeout cascade
# ---------------------------------------------------------------------------

@dataclass
class TimeoutConfig:
    service: str
    timeout_sec: float
    fallback_timeout: float | None = None


class TimeoutCascade:
    """Cascade timeouts across multiple services with decreasing budgets."""

    def __init__(self, configs: list[TimeoutConfig]):
        self.configs = configs

    def execute(self, fn_map: dict[str, Callable], total_budget: float) -> Any:
        remaining = total_budget
        last_exc = None
        for config in self.configs:
            if remaining <= 0:
                raise TimeoutCascadeError(f"Budget exhausted after {config.service}")
            start = time.monotonic()
            try:
                result = fn_map[config.service]()
                elapsed = time.monotonic() - start
                remaining -= elapsed
                return result
            except Exception as exc:
                elapsed = time.monotonic() - start
                remaining -= elapsed
                last_exc = exc
                logger.warning("Timeout cascade: %s failed (%.3fs): %s", config.service, elapsed, exc)
        raise TimeoutCascadeError(f"All services failed. Last: {last_exc}")


class TimeoutCascadeError(Exception):
    pass


# ---------------------------------------------------------------------------
# Idea 35 - Fallback chain
# ---------------------------------------------------------------------------

class FallbackChain:
    """Try primary, then fallbacks in order until one succeeds."""

    def __init__(self):
        self._chain: list[tuple[str, Callable]] = []

    def add(self, name: str, fn: Callable):
        self._chain.append((name, fn))

    def execute(self, *args, **kwargs) -> Any:
        last_exc = None
        for name, fn in self._chain:
            try:
                result = fn(*args, **kwargs)
                return result
            except Exception as exc:
                last_exc = exc
                logger.debug("Fallback '%s' failed: %s", name, exc)
        raise FallbackExhaustedError(f"All {len(self._chain)} fallbacks exhausted. Last: {last_exc}")


class FallbackExhaustedError(Exception):
    pass


# ---------------------------------------------------------------------------
# Idea 36 - Rate limiter (sliding window)
# ---------------------------------------------------------------------------

class SlidingWindowRateLimiter:
    """Sliding window rate limiter with token bucket."""

    def __init__(self, max_requests: int = 100, window_sec: float = 60.0):
        self.max_requests = max_requests
        self.window_sec = window_sec
        self._timestamps: deque = deque()
        self._lock = threading.Lock()
        self._total_allowed = 0
        self._total_rejected = 0

    def allow(self) -> bool:
        now = time.time()
        with self._lock:
            cutoff = now - self.window_sec
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()

            if len(self._timestamps) < self.max_requests:
                self._timestamps.append(now)
                self._total_allowed += 1
                return True
            else:
                self._total_rejected += 1
                return False

    def execute(self, fn: Callable, *args, **kwargs) -> Any:
        if not self.allow():
            raise RateLimitExceededError("Rate limit exceeded")
        return fn(*args, **kwargs)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            current = len(self._timestamps)
        return {
            "current_window_count": current,
            "max_requests": self.max_requests,
            "window_sec": self.window_sec,
            "total_allowed": self._total_allowed,
            "total_rejected": self._total_rejected,
        }


class RateLimitExceededError(Exception):
    pass


# ---------------------------------------------------------------------------
# Idea 37 - Adaptive concurrency limiter
# ---------------------------------------------------------------------------

class AdaptiveConcurrencyLimiter:
    """Dynamically adjust concurrency based on error rate."""

    def __init__(self, initial_limit: int = 20, min_limit: int = 5,
                 max_limit: int = 100, window_size: int = 50,
                 error_threshold: float = 0.25):
        self.initial_limit = initial_limit
        self.min_limit = min_limit
        self.max_limit = max_limit
        self.window_size = window_size
        self.error_threshold = error_threshold
        self._current_limit = initial_limit
        self._semaphore = threading.Semaphore(initial_limit)
        self._recent_results: deque = deque(maxlen=window_size)
        self._lock = threading.Lock()

    def execute(self, fn: Callable, *args, **kwargs) -> Any:
        acquired = self._semaphore.acquire(timeout=5.0)
        if not acquired:
            raise ConcurrencyLimitError("Adaptive limit reached")
        try:
            result = fn(*args, **kwargs)
            self._record(True)
            return result
        except Exception:
            self._record(False)
            raise
        finally:
            self._semaphore.release()

    def _record(self, success: bool):
        with self._lock:
            self._recent_results.append(success)
            if len(self._recent_results) >= self.window_size:
                errors = sum(1 for r in self._recent_results if not r)
                error_rate = errors / len(self._recent_results)
                if error_rate > self.error_threshold:
                    self._current_limit = max(self.min_limit, self._current_limit - 2)
                else:
                    self._current_limit = min(self.max_limit, self._current_limit + 1)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            window = list(self._recent_results)
        errors = sum(1 for r in window if not r)
        return {
            "current_limit": self._current_limit,
            "window_size": len(window),
            "error_rate": round(errors / len(window), 4) if window else 0,
        }


class ConcurrencyLimitError(Exception):
    pass


# ---------------------------------------------------------------------------
# Idea 38 - Health check aggregator
# ---------------------------------------------------------------------------

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    name: str
    status: HealthStatus
    latency_ms: float
    message: str = ""
    timestamp: float = field(default_factory=time.time)


class HealthCheckAggregator:
    """Aggregate health checks from multiple services."""

    def __init__(self):
        self._checks: dict[str, Callable[[], HealthCheckResult]] = {}
        self._results: dict[str, HealthCheckResult] = {}
        self._lock = threading.Lock()

    def register(self, name: str, check_fn: Callable[[], HealthCheckResult]):
        self._checks[name] = check_fn

    def run_all(self) -> dict[str, HealthCheckResult]:
        results = {}
        for name, fn in self._checks.items():
            try:
                result = fn()
            except Exception as exc:
                result = HealthCheckResult(
                    name=name, status=HealthStatus.UNHEALTHY,
                    latency_ms=0, message=str(exc),
                )
            results[name] = result

        with self._lock:
            self._results = results
        return results

    def overall_status(self) -> HealthStatus:
        with self._lock:
            statuses = [r.status for r in self._results.values()]
        if not statuses:
            return HealthStatus.HEALTHY
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        if any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    def stats(self) -> dict[str, Any]:
        with self._lock:
            results = {k: {"status": v.status.value, "latency_ms": round(v.latency_ms, 2)}
                       for k, v in self._results.items()}
        return {
            "overall": self.overall_status().value,
            "checks": results,
            "registered": list(self._checks.keys()),
        }


# ---------------------------------------------------------------------------
# Idea 39 - Chaos engineering injector
# ---------------------------------------------------------------------------

class ChaosType(Enum):
    LATENCY = "latency"
    ERROR = "error"
    TIMEOUT = "timeout"
    DROP = "drop"


class ChaosInjector:
    """Inject faults for chaos engineering testing."""

    def __init__(self):
        self._rules: dict[str, ChaosType] = {}
        self._params: dict[str, dict[str, Any]] = {}
        self._injected_count: dict[str, int] = {}
        self._enabled = False

    def enable(self, service: str, chaos_type: ChaosType, **params):
        self._rules[service] = chaos_type
        self._params[service] = params
        self._injected_count[service] = 0
        self._enabled = True

    def disable(self, service: str):
        self._rules.pop(service, None)
        self._params.pop(service, None)
        if not self._rules:
            self._enabled = False

    def disable_all(self):
        self._rules.clear()
        self._params.clear()
        self._enabled = False

    def execute(self, service: str, fn: Callable, *args, **kwargs) -> Any:
        if not self._enabled or service not in self._rules:
            return fn(*args, **kwargs)

        chaos = self._rules[service]
        params = self._params.get(service, {})
        self._injected_count[service] = self._injected_count.get(service, 0) + 1

        if chaos == ChaosType.LATENCY:
            delay = params.get("delay_sec", 1.0)
            time.sleep(delay)
            return fn(*args, **kwargs)

        elif chaos == ChaosType.ERROR:
            error_msg = params.get("message", "Chaos: injected error")
            raise ChaosInjectedError(error_msg)

        elif chaos == ChaosType.TIMEOUT:
            timeout = params.get("timeout_sec", 0.001)
            time.sleep(timeout)
            raise ChaosInjectedError("Chaos: timeout")

        elif chaos == ChaosType.DROP:
            if random.random() < params.get("drop_rate", 1.0):
                raise ChaosInjectedError("Chaos: dropped")
            return fn(*args, **kwargs)

        return fn(*args, **kwargs)

    def stats(self) -> dict[str, Any]:
        return {
            "enabled": self._enabled,
            "rules": {k: v.value for k, v in self._rules.items()},
            "injected_count": dict(self._injected_count),
        }


class ChaosInjectedError(Exception):
    pass


# ---------------------------------------------------------------------------
# Idea 40 - Graceful degradation
# ---------------------------------------------------------------------------

class DegradationLevel(Enum):
    FULL = "full"
    PARTIAL = "partial"
    MINIMAL = "minimal"
    OFFLINE = "offline"


class GracefulDegradation:
    """Gracefully degrade functionality based on system health."""

    def __init__(self):
        self._level = DegradationLevel.FULL
        self._feature_map: dict[str, DegradationLevel] = {}
        self._fallback_responses: dict[str, Any] = {}
        self._lock = threading.Lock()

    def set_level(self, level: DegradationLevel):
        with self._lock:
            self._level = level

    def register_feature(self, feature: str, min_level: DegradationLevel,
                         fallback: Any = None):
        self._feature_map[feature] = min_level
        if fallback is not None:
            self._fallback_responses[feature] = fallback

    def is_available(self, feature: str) -> bool:
        with self._lock:
            current = self._level
        min_level = self._feature_map.get(feature, DegradationLevel.FULL)
        level_order = [DegradationLevel.FULL, DegradationLevel.PARTIAL,
                       DegradationLevel.MINIMAL, DegradationLevel.OFFLINE]
        return level_order.index(current) <= level_order.index(min_level)

    def execute(self, feature: str, fn: Callable, fallback_fn: Callable | None = None,
                *args, **kwargs) -> Any:
        if self.is_available(feature):
            return fn(*args, **kwargs)

        if fallback_fn:
            return fallback_fn(*args, **kwargs)

        if feature in self._fallback_responses:
            return self._fallback_responses[feature]

        raise FeatureDegradedError(f"Feature '{feature}' unavailable at level {self._level.value}")


class FeatureDegradedError(Exception):
    pass


# ---------------------------------------------------------------------------
# Unified Resilience Manager
# ---------------------------------------------------------------------------

class ResilienceManager:
    """Unified interface to all resilience patterns."""

    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.bulkheads = BulkheadManager()
        self.retry = RetryWithJitter()
        self.rate_limiter = SlidingWindowRateLimiter()
        self.adaptive_concurrency = AdaptiveConcurrencyLimiter()
        self.health_checks = HealthCheckAggregator()
        self.chaos_injector = ChaosInjector()
        self.degradation = GracefulDegradation()

    def get_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)
        return self.circuit_breakers[name]

    def stats(self) -> dict[str, Any]:
        return {
            "circuit_breakers": {k: v.stats() for k, v in self.circuit_breakers.items()},
            "bulkheads": self.bulkheads.stats(),
            "rate_limiter": self.rate_limiter.stats(),
            "adaptive_concurrency": self.adaptive_concurrency.stats(),
            "health_checks": self.health_checks.stats(),
            "chaos": self.chaos_injector.stats(),
        }
