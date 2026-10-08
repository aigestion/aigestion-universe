"""Subagentes para Social."""

from typing import Any

from ..base import Agent


class TikTokSubagent(Agent):
    """Subagente de TikTok."""

    def __init__(self, config: dict | None = None):
        super().__init__("social_tiktok", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "platform": "tiktok"}


class TwitterSubagent(Agent):
    """Subagente de Twitter."""

    def __init__(self, config: dict | None = None):
        super().__init__("social_twitter", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "platform": "twitter"}


class InstagramSubagent(Agent):
    """Subagente de Instagram."""

    def __init__(self, config: dict | None = None):
        super().__init__("social_instagram", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "platform": "instagram"}
