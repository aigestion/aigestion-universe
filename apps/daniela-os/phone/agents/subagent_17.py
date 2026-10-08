"""Subagent 17 - Impulsor de Caudal.

Cuantifica el caudal adicional posible segun capacidad libre.
"""

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


class Subagent17:
    """Cuantifica el caudal adicional posible segun capacidad libre."""

    def __init__(self, name: str = "Subagent_17"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def boost_throughput(
        self,
        current_rps: float | None = None,
        workers: int | None = None,
        max_workers: int | None = None,
    ) -> dict:
        """Estimate the throughput gain from adding workers.

        Args:
            current_rps: measured requests per second today.
            workers: current worker count.
            max_workers: upper bound on workers available.

        Returns:
            Per-worker throughput, the projected rate at full scale and the
            gain. Requires all three inputs; a projection from any subset would
            be a guess.
        """
        if current_rps is None or not workers or not max_workers:
            return {
                "status": "insufficient_data",
                "required_input": "current_rps, workers and max_workers",
            }
        if workers <= 0 or max_workers <= 0:
            return {"status": "invalid_input", "error": "worker counts must be positive"}
        if max_workers < workers:
            return {
                "status": "invalid_input",
                "error": "max_workers is below the current worker count",
            }
        per_worker = float(current_rps) / workers
        projected = per_worker * max_workers
        return {
            "status": "measured",
            "current_rps": current_rps,
            "workers": workers,
            "max_workers": max_workers,
            "rps_per_worker": round(per_worker, 4),
            "projected_rps": round(projected, 4),
            "gain_percent": round((projected - float(current_rps)) / float(current_rps) * 100.0, 2)
            if current_rps
            else None,
            "workers_to_add": max_workers - workers,
        }

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
throughput_booster = Subagent17()
