"""Subagent 20 - Gestor de Concurrencia.

Dimensiona la concurrencia a partir de la latencia observada.
"""


class Subagent20:
    """Dimensiona la concurrencia a partir de la latencia observada."""

    def __init__(self, name: str = "Subagent_20"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def optimize_concurrency(
        self,
        latency_ms: float | None = None,
        target_utilization: float = 0.8,
        max_threads: int | None = None,
    ) -> dict:
        """Size a concurrency budget from measured latency.

        Uses Little's Law: concurrency needed to sustain a target rate is the
        rate multiplied by the latency.

        Args:
            latency_ms: observed service time per unit.
            target_utilization: fraction of the budget to plan for, 0 to 1.
            max_threads: optional hard ceiling on the pool.

        Returns:
            Required, recommended and capped concurrency. Without a latency
            reading there is nothing to size against.
        """
        if latency_ms is None:
            return {"status": "insufficient_data", "required_input": "latency_ms"}
        if latency_ms <= 0:
            return {"status": "invalid_input", "error": "latency_ms must be positive"}
        if not 0 < target_utilization <= 1:
            return {"status": "invalid_input", "error": "target_utilization must be in (0, 1]"}
        rate_per_thread = 1000.0 / float(latency_ms)
        required = rate_per_thread / target_utilization
        recommended = max(2, int(-(-required // 1)))
        capped = max_threads is not None and recommended > int(max_threads)
        return {
            "status": "measured",
            "latency_ms": latency_ms,
            "target_utilization": target_utilization,
            "rps_per_thread": round(rate_per_thread, 4),
            "required_concurrency": round(required, 2),
            "recommended_threads": int(min(recommended, max_threads))
            if max_threads
            else recommended,
            "capped_by_max": capped,
        }

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
concurrency_manager = Subagent20()
