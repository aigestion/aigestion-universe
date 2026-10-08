"""Tools para Git."""

import subprocess
from typing import Any


def get_status() -> dict[str, Any]:
    """Obtiene el estado del repo."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "clean": result.returncode == 0 and not result.stdout,
            "files": result.stdout.strip().split("\n") if result.stdout else [],
        }
    except Exception as e:
        return {"error": str(e)}


def get_recent_commits(n: int = 10) -> list[dict[str, Any]]:
    """Obtiene los últimos commits."""
    try:
        result = subprocess.run(
            ["git", "log", f"-{n}", "--oneline", "--format=%H|%s|%an|%ad"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|", 3)
                commits.append({
                    "hash": parts[0],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                })
        return commits
    except Exception as e:
        return [{"error": str(e)}]


def create_branch(name: str) -> dict[str, Any]:
    """Crea una rama."""
    try:
        result = subprocess.run(
            ["git", "checkout", "-b", name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {"success": result.returncode == 0, "output": result.stdout}
    except Exception as e:
        return {"error": str(e)}
