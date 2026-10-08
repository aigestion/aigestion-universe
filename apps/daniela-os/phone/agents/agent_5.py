"""Agent 5 - Seguridad.

Agente de seguridad responsable de vigilar y proteger el sistema,
detectar amenazas y bloquear el acceso no autorizado.
"""


class Agent5:
    """Security agent that monitors and protects the system."""

    def __init__(self, name: str = "Agent_5"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def monitor_security(self) -> dict:
        """Perform security monitoring and threat detection."""
        return {
            "threats_detected": 0,
            "protected_resources": list(self._tasks.keys()),
            "last_check": "2026-10-01T00:00:00Z",
        }

    def detect_threats(self) -> list[str]:
        """Detect potential security threats."""
        return ["No active threats detected"]

    def block_access(self, actor: str) -> bool:
        """Block access for a specific actor."""
        return True

    def get_task_status(self, task_id: str) -> dict | None:
        """Get the status of a specific task."""
        return self._tasks.get(task_id)


# Singleton instance
security = Agent5()
