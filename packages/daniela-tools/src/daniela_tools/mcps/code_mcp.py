"""MCP para tools de código."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.code_tools import find_todos, get_file_stats, run_lint, run_type_check


class CodeMCP:
    """MCP para análisis y mejora de código."""

    def __init__(self):
        self.tools = {
            "lint": self.lint,
            "type_check": self.type_check,
            "file_stats": self.file_stats,
            "find_todos": self.find_todos,
        }

    def lint(self, path: str = ".") -> dict[str, Any]:
        """Ejecuta lint."""
        return run_lint(path)

    def type_check(self, path: str = ".") -> dict[str, Any]:
        """Ejecuta type check."""
        return run_type_check(path)

    def file_stats(self, path: str = ".") -> dict[str, Any]:
        """Obtiene estadísticas de ficheros."""
        return get_file_stats(path)

    def find_todos(self, path: str = ".") -> list[dict[str, Any]]:
        """Busca TODOs."""
        return find_todos(path)

    def call(self, tool: str, **kwargs) -> Any:
        """Llama a un tool."""
        if tool in self.tools:
            return self.tools[tool](**kwargs)
        return {"error": f"Tool '{tool}' no encontrado"}
