"""Read-only Docker Compose status inspection."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def compose_stack_status(compose_dir: str | Path) -> dict[str, Any]:
    """Return service state from Compose without changing the running stack."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            cwd=compose_dir,
            capture_output=True,
            check=True,
            text=True,
            timeout=5,
        )
        services = [
            {
                "name": service.get("Service"),
                "state": service.get("State"),
                "health": service.get("Health"),
            }
            for line in result.stdout.splitlines()
            if line.strip()
            for service in [json.loads(line)]
        ]
        return {
            "ok": bool(services)
            and all(service["state"] == "running" for service in services),
            "available": True,
            "services": services,
        }
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "available": False,
            "services": [],
            "error": str(exc)[:200],
        }
