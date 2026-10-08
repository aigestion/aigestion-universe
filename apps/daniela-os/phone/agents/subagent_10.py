"""Subagent 10 - Monitor de Caudal.

Mide el caudal a partir de marcas de tiempo reales.
"""

from collections.abc import Sequence
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


class Subagent10:
    """Mide el caudal a partir de marcas de tiempo reales."""

    def __init__(self, name: str = "Subagent_10"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def measure_throughput(
        self,
        events: Sequence[float] | None = None,
        window_seconds: float | None = None,
        latencies_ms: Sequence[float] | None = None,
    ) -> dict:
        """Compute throughput from real timestamps.

        Args:
            events: event timestamps in seconds; at least two are required.
            window_seconds: measurement window, inferred from the timestamps
                when omitted.
            latencies_ms: optional per-request latencies for percentiles.

        Returns:
            Events per second plus latency statistics. Without timestamps this
            returns ``insufficient_data`` instead of a nominal figure.
        """
        rate = _m.measure_rate(list(events or []), window_seconds)
        report: dict[str, Any] = {"throughput": rate}
        if latencies_ms:
            numbers = [v for v in latencies_ms if isinstance(v, (int, float))]
            report["latency"] = {
                "status": "measured",
                "mean_ms": _m.mean(numbers),
                "p50_ms": _m.percentile(numbers, 0.50),
                "p95_ms": _m.percentile(numbers, 0.95),
                "p99_ms": _m.percentile(numbers, 0.99),
                "samples": len(numbers),
            }
        if rate.get("status") == "insufficient_data":
            return {
                "status": "insufficient_data",
                "required_input": "at least 2 event timestamps",
                **report,
            }
        return {"status": "measured", **report}

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
throughput_monitor = Subagent10()
