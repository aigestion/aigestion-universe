"""Subagentes para Scout."""

from typing import Any

from ..base import Agent


class YouTubeSubagent(Agent):
    """Subagente especializado en YouTube."""

    def __init__(self, config: dict | None = None):
        super().__init__("scout_youtube", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "source": "youtube"}


class RSSSubagent(Agent):
    """Subagente especializado en RSS."""

    def __init__(self, config: dict | None = None):
        super().__init__("scout_rss", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "source": "rss"}


class RedditSubagent(Agent):
    """Subagente especializado en Reddit."""

    def __init__(self, config: dict | None = None):
        super().__init__("scout_reddit", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "source": "reddit"}
