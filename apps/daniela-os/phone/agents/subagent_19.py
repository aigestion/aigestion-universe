"""Subagent 19 - Optimizador de Memoria.

Calcula el presupuesto de memoria segun la carga medida.
"""

from typing import Any


class Subagent19:
    """Calcula el presupuesto de memoria segun la carga medida."""

    def __init__(self, name: str = "Subagent_19"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def optimize_memory(
        self,
        used_bytes: int | None = None,
        total_bytes: int | None = None,
        growth_bytes_per_period: int | None = None,
    ) -> dict:
        """Report memory headroom and when it will run out.

        Args:
            used_bytes: memory currently in use.
            total_bytes: memory available.
            growth_bytes_per_period: optional growth rate for a projection.

        Returns:
            Used percentage, free bytes and, when growth is given, the periods
            until exhaustion. No usage figure is invented when the readings are
            absent.
        """
        if used_bytes is None or total_bytes is None:
            return {"status": "insufficient_data", "required_input": "used_bytes and total_bytes"}
        total = int(total_bytes)
        if total <= 0:
            return {"status": "invalid_input", "error": "total_bytes must be positive"}
        used = int(used_bytes)
        free = total - used
        percent = used / total * 100.0
        result: dict[str, Any] = {
            "status": "measured",
            "used_bytes": used,
            "total_bytes": total,
            "free_bytes": free,
            "used_percent": round(percent, 2),
            "verdict": "critical" if percent >= 92 else ("bad" if percent >= 80 else "ok"),
        }
        if growth_bytes_per_period:
            growth = int(growth_bytes_per_period)
            result["growth_bytes_per_period"] = growth
            result["periods_until_exhausted"] = round(free / growth, 2) if growth > 0 else None
        return result

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
memory_optimizer = Subagent19()
