"""Subagentes para Web."""

from typing import Any

from ..base import Agent


class MonitorSubagent(Agent):
    """Subagente de monitoreo."""

    def __init__(self, config: dict | None = None):
        super().__init__("web_monitor", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "task": "monitor"}


class ScraperSubagent(Agent):
    """Subagente de scraping."""

    def __init__(self, config: dict | None = None):
        super().__init__("web_scraper", config)

    def run(self) -> dict[str, Any]:
        self.start()
        self.metrics["runs"] += 1
        self.metrics["success"] += 1
        self.save_metrics()
        self.stop()
        return {"status": "ok", "task": "scrape"}
