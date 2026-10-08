"""Subagent 24 - Orquestador de Monitoreo.

Consolida varias señales de monitorización en un veredicto único.
"""

from typing import Any

try:  # pragma: no cover - resolves when phone/ is a package
    from ..core._loader import load_metrics
except ImportError:  # pragma: no cover - imported by file path
    import importlib.util as _ilu
    import pathlib as _pl

    def load_metrics():
        target = _pl.Path(__file__).resolve().parents[1] / "core" / "_loader.py"
        spec = _ilu.spec_from_file_location("_aig_loader", target)
        module = _ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.load_metrics()


_m = load_metrics()


class Subagent24:
    """Consolida varias señales de monitorización en un veredicto único."""

    def __init__(self, name: str = "Subagent_24"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    #: Signals the orchestrator expects, in the order they are reported.
    SIGNALS = ("cpu_percent", "memory_percent", "latency_ms", "error_rate")

    def orchestrate_monitoring(self, samples: dict[str, Any] | None = None) -> dict:
        """Roll individual signals into one verdict with named coverage.

        Args:
            samples: metric name to value; any subset of :attr:`SIGNALS`.

        Returns:
            The consolidated verdict plus per-signal detail and which signals
            are missing, so partial coverage is visible instead of implied.
        """
        samples = samples or {}
        detail: dict[str, Any] = {}
        verdicts: list[str] = []
        missing: list[str] = []
        for signal in self.SIGNALS:
            if signal not in samples:
                missing.append(signal)
                continue
            report = _m.summarise(signal, samples.get(signal), source="orchestrate_monitoring")
            detail[signal] = report
            if report.get("verdict") not in (None, "unknown"):
                verdicts.append(report["verdict"])
        if not verdicts:
            return {
                "status": "insufficient_data",
                "required_input": f"at least one of {list(self.SIGNALS)}",
                "missing_signals": missing,
            }
        for level in ("critical", "bad", "acceptable"):
            if level in verdicts:
                overall = level
                break
        else:
            overall = "good"
        return {
            "status": "measured",
            "overall": overall,
            "coverage": f"{len(verdicts)}/{len(self.SIGNALS)}",
            "signals": detail,
            "missing_signals": missing,
            "alert_routing": "centralized",
        }

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
monitoring_orchestrator = Subagent24()
