"""
aig Multi-Region Failover Manager
=========================================
Automatic failover, health checks, and primary restore.

Autor: aig Team
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    from .config import REGIONS, get_failover_targets, get_region
except ImportError:
    from config import REGIONS, get_failover_targets, get_region


# ── Status Enum ────────────────────────────────────────────────


class RegionStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    FAILOVER = "failover"
    RESTORING = "restoring"


# ── Health Check Result ────────────────────────────────────────


@dataclass
class HealthCheckResult:
    region_name: str
    status: RegionStatus
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)
    error: str | None = None


# ── Failover Event ─────────────────────────────────────────────


@dataclass
class FailoverEvent:
    source_region: str
    target_region: str
    reason: str
    timestamp: float = field(default_factory=time.time)
    restored: bool = False


# ── Failover Manager ──────────────────────────────────────────


class FailoverManager:
    """Manages health checks, automatic failover, and primary restore."""

    HEALTH_CHECK_INTERVAL = 5.0
    CONSECUTIVE_FAILURES_THRESHOLD = 3
    RESTORE_COOLDOWN = 30.0

    def __init__(self, local_region: str):
        self.local_region = local_region
        self._region_status: dict[str, RegionStatus] = dict.fromkeys(REGIONS, RegionStatus.HEALTHY)
        self._failover_events: list[FailoverEvent] = []
        self._consecutive_failures: dict[str, int] = dict.fromkeys(REGIONS, 0)
        self._last_restore: dict[str, float] = dict.fromkeys(REGIONS, 0.0)
        self._notifications: list[dict[str, Any]] = []
        self._running = False
        self._thread: threading.Thread | None = None
        self._health_check_fn: Callable[[str], bool] | None = None
        self._dns_update_fn: Callable[[str, str], None] | None = None

    # ── Configuration ──────────────────────────────────────────

    def set_health_check_fn(self, fn: Callable[[str], bool]) -> None:
        """Set custom health check function (region_name -> is_healthy)."""
        self._health_check_fn = fn

    def set_dns_update_fn(self, fn: Callable[[str, str], None]) -> None:
        """Set custom DNS update function (region_name, target_host)."""
        self._dns_update_fn = fn

    # ── Health Checks ──────────────────────────────────────────

    def check_health(self, region_name: str | None = None) -> list[HealthCheckResult]:
        """Run health checks on one or all regions."""
        targets = [region_name] if region_name else list(REGIONS.keys())
        results: list[HealthCheckResult] = []

        for name in targets:
            result = self._check_single_region(name)
            results.append(result)
            self._process_health_result(result)

        return results

    def _check_single_region(self, region_name: str) -> HealthCheckResult:
        region = get_region(region_name)
        if region is None:
            return HealthCheckResult(
                region_name=region_name,
                status=RegionStatus.DOWN,
                error="Region not found",
            )

        start = time.time()
        try:
            if self._health_check_fn:
                is_healthy = self._health_check_fn(region_name)
            else:
                is_healthy = self._default_health_check(region_name)
            latency = (time.time() - start) * 1000

            if is_healthy and latency <= region.latency_threshold_ms:
                return HealthCheckResult(
                    region_name=region_name,
                    status=RegionStatus.HEALTHY,
                    latency_ms=latency,
                )
            elif is_healthy:
                return HealthCheckResult(
                    region_name=region_name,
                    status=RegionStatus.DEGRADED,
                    latency_ms=latency,
                )
            else:
                return HealthCheckResult(
                    region_name=region_name,
                    status=RegionStatus.DOWN,
                    latency_ms=latency,
                    error="Health check returned unhealthy",
                )
        except Exception as e:
            return HealthCheckResult(
                region_name=region_name,
                status=RegionStatus.DOWN,
                error=str(e),
            )

    def _default_health_check(self, region_name: str) -> bool:
        region = get_region(region_name)
        if region is None:
            return False
        return region.is_active

    def _process_health_result(self, result: HealthCheckResult) -> None:
        name = result.region_name

        if result.status == RegionStatus.DOWN:
            self._consecutive_failures[name] += 1
            if (
                self._consecutive_failures[name] >= self.CONSECUTIVE_FAILURES_THRESHOLD
                and self._region_status[name] != RegionStatus.DOWN
            ):
                self._region_status[name] = RegionStatus.DOWN
                self.trigger_failover(name)
        elif result.status == RegionStatus.HEALTHY:
            self._consecutive_failures[name] = 0
            if self._region_status[name] == RegionStatus.DOWN:
                self._region_status[name] = RegionStatus.HEALTHY
        else:
            self._consecutive_failures[name] = 0
            self._region_status[name] = result.status

    # ── Failover ───────────────────────────────────────────────

    def trigger_failover(self, failed_region: str) -> FailoverEvent | None:
        """Trigger failover from a failed region to its next target."""
        targets = get_failover_targets(failed_region)
        target_region = None

        for candidate in targets:
            if self._region_status.get(candidate) == RegionStatus.HEALTHY:
                target_region = candidate
                break

        if target_region is None:
            self._emit_notification(
                "failover_failed",
                f"No healthy target for {failed_region}",
            )
            return None

        event = FailoverEvent(
            source_region=failed_region,
            target_region=target_region,
            reason=f"Consecutive failures exceeded threshold for {failed_region}",
        )
        self._failover_events.append(event)
        self._region_status[failed_region] = RegionStatus.FAILOVER

        target = get_region(target_region)
        if target and self._dns_update_fn:
            self._dns_update_fn(failed_region, target.primary_host)

        self._emit_notification(
            "failover",
            f"Failover: {failed_region} -> {target_region}",
        )
        return event

    # ── Restore Primary ────────────────────────────────────────

    def restore_primary(self, region_name: str) -> bool:
        """Restore a region to primary status after cooldown."""
        now = time.time()
        last = self._last_restore.get(region_name, 0.0)

        if now - last < self.RESTORE_COOLDOWN:
            self._emit_notification(
                "restore_cooldown",
                f"Restore for {region_name} still in cooldown",
            )
            return False

        health = self._check_single_region(region_name)
        if health.status not in (RegionStatus.HEALTHY, RegionStatus.DEGRADED):
            self._emit_notification(
                "restore_failed",
                f"Cannot restore {region_name}: {health.status.value}",
            )
            return False

        self._region_status[region_name] = RegionStatus.RESTORING
        region = get_region(region_name)
        if region and self._dns_update_fn:
            self._dns_update_fn(region_name, region.primary_host)

        self._region_status[region_name] = RegionStatus.HEALTHY
        self._last_restore[region_name] = now

        for event in self._failover_events:
            if event.source_region == region_name and not event.restored:
                event.restored = True
                break

        self._emit_notification(
            "restore",
            f"Primary restored: {region_name}",
        )
        return True

    # ── Background Polling ─────────────────────────────────────

    def start_polling(self) -> None:
        """Start background health check polling."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop_polling(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.HEALTH_CHECK_INTERVAL + 2)
            self._thread = None

    def _poll_loop(self) -> None:
        while self._running:
            self.check_health()
            time.sleep(self.HEALTH_CHECK_INTERVAL)

    # ── Notifications ──────────────────────────────────────────

    def _emit_notification(self, event_type: str, message: str) -> None:
        self._notifications.append(
            {
                "type": event_type,
                "message": message,
                "timestamp": time.time(),
            }
        )

    def get_notifications(self) -> list[dict[str, Any]]:
        return list(self._notifications)

    def get_failover_events(self) -> list[FailoverEvent]:
        return list(self._failover_events)

    def get_status(self) -> dict[str, str]:
        return {k: v.value for k, v in self._region_status.items()}
