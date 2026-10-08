"""Experiment runner with blast radius, steady-state checks, rollback, dry-run."""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from .faults import Fault, create_fault


@dataclass
class BlastRadius:
    """Defines how far an experiment may reach."""

    services: list[str] = field(default_factory=lambda: ["default"])
    max_targets: int = 1
    environment: str = "staging"
    allowed_envs: Sequence[str] = ("staging", "dev", "test")

    def is_allowed(self) -> bool:
        if self.environment not in tuple(self.allowed_envs):
            return False
        if len(self.services) > self.max_targets:
            return False
        return True

    def violation_reason(self) -> str | None:
        if self.environment not in tuple(self.allowed_envs):
            return f"environment {self.environment!r} not in allowed {list(self.allowed_envs)}"
        if len(self.services) > self.max_targets:
            return f"{len(self.services)} services exceed max_targets={self.max_targets}"
        return None


@dataclass
class FaultSchedule:
    fault: Fault
    delay_seconds: float = 0.0
    duration_seconds: float | None = None

    def effective_duration(self) -> float:
        return float(self.duration_seconds) if self.duration_seconds is not None else float(self.fault.duration)


@dataclass
class ExperimentResult:
    experiment_name: str
    success: bool
    dry_run: bool
    faults_injected: list[str] = field(default_factory=list)
    steady_state_before: bool | None = None
    steady_state_after: bool | None = None
    rollback_performed: bool = False
    error: str | None = None
    started_at: float = 0.0
    ended_at: float = 0.0
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_schedule(
    faults: Sequence[Fault | FaultSchedule | dict[str, Any]],
) -> list[FaultSchedule]:
    out: list[FaultSchedule] = []
    for item in faults or []:
        if isinstance(item, FaultSchedule):
            out.append(item)
        elif isinstance(item, Fault):
            out.append(FaultSchedule(fault=item))
        elif isinstance(item, dict):
            d = dict(item)
            fault = d.pop("fault", None)
            if isinstance(fault, Fault):
                out.append(
                    FaultSchedule(
                        fault=fault,
                        delay_seconds=float(d.get("delay_seconds", d.get("delay", 0.0))),
                        duration_seconds=d.get("duration_seconds", d.get("duration")),
                    )
                )
            else:
                ftype = d.pop("type", d.pop("fault_type", "latency_injection"))
                out.append(
                    FaultSchedule(
                        fault=create_fault(
                            ftype,
                            target=d.pop("target", "default"),
                            duration=float(d.pop("duration", d.pop("duration_seconds", 60.0))),
                            **d.get("params", d),
                        ),
                        delay_seconds=float(d.get("delay_seconds", d.get("delay", 0.0))),
                    )
                )
        else:
            raise TypeError(f"unsupported fault entry: {item!r}")
    return out


class Experiment:
    """Runs a fault schedule with steady-state checks and automatic rollback."""

    def __init__(
        self,
        name: str,
        faults: Sequence[Fault | FaultSchedule | dict[str, Any]] | None = None,
        steady_state_check: Callable[[], bool] | None = None,
        blast_radius: BlastRadius | None = None,
        dry_run: bool = True,
        auto_rollback: bool = True,
    ) -> None:
        self.name = name
        self.schedule = _normalize_schedule(faults or [])
        self.steady_state_check = steady_state_check
        self.blast_radius = blast_radius or BlastRadius()
        self.dry_run = bool(dry_run)
        self.auto_rollback = bool(auto_rollback)

    def _check_steady_state(self) -> bool:
        if self.steady_state_check is None:
            return True
        result = self.steady_state_check()
        return bool(result)

    def _rollback(self, injected: list[Fault]) -> bool:
        for fault in injected:
            try:
                fault.recover()
            except Exception:
                pass
        return True  # rollback was performed (attempted)

    def run(self) -> ExperimentResult:
        started = time.time()
        result = ExperimentResult(
            experiment_name=self.name,
            success=False,
            dry_run=self.dry_run,
            started_at=started,
        )
        try:
            # Blast-radius enforcement (skipped for dry-run: dry-run does nothing anyway).
            if not self.dry_run:
                reason = self.blast_radius.violation_reason()
                if reason is not None:
                    result.error = f"blast radius violation: {reason}"
                    result.success = False
                    result.ended_at = time.time()
                    result.duration_seconds = result.ended_at - started
                    return result

            try:
                result.steady_state_before = self._check_steady_state()
            except Exception as exc:
                result.error = f"steady-state (before) raised: {exc}"
                result.success = False
                result.ended_at = time.time()
                result.duration_seconds = result.ended_at - started
                return result

            if not result.steady_state_before:
                result.error = "steady-state check failed before injection"
                result.success = False
                result.ended_at = time.time()
                result.duration_seconds = result.ended_at - started
                return result

            if self.dry_run:
                # Dry-run: report what WOULD run, touch nothing.
                result.faults_injected = []
                result.steady_state_after = result.steady_state_before
                result.rollback_performed = False
                result.success = True
                result.ended_at = time.time()
                result.duration_seconds = result.ended_at - started
                return result

            injected: list[Fault] = []
            try:
                for entry in self.schedule:
                    if entry.delay_seconds and entry.delay_seconds > 0:
                        time.sleep(min(float(entry.delay_seconds), 3600.0))
                    entry.fault.inject()
                    injected.append(entry.fault)
                    result.faults_injected.append(entry.fault.name)
                try:
                    result.steady_state_after = self._check_steady_state()
                except Exception as exc:
                    result.error = f"steady-state (after) raised: {exc}"
                    result.steady_state_after = False
                result.success = bool(result.steady_state_after) and result.error is None
            finally:
                if self.auto_rollback and injected:
                    self._rollback(injected)
                    result.rollback_performed = True
            result.ended_at = time.time()
            result.duration_seconds = result.ended_at - started
            return result
        except Exception as exc:
            result.error = str(exc)
            result.success = False
            result.ended_at = time.time()
            result.duration_seconds = result.ended_at - started
            return result
