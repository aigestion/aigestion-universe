"""Subagent 12 - Balanceador de Carga.

Reparte la carga entre servicios segun su capacidad real.
"""


class Subagent12:
    """Reparte la carga entre servicios segun su capacidad real."""

    def __init__(self, name: str = "Subagent_12"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def balance_load(
        self,
        pending: dict[str, float] | None = None,
        capacities: dict[str, float] | None = None,
    ) -> dict:
        """Distribute pending work across services proportionally to capacity.

        Args:
            pending: service name to units of work waiting.
            capacities: service name to units it can absorb.

        Returns:
            The allocation plus the resulting load per service. Work that
            exceeds total capacity is reported as unassignable rather than
            silently dropped, and a service at or below capacity is left alone.
        """
        pending = {k: float(v) for k, v in (pending or {}).items() if float(v) > 0}
        capacities = {k: float(v) for k, v in (capacities or {}).items() if float(v) > 0}
        if not pending:
            return {
                "status": "insufficient_data",
                "required_input": "a pending work map",
                "allocation": {},
            }
        if not capacities:
            return {
                "status": "insufficient_data",
                "required_input": "a capacity map matching the pending keys",
                "allocation": {},
            }

        total_capacity = sum(capacities.get(service, 0.0) for service in pending)
        total_pending = sum(pending.values())
        allocation = (
            {
                service: round(total_pending * capacities.get(service, 0.0) / total_capacity, 4)
                for service in pending
            }
            if total_capacity > 0
            else dict.fromkeys(pending, 0.0)
        )

        unassignable = round(max(0.0, total_pending - total_capacity), 4)
        utilisation = {
            service: round(allocation.get(service, 0.0) / capacities[service] * 100.0, 2)
            for service in allocation
            if service in capacities and capacities[service] > 0
        }
        return {
            "status": "measured",
            "allocation": allocation,
            "utilisation_percent": utilisation,
            "total_pending": total_pending,
            "total_capacity": total_capacity,
            "unassignable": unassignable,
        }

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
load_balancer = Subagent12()
