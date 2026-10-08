"""MCP para tools de redes sociales."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.social_tools import (
    get_twitter_trends,
    post_to_instagram,
    post_to_tiktok,
    post_to_twitter,
)


class SocialMCP:
    """MCP para redes sociales."""

    def __init__(self):
        self.tools = {
            "post_tiktok": self.post_tiktok,
            "post_twitter": self.post_twitter,
            "post_instagram": self.post_instagram,
            "get_trends": self.get_trends,
        }

    def post_tiktok(self, video_path: str, description: str) -> dict[str, Any]:
        """Publica en TikTok."""
        return post_to_tiktok(video_path, description)

    def post_twitter(self, text: str, media: str | None = None) -> dict[str, Any]:
        """Publica en Twitter."""
        return post_to_twitter(text, media)

    def post_instagram(self, media_path: str, caption: str) -> dict[str, Any]:
        """Publica en Instagram."""
        return post_to_instagram(media_path, caption)

    def get_trends(self, woeid: int = 1) -> list[dict[str, Any]]:
        """Obtiene tendencias."""
        return get_twitter_trends(woeid)

    def call(self, tool: str, **kwargs) -> Any:
        """Llama a un tool."""
        if tool in self.tools:
            return self.tools[tool](**kwargs)
        return {"error": f"Tool '{tool}' no encontrado"}
