"""Subagent 15 - Medidor de Eficiencia.

Calcula la eficiencia real a partir de metricas observadas.
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


class Subagent15:
    """Calcula la eficiencia real a partir de metricas observadas."""

    def __init__(self, name: str = "Subagent_15"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def track_efficiency(self, samples: dict[str, Any] | None = None) -> dict:
        """Score efficiency from measured indicators.

        Args:
            samples: any of ``cpu_percent``, ``memory_percent``,
                ``latency_ms``, ``error_rate``.

        Returns:
            A 0-100 score derived from the indicators supplied, with the
            weakest one named. The score is only produced when at least one
            indicator was actually measured.
        """
        metrics = ("cpu_percent", "memory_percent", "latency_ms", "error_rate")
        samples = samples or {}
        parts: list[dict[str, Any]] = []
        for name in metrics:
            if name in samples:
                parts.append(_m.summarise(name, samples.get(name), source="track_efficiency"))
        if not parts:
            return {
                "status": "insufficient_data",
                "required_input": f"any of {list(metrics)}",
                "score": None,
            }
        penalty = {"good": 0.0, "acceptable": 0.2, "bad": 0.45, "critical": 0.8}
        score = max(
            0.0, 100.0 * (1.0 - sum(penalty.get(p["verdict"], 0.5) for p in parts) / len(parts))
        )
        weakest = min(
            parts, key=lambda p: p["value"] if p["metric"] == "error_rate" else -p["value"]
        )
        return {
            "status": "measured",
            "score": round(score, 2),
            "measured_metrics": [p["metric"] for p in parts],
            "metrics": {p["metric"]: p for p in parts},
            "weakest": weakest["metric"],
        }

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
efficiency_tracker = Subagent15()
