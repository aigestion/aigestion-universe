"""Subagent 21 - Optimizador de Colas.

Calcula el tamano de cola segun latencia y throughput medidos.
"""

from typing import Any


class Subagent21:
    """Calcula el tamano de cola segun latencia y throughput medidos."""

    def __init__(self, name: str = "Subagent_21"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def optimize_queue(
        self,
        arrival_rate: float | None = None,
        service_rate: float | None = None,
        max_wait_ms: float | None = None,
    ) -> dict:
        """Apply queueing analysis to measured rates.

        Args:
            arrival_rate: arrivals per second.
            service_rate: completions per second.
            max_wait_ms: tolerated wait, used to size the buffer.

        Returns:
            Utilisation and, when a wait budget is given, the queue depth that
            stays inside it. Utilisation at or above 1.0 is reported as
            unstable because the queue then grows without bound.
        """
        if arrival_rate is None or service_rate is None:
            return {
                "status": "insufficient_data",
                "required_input": "arrival_rate and service_rate",
            }
        if service_rate <= 0:
            return {"status": "invalid_input", "error": "service_rate must be positive"}
        rho = float(arrival_rate) / float(service_rate)
        result: dict[str, Any] = {
            "status": "measured",
            "arrival_rate": arrival_rate,
            "service_rate": service_rate,
            "utilisation": round(rho, 4),
            "stable": rho < 1.0,
            "verdict": "saturated" if rho >= 1.0 else ("tight" if rho >= 0.85 else "ok"),
        }
        if max_wait_ms:
            wait_s = float(max_wait_ms) / 1000.0
            result["max_wait_ms"] = max_wait_ms
            # Little's Law on the queue itself.
            result["recommended_depth"] = (
                round(max(0.0, (rho / (1 - rho))) * arrival_rate * wait_s, 2) if rho < 1 else None
            )
        return result

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
queue_optimizer = Subagent21()
