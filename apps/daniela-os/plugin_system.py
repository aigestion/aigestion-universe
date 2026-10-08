#!/usr/bin/env python3
"""
AIGestion Plugin System v1.0
=============================
Sistema de extensiones para AIGestion.

- Plugins cargados dinamicamente desde directorio plugins/
- Cada plugin expone: nombre, version, hooks, handlers
- Hooks: pre_ask, post_ask, pre_pipeline, post_pipeline
- Sandboxing basico (solo acceso a API del core)

Autor: AIGestion Team
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PluginInfo:
    """Metadatos de un plugin."""

    name: str
    version: str
    description: str
    author: str
    hooks: dict[str, Callable[..., Any]] = field(default_factory=dict)
    enabled: bool = True


class PluginManager:
    """Gestiona carga, ejecucion y sandboxing de plugins."""

    PLUGIN_DIR = Path(__file__).parent / "plugins"

    def __init__(self):
        self.plugins: dict[str, PluginInfo] = {}
        self._ensure_plugin_dir()

    def _ensure_plugin_dir(self) -> None:
        self.PLUGIN_DIR.mkdir(exist_ok=True)
        # Crear plugin de ejemplo si no existe
        example = self.PLUGIN_DIR / "example_plugin.py"
        if not example.exists():
            example.write_text('''"""Plugin de ejemplo para AIGestion."""

NAME = "example"
VERSION = "1.0.0"
DESCRIPTION = "Plugin de demostracion"
AUTHOR = "AIGestion"


def pre_ask(query: str, context: dict) -> tuple[str, dict]:
    """Se ejecuta antes de procesar una consulta."""
    print(f"[Plugin Example] Interceptando: {query[:30]}...")
    return query, context


def post_ask(result: dict) -> dict:
    """Se ejecuta despues de procesar una consulta."""
    result["_plugin_processed"] = True
    return result
''')

    def load_all(self) -> list[PluginInfo]:
        """Carga todos los plugins del directorio."""
        if not self.PLUGIN_DIR.exists():
            return []

        for file_path in self.PLUGIN_DIR.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            try:
                self._load_plugin(file_path)
            except Exception as e:
                print(f"[PLUGIN] Error cargando {file_path.name}: {e}")

        return list(self.plugins.values())

    def _load_plugin(self, file_path: Path) -> PluginInfo | None:
        """Carga un plugin individual."""
        name = file_path.stem
        spec = importlib.util.spec_from_file_location(name, file_path)
        if not spec or not spec.loader:
            return None

        mod = importlib.util.module_from_spec(spec)
        # Sandbox: limitar builtins
        mod.__dict__["__builtins__"] = {
            "print": print,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,
            "setattr": setattr,
            "type": type,
            "Exception": Exception,
            "ValueError": ValueError,
            "KeyError": KeyError,
            "True": True,
            "False": False,
            "None": None,
        }

        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            print(f"[PLUGIN] Error ejecutando {name}: {e}")
            return None

        # Extraer metadatos
        info = PluginInfo(
            name=getattr(mod, "NAME", name),
            version=getattr(mod, "VERSION", "0.0.1"),
            description=getattr(mod, "DESCRIPTION", ""),
            author=getattr(mod, "AUTHOR", "unknown"),
        )

        # Extraer hooks
        for hook_name in ["pre_ask", "post_ask", "pre_pipeline", "post_pipeline"]:
            if hasattr(mod, hook_name):
                info.hooks[hook_name] = getattr(mod, hook_name)

        self.plugins[info.name] = info
        print(f"[PLUGIN] Cargado: {info.name} v{info.version}")
        return info

    def run_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> Any:
        """Ejecuta un hook en todos los plugins habilitados."""
        result = args[0] if args else kwargs
        for plugin in self.plugins.values():
            if not plugin.enabled or hook_name not in plugin.hooks:
                continue
            try:
                hook = plugin.hooks[hook_name]
                if hook_name.startswith("pre_"):
                    result = hook(*args, **kwargs)
                else:
                    result = hook(result)
            except Exception as e:
                print(f"[PLUGIN] Error en {plugin.name}.{hook_name}: {e}")
        return result

    def list_plugins(self) -> list[dict[str, Any]]:
        """Lista plugins cargados."""
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "author": p.author,
                "enabled": p.enabled,
                "hooks": list(p.hooks.keys()),
            }
            for p in self.plugins.values()
        ]

    def enable(self, name: str) -> bool:

        if name in self.plugins:
            self.plugins[name].enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """Desactiva un plugin por nombre."""

        if name in self.plugins:
            self.plugins[name].enabled = False
            return True
        return False


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="AIGestion Plugin System")
    parser.add_argument("--list", action="store_true", help="Listar plugins")
    parser.add_argument("--enable", help="Habilitar plugin")
    parser.add_argument("--disable", help="Deshabilitar plugin")
    parser.add_argument("--test-hooks", action="store_true", help="Testear hooks")

    args = parser.parse_args()

    manager = PluginManager()
    manager.load_all()

    if args.list:
        plugins = manager.list_plugins()
        print(json.dumps(plugins, indent=2, ensure_ascii=False))

    if args.enable:
        if manager.enable(args.enable):
            print(f"[OK] Plugin '{args.enable}' habilitado")
        else:
            print(f"[ERROR] Plugin '{args.enable}' no encontrado")

    if args.disable:
        if manager.disable(args.disable):
            print(f"[OK] Plugin '{args.disable}' deshabilitado")
        else:
            print(f"[ERROR] Plugin '{args.disable}' no encontrado")

    if args.test_hooks:
        print("[TEST] Ejecutando hook pre_ask...")
        result = manager.run_hook("pre_ask", "hola mundo", {})
        print(f"  Resultado: {result}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
