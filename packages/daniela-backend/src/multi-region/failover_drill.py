"""
aig Multi-Region Failover Drill
=======================================
Scriptable failover drill: pick a victim region, simulate its primary
going down, verify traffic shifts to the next region in failover order,
verify restore with cooldown, and emit a drill report dict with timings
and pass/fail.

Safe by default: simulation only. Pass real_drain=True to perform real
shifts on the injected manager/DNS table.

Autor: aig Team
"""

from __future__ import annotations

import time
from typing import Any

try:
    from .config import REGIONS, get_failover_targets
except ImportError:
    from config import REGIONS, get_failover_targets

try:
    from .failover import FailoverManager, RegionStatus
except ImportError:
    from failover import FailoverManager, RegionStatus

try:
    from .dns_sim import DnsWeightTable
except ImportError:
    from dns_sim import DnsWeightTable


class FailoverDrill:
    """Runs scriptable, simulation-first failover drills."""

    def __init__(
        self,
        manager: FailoverManager | None = None,
        dns: DnsWeightTable | None = None,
    ) -> None:
        self.manager = manager or FailoverManager(local_region="eu-west")
        self.dns = dns or DnsWeightTable()

    # ── Main entry point ───────────────────────────────────────

    def run(self, victim_region: str, real_drain: bool = False) -> dict[str, Any]:
        """Run a drill against victim_region.

        Simulation (default) never mutates self.manager / self.dns.
        real_drain=True performs a real failover + DNS weight shift.
        """
        wall_start = time.time()
        perf_start = time.perf_counter()
        mode = "real" if real_drain else "simulation"
        steps: list[dict[str, Any]] = []
        failover_ms = 0.0
        restore_ms = 0.0
        cooldown_respected = False
        target: str | None = None

        # Step 1 — validate victim, resolve next in failover order.
        t = time.perf_counter()
        if victim_region not in REGIONS:
            steps.append(
                self._step(
                    "validate", False, (time.perf_counter() - t) * 1000,
                    {"error": f"Unknown region: {victim_region}"},
                )
            )
            return self._report(
                victim_region, None, mode, False, steps,
                failover_ms, restore_ms, False, wall_start, perf_start,
            )
        candidates = get_failover_targets(victim_region)
        if not candidates:
            steps.append(
                self._step(
                    "validate", False, (time.perf_counter() - t) * 1000,
                    {"error": f"No failover targets for {victim_region}"},
                )
            )
            return self._report(
                victim_region, None, mode, False, steps,
                failover_ms, restore_ms, False, wall_start, perf_start,
            )
        target = candidates[0]
        steps.append(
            self._step(
                "validate", True, (time.perf_counter() - t) * 1000,
                {"victim": victim_region, "target": target, "chain": candidates},
            )
        )

        # Step 2 — simulate primary down, verify failover target.
        t = time.perf_counter()
        sim = FailoverManager(local_region=victim_region)
        sim.set_health_check_fn(lambda r, _v=victim_region: r != _v)
        for _ in range(FailoverManager.CONSECUTIVE_FAILURES_THRESHOLD):
            sim.check_health(victim_region)
        events = [
            e for e in sim.get_failover_events()
            if e.source_region == victim_region
        ]
        failover_ok = bool(events) and events[0].target_region == target
        failover_ms = (time.perf_counter() - t) * 1000
        steps.append(
            self._step(
                "failover", failover_ok, failover_ms,
                {
                    "expected_target": target,
                    "actual_target": events[0].target_region if events else None,
                },
            )
        )

        # Step 3 — verify traffic shifts to next in failover order.
        t = time.perf_counter()
        before = self.dns.get_table()
        if real_drain:
            self.manager._region_status[victim_region] = RegionStatus.DOWN
            real_event = self.manager.trigger_failover(victim_region)
            after = self.dns.shift_weight(victim_region, target)
            shift_ok = (
                real_event is not None
                and real_event.target_region == target
                and after.get(victim_region) == 0.0
            )
            detail: dict[str, Any] = {
                "mode": "real",
                "event_target": real_event.target_region if real_event else None,
                "weights": after,
            }
        else:
            preview = dict(before)
            moved = preview.get(victim_region, 0.0)
            preview[victim_region] = 0.0
            preview[target] = round(preview.get(target, 0.0) + moved, 6)
            untouched = self.dns.get_table() == before
            no_new_events = len(
                [e for e in self.manager.get_failover_events()
                 if e.source_region == victim_region]
            ) == 0
            shift_ok = preview[victim_region] == 0.0 and untouched
            detail = {
                "mode": "simulation",
                "preview_weights": preview,
                "real_weights_untouched": untouched,
                "real_manager_untouched": no_new_events,
            }
        steps.append(
            self._step("traffic_shift", shift_ok, (time.perf_counter() - t) * 1000, detail)
        )

        # Step 4 — verify restore with cooldown (isolated sim).
        t = time.perf_counter()
        sim.set_health_check_fn(lambda r: True)
        sim._last_restore[victim_region] = 0.0
        first = sim.restore_primary(victim_region)
        second = sim.restore_primary(victim_region)
        cooldown_respected = first is True and second is False
        restore_ms = (time.perf_counter() - t) * 1000
        steps.append(
            self._step(
                "restore", cooldown_respected, restore_ms,
                {
                    "first_restore": first,
                    "second_restore_blocked": not second,
                    "cooldown_s": sim.RESTORE_COOLDOWN,
                },
            )
        )

        passed = all(s["passed"] for s in steps)
        report = self._report(
            victim_region, target, mode, passed, steps,
            failover_ms, restore_ms, cooldown_respected,
            wall_start, perf_start,
        )
        if real_drain:
            report["restore_pending"] = True
            report["note"] = (
                "Real drain performed; operator must restore primary and weights."
            )
        return report

    # ── Report helpers ─────────────────────────────────────────

    @staticmethod
    def _step(
        name: str, passed: bool, duration_ms: float, detail: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "name": name,
            "passed": bool(passed),
            "duration_ms": round(duration_ms, 3),
            "detail": detail,
        }

    @staticmethod
    def _report(
        victim: str,
        target: str | None,
        mode: str,
        passed: bool,
        steps: list[dict[str, Any]],
        failover_ms: float,
        restore_ms: float,
        cooldown_respected: bool,
        wall_start: float,
        perf_start: float,
    ) -> dict[str, Any]:
        return {
            "drill_id": f"drill-{victim}-{int(wall_start)}",
            "victim": victim,
            "target": target,
            "mode": mode,
            "passed": bool(passed),
            "steps": steps,
            "timings_ms": {
                "total": round((time.perf_counter() - perf_start) * 1000, 3),
                "failover": round(failover_ms, 3),
                "restore": round(restore_ms, 3),
            },
            "cooldown_respected": bool(cooldown_respected),
            "timestamp": wall_start,
        }


def run_drill(victim_region: str, real_drain: bool = False) -> dict[str, Any]:
    """Convenience helper: run a drill with default manager/DNS."""
    return FailoverDrill().run(victim_region, real_drain=real_drain)
