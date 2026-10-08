"""MCP para tools de Git."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.git_tools import create_branch, get_recent_commits, get_status


class GitMCP:
    """MCP para Git."""

    def __init__(self):
        self.tools = {
            "status": self.status,
            "recent_commits": self.recent_commits,
            "create_branch": self.create_branch,
        }

    def status(self) -> dict[str, Any]:
        """Obtiene estado del repo."""
        return get_status()

    def recent_commits(self, n: int = 10) -> list[dict[str, Any]]:
        """Obtiene commits recientes."""
        return get_recent_commits(n)

    def create_branch(self, name: str) -> dict[str, Any]:
        """Crea una rama."""
        return create_branch(name)

    def call(self, tool: str, **kwargs) -> Any:
        """Llama a un tool."""
        if tool in self.tools:
            return self.tools[tool](**kwargs)
        return {"error": f"Tool '{tool}' no encontrado"}
