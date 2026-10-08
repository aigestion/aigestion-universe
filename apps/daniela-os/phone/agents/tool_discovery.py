"""Auto-discovery de Tools.

Los agentes descubren nuevos tools automáticamente.
"""

import importlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ToolDiscovery:
    """Descubre tools automáticamente."""

    def __init__(self, tools_dir: str | None = None):
        self.tools_dir = Path(tools_dir or Path(__file__).parent.parent.parent / "tools")
        self.discovered_file = Path(__file__).parent / "discovered_tools.json"
        self.discovered = self._load_discovered()

    def _load_discovered(self) -> dict:
        if self.discovered_file.exists():
            return json.loads(self.discovered_file.read_text())
        return {"tools": [], "last_discovery": None}

    def _save_discovered(self):
        self.discovered_file.write_text(json.dumps(self.discovered, indent=2))

    def discover_tools(self) -> list[dict[str, Any]]:
        """Descubre todos los tools disponibles."""
        tools = []
        for py_file in self.tools_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            tool_name = py_file.stem
            try:
                module = importlib.import_module(f"tools.{tool_name}")
                functions = [
                    name
                    for name in dir(module)
                    if not name.startswith("_") and callable(getattr(module, name))
                ]
                tools.append(
                    {
                        "name": tool_name,
                        "module": f"tools.{tool_name}",
                        "functions": functions,
                        "discovered": True,
                    }
                )
            except Exception as e:
                tools.append(
                    {
                        "name": tool_name,
                        "module": f"tools.{tool_name}",
                        "functions": [],
                        "error": str(e),
                    }
                )

        self.discovered["tools"] = tools
        self.discovered["last_discovery"] = datetime.now().isoformat()
        self._save_discovered()
        return tools

    def get_tool(self, name: str) -> dict[str, Any] | None:
        """Obtiene un tool por nombre."""
        for tool in self.discovered.get("tools", []):
            if tool["name"] == name:
                return tool
        return None

    def call_tool(self, name: str, function: str, **kwargs) -> Any:
        """Llama a una función de un tool."""
        try:
            module = importlib.import_module(f"tools.{name}")
            func = getattr(module, function)
            return func(**kwargs)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    discovery = ToolDiscovery()
    tools = discovery.discover_tools()
    print(f"Tools descubiertos: {len(tools)}")
    for tool in tools:
        print(f"  - {tool['name']}: {len(tool.get('functions', []))} funciones")
