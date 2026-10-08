"""MCP para tools del sistema."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.system_tools import (
    get_disk_usage,
    get_memory_usage,
    get_running_processes,
    get_system_info,
)


class SystemMCP:
    """MCP para el sistema."""

    def __init__(self):
        self.tools = {
            "system_info": self.system_info,
            "disk_usage": self.disk_usage,
            "memory_usage": self.memory_usage,
            "processes": self.processes,
        }

    def system_info(self) -> dict[str, Any]:
        """Obtiene info del sistema."""
        return get_system_info()

    def disk_usage(self) -> dict[str, Any]:
        """Obtiene uso de disco."""
        return get_disk_usage()

    def memory_usage(self) -> dict[str, Any]:
        """Obtiene uso de memoria."""
        return get_memory_usage()

    def processes(self) -> list[dict[str, Any]]:
        """Obtiene procesos."""
        return get_running_processes()

    def call(self, tool: str, **kwargs) -> Any:
        """Llama a un tool."""
        if tool in self.tools:
            return self.tools[tool](**kwargs)
        return {"error": f"Tool '{tool}' no encontrado"}
