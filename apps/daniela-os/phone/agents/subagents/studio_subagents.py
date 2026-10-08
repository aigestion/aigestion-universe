"""Subagentes para Studio."""

from typing import Any

from ..base import Agent


class TranscriberSubagent(Agent):
    """Subagente de transcripción."""

    def __init__(self, config: dict | None = None):
        super().__init__("studio_transcriber", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "task": "transcribe"}


class VoiceSubagent(Agent):
    """Subagente de voz."""

    def __init__(self, config: dict | None = None):
        super().__init__("studio_voice", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "task": "voice"}


class VideoSubagent(Agent):
    """Subagente de video."""

    def __init__(self, config: dict | None = None):
        super().__init__("studio_video", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "task": "video"}
