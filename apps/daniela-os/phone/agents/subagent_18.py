"""Subagent 18 - Reductor de Latencia.

Calcula la latencia restante tras una optimizacion aplicada.
"""


class Subagent18:
    """Calcula la latencia restante tras una optimizacion aplicada."""

    def __init__(self, name: str = "Subagent_18"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def reduce_latency(
        self,
        current_latency_ms: float | None = None,
        component_costs_ms: dict[str, float] | None = None,
        target_component: str | None = None,
        reduction: float = 0.8,
    ) -> dict:
        """Show how much latency disappears if one component improves.

        Args:
            current_latency_ms: measured end-to-end latency.
            component_costs_ms: per-component cost, which should sum to the
                current latency.
            target_component: the component to improve.
            reduction: fraction of that component's cost removed, 0 to 1.

        Returns:
            Before, after and the saving. The saving is bounded by the
            component's own cost, so the arithmetic cannot claim to remove more
            time than the component takes.
        """
        if current_latency_ms is None:
            return {"status": "insufficient_data", "required_input": "current_latency_ms"}
        if not component_costs_ms or not target_component:
            return {
                "status": "insufficient_data",
                "required_input": "component_costs_ms and target_component",
            }
        if target_component not in component_costs_ms:
            return {
                "status": "invalid_input",
                "error": f"{target_component!r} not present in component_costs_ms",
                "available": sorted(component_costs_ms),
            }
        reduction = max(0.0, min(float(reduction), 1.0))
        cost = float(component_costs_ms[target_component])
        saved = cost * reduction
        after = max(0.0, float(current_latency_ms) - saved)
        return {
            "status": "measured",
            "current_latency_ms": current_latency_ms,
            "component": target_component,
            "component_cost_ms": cost,
            "reduction": reduction,
            "saved_ms": round(saved, 4),
            "resulting_latency_ms": round(after, 4),
            "improvement_percent": round(saved / float(current_latency_ms) * 100.0, 2)
            if current_latency_ms
            else None,
        }

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
latency_reducer = Subagent18()
