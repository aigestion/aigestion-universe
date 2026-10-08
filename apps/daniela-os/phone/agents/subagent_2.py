"""Subagent 2 - Organizador de Datos."""


class Subagent2:
    """Subagente de organización de datos: estructura, ordena e indexa la información."""

    def __init__(self, name: str = "Subagent_2"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def organize_data(self, data: list) -> dict:
        """Organize raw data into categories."""
        categorized = {}
        for item in data:
            category = self._categorize(item)
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(item)
        return categorized

    def _categorize(self, item: str) -> str:
        """Categorize an item based on its content."""
        # Simple categorization logic
        if "email" in item.lower():
            return "communications"
        elif "file" in item.lower():
            return "files"
        elif "report" in item.lower():
            return "reports"
        else:
            return "general"

    def get_organized_data(self, data: list) -> dict:
        """Get data organized by category."""
        return self.organize_data(data)

    def get_task(self, task_id: str) -> dict | None:
        """Get a task by its ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[dict]:
        """Get all tasks."""
        return list(self._tasks.values())


# Singleton instance
data_organizer = Subagent2()
