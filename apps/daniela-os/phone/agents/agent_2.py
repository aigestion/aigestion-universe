"""Agent 2 - Procesamiento de Datos.

Agente de procesamiento responsable de transformar y validar los datos,
garantizando entradas de alta calidad para los procesos posteriores.
"""


class Agent2:
    """Data processing agent that handles transformation and validation."""

    def __init__(self, name: str = "Agent_2"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def process_data(self, data: list) -> list:
        """Process and transform incoming data."""
        # Example processing: convert to uppercase, filter empty
        return [item.upper() for item in data if item]

    def validate_input(self, data: list) -> bool:
        """Validate input data integrity."""
        return isinstance(data, list) and all(isinstance(item, str) for item in data)

    def enrich_data(self, data: list) -> list:
        """Enrich data with additional metadata."""
        return [f"enriched_{item}" for item in data]

    def get_task_status(self, task_id: str) -> dict | None:
        """Get the status of a specific task."""
        return self._tasks.get(task_id)


# Singleton instance
processor = Agent2()
