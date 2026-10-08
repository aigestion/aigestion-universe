"""Subagentes para Guardian."""

from typing import Any

from ..base import Agent


class BackupSubagent(Agent):
    """Subagente de backups."""

    def __init__(self, config: dict | None = None):
        super().__init__("guardian_backup", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "task": "backup"}


class SecuritySubagent(Agent):
    """Subagente de seguridad."""

    def __init__(self, config: dict | None = None):
        super().__init__("guardian_security", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "task": "security"}
