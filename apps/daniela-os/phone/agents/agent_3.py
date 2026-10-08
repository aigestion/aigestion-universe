"""Agent 3 - Interacción con Usuario.

Agente de interacción que gestiona las comunicaciones directas con el
usuario, captura las entradas y genera las respuestas.
"""


class Agent3:
    """User interaction agent that manages user-facing operations."""

    def __init__(self, name: str = "Agent_3"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}

    def handle_user_input(self, input_text: str) -> str:
        """Handle and respond to user input."""
        # Generate a sample response based on input
        return f"Processed: {input_text}"

    def generate_response(self, prompt: str) -> str:
        """Generate a structured response."""
        return f"Response to: {prompt}"

    def get_task_status(self, task_id: str) -> dict | None:
        """Get the status of a specific task."""
        return self._tasks.get(task_id)


# Singleton instance
interactor = Agent3()
