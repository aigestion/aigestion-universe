"""Tools para análisis y mejora de código."""

import json
import os
import subprocess
from pathlib import Path
from typing import Any


def run_lint(path: str = ".") -> dict[str, Any]:
    """Ejecuta ruff check."""
    try:
        result = subprocess.run(
            ["ruff", "check", path, "--output-format=json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "returncode": result.returncode,
            "issues": json.loads(result.stdout) if result.stdout else [],
        }
    except Exception as e:
        return {"error": str(e)}


def run_type_check(path: str = ".") -> dict[str, Any]:
    """Ejecuta mypy."""
    try:
        result = subprocess.run(
            ["mypy", path, "--no-error-summary"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "returncode": result.returncode,
            "output": result.stdout,
        }
    except Exception as e:
        return {"error": str(e)}


def get_file_stats(path: str = ".") -> dict[str, Any]:
    """Obtiene estadísticas de ficheros."""
    stats = {"total": 0, "by_extension": {}}
    for root, _, files in os.walk(path):
        if "node_modules" in root or ".git" in root:
            continue
        for f in files:
            stats["total"] += 1
            ext = Path(f).suffix
            stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1
    return stats


def find_todos(path: str = ".") -> list[dict[str, Any]]:
    """Busca TODOs y FIXMEs en el código."""
    todos = []
    for root, _, files in os.walk(path):
        if "node_modules" in root or ".git" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                file_path = Path(root) / f
                try:
                    content = file_path.read_text()
                    for i, line in enumerate(content.split("\n"), 1):
                        if "TODO" in line or "FIXME" in line:
                            todos.append({
                                "file": str(file_path),
                                "line": i,
                                "text": line.strip(),
                            })
                except Exception:
                    pass
    return todos
