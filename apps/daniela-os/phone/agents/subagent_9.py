"""Subagent 9 - Verificador de Escalabilidad.

Evalua si el sistema puede escalar segun su carga medida.
"""


class Subagent9:
    """Evalua si el sistema puede escalar segun su carga medida."""

    def __init__(self, name: str = "Subagent_9"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def check_scalability(
        self,
        current_load: float | None = None,
        capacity: float | None = None,
        headroom_threshold: float = 20.0,
    ) -> dict:
        """Compare measured load against measured capacity.

        Args:
            current_load: observed utilisation, same unit as ``capacity``.
            capacity: maximum the system carries, same unit.
            headroom_threshold: minimum spare percentage treated as healthy.

        Returns:
            Headroom, verdict and a recommendation derived from the ratio.
            Without both readings it returns ``insufficient_data`` rather than
            asserting a load level it did not observe.
        """
        if current_load is None or capacity is None:
            return {
                "status": "insufficient_data",
                "required_input": "both current_load and capacity",
                "headroom_threshold": headroom_threshold,
            }
        capacity = float(capacity)
        if capacity <= 0:
            return {"status": "invalid_input", "error": "capacity must be greater than 0"}
        usage = float(current_load) / capacity * 100.0
        headroom = 100.0 - usage
        if headroom < headroom_threshold:
            verdict, action = "needs_scaling", "add capacity or shed load"
        elif headroom < headroom_threshold * 3:
            verdict, action = "tight", "plan capacity increase"
        else:
            verdict, action = "comfortable", "no action"
        return {
            "status": "measured",
            "usage_percent": round(usage, 2),
            "headroom_percent": round(headroom, 2),
            "verdict": verdict,
            "recommended_action": action,
            "current_load": current_load,
            "capacity": capacity,
        }

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
scalability_checker = Subagent9()
