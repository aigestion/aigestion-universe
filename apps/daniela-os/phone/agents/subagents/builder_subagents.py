"""Subagentes para Builder."""

from typing import Any

from ..base import Agent


class ScriptSubagent(Agent):
    """Subagente de scripts."""

    def __init__(self, config: dict | None = None):
        super().__init__("builder_script", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "task": "script"}


class CronSubagent(Agent):
    """Subagente de cron jobs."""

    def __init__(self, config: dict | None = None):
        super().__init__("builder_cron", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "task": "cron"}
