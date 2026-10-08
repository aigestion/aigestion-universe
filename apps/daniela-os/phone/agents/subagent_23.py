"""Subagent 23 - Asesor de Escalado.

Recomienda escalar o no segun carga y capacidad medidas.
"""


class Subagent23:
    """Recomienda escalar o no segun carga y capacidad medidas."""

    def __init__(self, name: str = "Subagent_23"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def recommend_scaling(
        self,
        current_load: float | None = None,
        capacity: float | None = None,
        target_utilization: float = 0.7,
        cost_per_unit: float | None = None,
    ) -> dict:
        """Advise whether to scale out, and by how much.

        Args:
            current_load: measured utilisation.
            capacity: current capacity.
            target_utilization: utilisation to scale back down to.
            cost_per_unit: optional, to report the cost of the recommendation.

        Returns:
            The decision, the capacity to reach and the increment. Recommending
            no change when load is within target is a valid outcome.
        """
        if current_load is None or capacity is None:
            return {
                "status": "insufficient_data",
                "required_input": "current_load and capacity",
            }
        capacity = float(capacity)
        if capacity <= 0:
            return {"status": "invalid_input", "error": "capacity must be positive"}
        if not 0 < target_utilization <= 1:
            return {"status": "invalid_input", "error": "target_utilization must be in (0, 1]"}
        utilisation = float(current_load) / capacity
        if utilisation <= target_utilization:
            return {
                "status": "measured",
                "decision": "hold",
                "utilisation": round(utilisation, 4),
                "target_utilization": target_utilization,
                "rationale": "load is already within target",
            }
        required = float(current_load) / target_utilization
        increment = required - capacity
        recommendation = {
            "status": "measured",
            "decision": "scale_out",
            "utilisation": round(utilisation, 4),
            "target_utilization": target_utilization,
            "required_capacity": round(required, 4),
            "increment": round(increment, 4),
            "scale_factor": round(required / capacity, 4),
        }
        if cost_per_unit:
            recommendation["estimated_cost"] = round(increment * float(cost_per_unit), 4)
        return recommendation

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
scaling_advisor = Subagent23()
