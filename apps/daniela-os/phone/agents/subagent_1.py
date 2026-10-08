"""Subagent 1 - Gestor de Tareas."""


class Subagent1:
    """Subagente de gestión de tareas: creación, seguimiento y priorización."""

    def __init__(self, name: str = "Subagent_1"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def create_task(self, task_id: str, description: str) -> str:
        """Create a new task and return its ID."""
        task = {
            "task_id": task_id,
            "description": description,
            "priority": "medium",
            "status": "pending",
            "assignee": None,
        }
        self._tasks[task_id] = task
        return f"Task {task_id} created: {description}"

    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update the status of a task."""
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = status
            return True
        return False

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
task_manager = Subagent1()
