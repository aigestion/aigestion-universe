"""Subagent 13 - Planificador de Capacidad.

Pronostica la capacidad necesaria a partir de una tendencia real.
"""

from collections.abc import Sequence


class Subagent13:
    """Pronostica la capacidad necesaria a partir de una tendencia real."""

    def __init__(self, name: str = "Subagent_13"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def forecast_capacity(
        self,
        history: Sequence[float] | None = None,
        periods_ahead: int = 4,
    ) -> dict:
        """Project future demand from observed history.

        Args:
            history: load per period, oldest first.
            periods_ahead: how many periods to project.

        Returns:
            The linear trend, the projection and the required capacity if the
            trend holds. Fewer than two points cannot define a trend, so the
            result is ``insufficient_data`` rather than a flat guess.
        """
        values = [float(v) for v in (history or []) if isinstance(v, (int, float))]
        if len(values) < 2:
            return {
                "status": "insufficient_data",
                "required_input": "at least 2 historical load values",
                "samples": len(values),
            }
        n = len(values)
        # Least squares slope and intercept over the sample index.
        mean_x = (n - 1) / 2.0
        mean_y = sum(values) / n
        denominator = sum((i - mean_x) ** 2 for i in range(n))
        slope = (
            sum((i - mean_x) * (v - mean_y) for i, v in enumerate(values)) / denominator
            if denominator
            else 0.0
        )
        intercept = mean_y - slope * mean_x
        projection = [
            round(intercept + slope * (n - 1 + step), 4) for step in range(1, periods_ahead + 1)
        ]
        return {
            "status": "measured",
            "samples": n,
            "trend_per_period": round(slope, 4),
            "direction": "growing" if slope > 0 else ("shrinking" if slope < 0 else "flat"),
            "projection": projection,
            "peak_projection": max(projection) if projection else None,
            "periods_ahead": periods_ahead,
        }

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
capacity_planner = Subagent13()
