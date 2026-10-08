"""Subagentes para Caller."""

from typing import Any

from ..base import Agent


class DialerSubagent(Agent):
    """Subagente de marcación."""

    def __init__(self, config: dict | None = None):
        super().__init__("caller_dialer", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "task": "dial"}


class MessageSubagent(Agent):
    """Subagente de mensajes."""

    def __init__(self, config: dict | None = None):
        super().__init__("caller_message", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "task": "message"}
