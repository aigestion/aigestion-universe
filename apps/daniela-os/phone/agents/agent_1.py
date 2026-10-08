"""Agent 1 - Coordinador Central.

Agente coordinador responsable de orquestar todos los subsistemas,
gestionar la sincronización entre agentes, garantizar la consistencia de
los datos y coordinar los flujos de trabajo distribuidos.
"""

from datetime import UTC, datetime


class Agent1:
    """Core coordination agent that manages the entire system."""

    def __init__(self, name: str = "Agent_1"):
        self.name = name
        self.status = "active"
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, list[str]] = {}
        self._agents: list[str] = []

    def coordinate(self) -> str:
        """Orchestrate distributed tasks across all subsystems."""
        # Coordinate task distribution
        task = {
            "task_id": f"task_{len(self._tasks)}",
            "assigned_to": self.name,
            "dependencies": [],
            "status": "pending",
        }
        self._tasks[task["task_id"]] = task
        return f"Coordinated task {task['task_id']} assigned to {self.name}"

    def resolve_conflicts(self) -> list[str]:
        """Resolve conflicts between competing agents."""
        conflicts = []
        # Simple conflict detection based on overlapping dependencies
        for task_id, _task in self._tasks.items():
            # Check for dependency cycles
            if self._has_cycle(task_id):
                conflicts.append(f"Task {task_id} has cycle")
        return conflicts

    def register_agent(self, agent_name: str) -> str:
        """Register a peer agent under this coordinator."""
        if agent_name not in self._agents:
            self._agents.append(agent_name)
        return agent_name

    def sync_state(self) -> dict:
        """Synchronize global state across all agents."""
        return {
            "coordinator": self.name,
            "agents": list(self._agents),
            "total_agents": len(self._agents),
            "total_tasks": len(self._tasks),
            "last_sync": datetime.now(UTC).isoformat(),
        }

    def _has_cycle(self, task_id: str) -> bool:
        """Detect if a task creates a dependency cycle."""
        visited = set()
        recursion_stack = set()

        def dfs(current):
            visited.add(current)
            recursion_stack.add(current)

            # Find dependent tasks
            for dep in self._dependencies.get(current, []):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in recursion_stack:
                    return True

            recursion_stack.remove(current)
            return False

        return dfs(task_id)

    def add_dependency(self, task_id: str, depends_on: str) -> bool:
        """Add a dependency relationship between tasks."""
        if task_id in self._dependencies and depends_on in self._dependencies[task_id]:
            return True
        self._dependencies.setdefault(task_id, []).append(depends_on)
        return True

    def remove_dependency(self, task_id: str, depends_on: str) -> bool:
        """Remove a dependency relationship."""
        if task_id in self._dependencies and depends_on in self._dependencies[task_id]:
            self._dependencies[task_id].remove(depends_on)
            return True
        return False

    def get_task_status(self, task_id: str) -> dict | None:
        """Get the status of a specific task."""
        return self._tasks.get(task_id)


# Singleton instance
coordinator = Agent1()
