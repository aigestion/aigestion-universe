"""Subagent 6 - Enrutador de Mensajes."""


class Subagent6:
    """Subagente de enrutamiento de mensajes: enruta comunicaciones entre servicios."""

    def __init__(self, name: str = "Subagent_6"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def route_message(self, sender: str, recipient: str, content: str) -> str:
        """Route a message from sender to recipient."""
        message = f"FROM: {sender} -> TO: {recipient}: {content}"
        print(message)
        return message

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
message_router = Subagent6()
