"""Subagent 8 - Detector de Cuellos de Botella.

Detecta cuellos de botella a partir de mediciones reales.
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


class Subagent8:
    """Detecta cuellos de botella a partir de mediciones reales."""

    def __init__(self, name: str = "Subagent_8"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    #: A metric counts as a bottleneck once it passes the "bad" threshold.
    _BOTTLENECK_METRICS = (
        "cpu_percent",
        "memory_percent",
        "latency_ms",
        "queue_depth",
        "disk_percent",
    )

    def detect_bottlenecks(self, samples: dict[str, Any] | None = None) -> dict:
        """Identify which measured resource is saturated.

        Args:
            samples: metric name to value.

        Returns:
            The saturated metrics, worst first. An empty list means nothing
            crossed the threshold, which is a real result and not the same as
            having measured nothing.
        """
        samples = samples or {}
        found: list[dict[str, Any]] = []
        checked: list[str] = []
        for metric in self._BOTTLENECK_METRICS:
            if metric not in samples:
                continue
            report = _m.summarise(metric, samples.get(metric), source="detect_bottlenecks")
            checked.append(metric)
            if report.get("verdict") in ("bad", "critical"):
                found.append(
                    {"metric": metric, "value": report["value"], "verdict": report["verdict"]}
                )
        if not checked:
            return {
                "status": "insufficient_data",
                "required_input": f"any of {list(self._BOTTLENECK_METRICS)}",
                "bottlenecks": [],
            }
        found.sort(key=lambda item: -(item["value"] or 0))
        return {
            "status": "measured",
            "bottlenecks": found,
            "worst": found[0] if found else None,
            "checked_metrics": checked,
        }

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
bottleneck_detector = Subagent8()
