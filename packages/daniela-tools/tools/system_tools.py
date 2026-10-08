"""Tools para el sistema."""

import platform
import subprocess
from typing import Any


def get_system_info() -> dict[str, Any]:
    """Obtiene información del sistema."""
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor(),
        "hostname": platform.node(),
    }


def get_disk_usage() -> dict[str, Any]:
    """Obtiene uso de disco."""
    try:
        result = subprocess.run(
            ["df", "-h", "/"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {"output": result.stdout}
    except Exception as e:
        return {"error": str(e)}


def get_memory_usage() -> dict[str, Any]:
    """Obtiene uso de memoria."""
    try:
        result = subprocess.run(
            ["free", "-h"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {"output": result.stdout}
    except Exception as e:
        return {"error": str(e)}


def get_running_processes() -> list[dict[str, Any]]:
    """Obtiene procesos en ejecución."""
    try:
        result = subprocess.run(
            ["ps", "aux", "--sort=-%mem"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        lines = result.stdout.strip().split("\n")
        processes = []
        for line in lines[1:11]:  # Top 10
            parts = line.split()
            if len(parts) >= 11:
                processes.append({
                    "pid": parts[1],
                    "cpu": parts[2],
                    "mem": parts[3],
                    "command": " ".join(parts[10:]),
                })
        return processes
    except Exception as e:
        return [{"error": str(e)}]
