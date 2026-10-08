"""Subagent 7 - Monitor de Rendimiento.

Mide el rendimiento con muestras reales y clasifica cada indicador.
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
summarise = _m.summarise
classify = _m.classify


class Subagent7:
    """Mide el rendimiento con muestras reales y clasifica cada indicador."""

    def __init__(self, name: str = "Subagent_7"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def monitor_performance(self, samples: dict[str, Any] | None = None) -> dict:
        """Classify caller-supplied performance samples.

        Args:
            samples: metric name to value, e.g.
                ``{"cpu_percent": 82, "memory_percent": 61, "latency_ms": 240}``.

        Returns:
            One report per metric plus an overall verdict. Missing metrics are
            reported as ``insufficient_data`` rather than defaulted, so a
            partial reading never looks like a healthy system.
        """
        samples = samples or {}
        reports = {
            name: summarise(name, samples.get(name), source="monitor_performance")
            for name in ("cpu_percent", "memory_percent", "latency_ms")
        }
        verdicts = [
            r["verdict"] for r in reports.values() if r.get("verdict") not in (None, "unknown")
        ]
        if not verdicts:
            return {
                "status": "insufficient_data",
                "required_input": "at least one of cpu_percent, memory_percent, latency_ms",
                "metrics": reports,
            }
        if "critical" in verdicts:
            overall = "critical"
        elif "bad" in verdicts:
            overall = "bad"
        elif "acceptable" in verdicts:
            overall = "acceptable"
        else:
            overall = "good"
        return {
            "status": "measured",
            "overall": overall,
            "metrics": reports,
            "measured_count": len(verdicts),
        }

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
performance_monitor = Subagent7()
