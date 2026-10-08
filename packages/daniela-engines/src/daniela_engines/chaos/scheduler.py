"""Chaos scheduler: cron-like schedule, allowed windows, armed flag, kill switch."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


def _parse_field(expr: str, minimum: int, maximum: int) -> set[int]:
    """Parse one cron field into a set of matching ints. Supports *, */n, a,b, a-b, n."""
    expr = expr.strip()
    values: set[int] = set()
    if expr == "*":
        return set(range(minimum, maximum + 1))
    for part in expr.split(","):
        part = part.strip()
        if not part:
            continue
        if part.startswith("*/"):
            step = int(part[2:])
            values.update(range(minimum, maximum + 1, step))
        elif "-" in part and "/" not in part:
            lo_s, hi_s = part.split("-", 1)
            lo, hi = int(lo_s), int(hi_s)
            values.update(range(max(lo, minimum), min(hi, maximum) + 1))
        elif part == "*":
            values.update(range(minimum, maximum + 1))
        else:
            values.add(int(part))
    return {v for v in values if minimum <= v <= maximum}


def cron_matches(cron_expr: str, now: datetime | None = None) -> bool:
    """Match a 5-field cron (minute hour dom month dow) against `now` (UTC)."""
    now = now or datetime.now(UTC)
    # cron dow: 0-6 (Sun=0); python weekday Mon=0..Sun=6 -> convert
    cron_dow = (now.weekday() + 1) % 7
    fields = cron_expr.strip().split()
    if len(fields) != 5:
        raise ValueError(f"cron expression must have 5 fields, got: {cron_expr!r}")
    minute, hour, dom, month, dow = fields
    checks = [
        (minute, now.minute, 0, 59),
        (hour, now.hour, 0, 23),
        (dom, now.day, 1, 31),
        (month, now.month, 1, 12),
        (dow, cron_dow, 0, 6),
    ]
    for expr, current, lo, hi in checks:
        if current not in _parse_field(expr, lo, hi):
            return False
    return True


@dataclass
class ScheduledExperiment:
    name: str
    cron: str
    experiment: Any = None
    last_run: str | None = None


class ChaosScheduler:
    """Safety-first scheduler. Deny-by-default: must be armed, in-window, kill-switch off."""

    def __init__(
        self,
        allowed_windows: list[tuple[int, int]] | None = None,
        armed: bool = False,
    ) -> None:
        # allowed_windows: list of (start_hour_incl, end_hour_excl) in UTC.
        self.allowed_windows: list[tuple[int, int]] = list(allowed_windows) if allowed_windows else [(9, 17)]
        self._armed = bool(armed)
        self._kill_switch = False
        self.scheduled: list[ScheduledExperiment] = []

    # -- safety controls -----------------------------------------------------
    @property
    def is_armed(self) -> bool:
        return self._armed

    @property
    def kill_switch_engaged(self) -> bool:
        return self._kill_switch

    def arm(self) -> bool:
        self._armed = True
        return True

    def disarm(self) -> bool:
        self._armed = False
        return True

    def engage_kill_switch(self) -> bool:
        self._kill_switch = True
        return True

    def release_kill_switch(self) -> bool:
        self._kill_switch = False
        return True

    def set_allowed_windows(self, windows: list[tuple[int, int]]) -> None:
        self.allowed_windows = list(windows)

    # -- gating --------------------------------------------------------------
    def is_window_allowed(self, now: datetime | None = None) -> bool:
        if not self.allowed_windows:
            return False
        now = now or datetime.now(UTC)
        hour = now.hour
        for start, end in self.allowed_windows:
            s, e = int(start), int(end)
            if s <= e:
                if s <= hour < e or (s == e == hour):
                    return True
            else:  # overnight window, e.g. (22, 6)
                if hour >= s or hour < e:
                    return True
        return False

    def can_run(self, now: datetime | None = None) -> bool:
        """True only when armed AND kill-switch off AND inside an allowed window."""
        if not self._armed:
            return False
        if self._kill_switch:
            return False
        if not self.is_window_allowed(now):
            return False
        return True

    # -- scheduling ----------------------------------------------------------
    def add_schedule(self, name: str, experiment: Any, cron: str) -> ScheduledExperiment:
        # Validate cron eagerly.
        cron_matches(cron, datetime.now(UTC))
        entry = ScheduledExperiment(name=name, cron=cron, experiment=experiment)
        self.scheduled.append(entry)
        return entry

    def due_experiments(self, now: datetime | None = None) -> list[ScheduledExperiment]:
        now = now or datetime.now(UTC)
        if not self.can_run(now):
            return []
        return [s for s in self.scheduled if cron_matches(s.cron, now)]

    def safety_status(self) -> dict[str, Any]:
        return {
            "armed": self._armed,
            "kill_switch_engaged": self._kill_switch,
            "kill_switch": "engaged" if self._kill_switch else "released",
            "allowed_windows": [[s, e] for s, e in self.allowed_windows],
            "scheduled_count": len(self.scheduled),
        }
