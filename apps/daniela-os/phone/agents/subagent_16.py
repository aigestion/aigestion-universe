"""Subagent 16 - Optimizador de Cuellos de Botella.

Propone acciones segun el cuello de botella medido.
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


class Subagent16:
    """Propone acciones segun el cuello de botella medido."""

    def __init__(self, name: str = "Subagent_16"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    #: Which action addresses which saturated metric.
    _REMEDIES = {
        "cpu_percent": "scale out or reduce per-request work",
        "memory_percent": "free buffers or widen the heap",
        "latency_ms": "cache the slow dependency",
        "queue_depth": "add workers or batch the queue",
        "disk_percent": "compact or move cold data",
    }

    def eliminate_constraints(self, samples: dict[str, Any] | None = None) -> dict:
        """Recommend an action for each measured constraint.

        Args:
            samples: metric name to value.

        Returns:
            One remedy per saturated metric. Nothing saturated is reported as an
            explicit empty result, which is different from having no data.
        """
        samples = samples or {}
        actions: list[dict[str, Any]] = []
        checked: list[str] = []
        for metric in (
            "cpu_percent",
            "memory_percent",
            "latency_ms",
            "queue_depth",
            "disk_percent",
        ):
            if metric not in samples:
                continue
            report = _m.summarise(metric, samples.get(metric), source="eliminate_constraints")
            checked.append(metric)
            if report.get("verdict") in ("bad", "critical"):
                actions.append(
                    {
                        "metric": metric,
                        "value": report["value"],
                        "severity": report["verdict"],
                        "action": self._REMEDIES[metric],
                    }
                )
        if not checked:
            return {
                "status": "insufficient_data",
                "required_input": "at least one measured metric",
                "actions": [],
            }
        actions.sort(key=lambda item: -(item["value"] or 0))
        return {
            "status": "measured",
            "actions": actions,
            "highest_priority": actions[0]["metric"] if actions else None,
            "checked_metrics": checked,
        }

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
bottleneck_optimizer = Subagent16()
