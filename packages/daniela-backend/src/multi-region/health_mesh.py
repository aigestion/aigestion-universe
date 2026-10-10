"""
aig Multi-Region Health Mesh
====================================
Cross-region health prober: probes each region primary endpoint,
tracks consecutive failures, and evaluates quorum (2 of 3 healthy).

Autor: aig Team
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

try:
    from .config import REGIONS, get_region
except ImportError:
    from config import REGIONS, get_region

try:
    from .failover import HealthCheckResult, RegionStatus
except ImportError:
    from failover import HealthCheckResult, RegionStatus


class HealthMesh:
    """Probes every region primary endpoint and tracks a health matrix."""

    PROBE_INTERVAL = 10.0
    FAILURE_THRESHOLD = 3
    QUORUM_SIZE = 2

    def __init__(
        self,
        probe_fn: Callable[[str], bool] | None = None,
        failure_threshold: int = 3,
        quorum_size: int = 2,
    ) -> None:
        self._probe_fn = probe_fn
        self.failure_threshold = failure_threshold
        self.quorum_size = quorum_size
        self._consecutive_failures: dict[str, int] = dict.fromkeys(REGIONS, 0)
        self._status: dict[str, RegionStatus] = dict.fromkeys(REGIONS, RegionStatus.HEALTHY)
        self._latency_ms: dict[str, float] = dict.fromkeys(REGIONS, 0.0)
        self._last_probe: dict[str, float] = dict.fromkeys(REGIONS, 0.0)
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    # ── Configuration ──────────────────────────────────────────

    def set_probe_fn(self, fn: Callable[[str], bool]) -> None:
        """Set custom probe function (region_name -> is_healthy)."""
        self._probe_fn = fn

    def _default_probe(self, region_name: str) -> bool:
        region = get_region(region_name)
        return bool(region is not None and region.is_active)

    # ── Probing ────────────────────────────────────────────────

    def probe_region(self, region_name: str) -> HealthCheckResult:
        """Probe a single region primary endpoint."""
        region = get_region(region_name)
        if region is None:
            return HealthCheckResult(
                region_name=region_name,
                status=RegionStatus.DOWN,
                error="Region not found",
            )

        start = time.time()
        error: str | None = None
        try:
            fn = self._probe_fn or self._default_probe
            healthy = bool(fn(region_name))
        except Exception as e:
            healthy = False
            error = str(e)
        latency = (time.time() - start) * 1000

        with self._lock:
            self._last_probe[region_name] = time.time()
            self._latency_ms[region_name] = latency
            if healthy:
                self._consecutive_failures[region_name] = 0
                self._status[region_name] = RegionStatus.HEALTHY
            else:
                self._consecutive_failures[region_name] += 1
                if (
                    self._consecutive_failures[region_name]
                    >= self.failure_threshold
                ):
                    self._status[region_name] = RegionStatus.DOWN
            status = self._status[region_name]

        return HealthCheckResult(
            region_name=region_name,
            status=status,
            latency_ms=latency,
            error=error,
        )

    def probe_once(self) -> dict[str, HealthCheckResult]:
        """Probe all regions once; returns results keyed by region name."""
        return {name: self.probe_region(name) for name in REGIONS}

    # ── Matrix & Quorum ────────────────────────────────────────

    def get_matrix(self) -> dict[str, dict[str, Any]]:
        """Return the cross-region health matrix (JSON-serializable)."""
        with self._lock:
            matrix: dict[str, dict[str, Any]] = {}
            for name in REGIONS:
                region = get_region(name)
                matrix[name] = {
                    "status": self._status[name].value,
                    "consecutive_failures": self._consecutive_failures[name],
                    "latency_ms": round(self._latency_ms[name], 3),
                    "last_probe": self._last_probe[name],
                    "primary_host": region.primary_host if region else "",
                    "failover_order": region.failover_order if region else -1,
                }
            return matrix

    def get_healthy_regions(self) -> list[str]:
        """Return names of regions currently HEALTHY."""
        with self._lock:
            return [
                n for n, s in self._status.items() if s == RegionStatus.HEALTHY
            ]

    def is_quorum_healthy(self) -> bool:
        """True when at least quorum_size regions are healthy."""
        return len(self.get_healthy_regions()) >= self.quorum_size

    def quorum_check(self) -> dict[str, Any]:
        """Evaluate quorum: 2 of 3 regions healthy by default."""
        healthy = self.get_healthy_regions()
        unhealthy = [n for n in REGIONS if n not in healthy]
        return {
            "quorum": len(healthy) >= self.quorum_size,
            "healthy": healthy,
            "unhealthy": unhealthy,
            "healthy_count": len(healthy),
            "total": len(REGIONS),
            "quorum_size": self.quorum_size,
        }

    # ── Background Probing ─────────────────────────────────────

    def start(self) -> None:
        """Start background probing every PROBE_INTERVAL seconds."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop background probing."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.PROBE_INTERVAL + 2)
            self._thread = None

    def _loop(self) -> None:
        while self._running:
            self.probe_once()
            time.sleep(self.PROBE_INTERVAL)
