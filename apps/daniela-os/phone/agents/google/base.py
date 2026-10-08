"""Base para agentes de Google."""

import os
from typing import Any

import requests

from ..base import Agent


class GoogleAgent(Agent):
    """Base para agentes de Google Workspace."""

    def __init__(self, name: str, config: dict | None = None):
        super().__init__(name, config)
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        self.access_token = os.getenv("GOOGLE_ACCESS_TOKEN", "")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.headers = (
            {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            if self.access_token
            else {}
        )

    def _request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        """Ejecuta request HTTP."""
        try:
            resp = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except Exception as e:
            return {"error": str(e)}
