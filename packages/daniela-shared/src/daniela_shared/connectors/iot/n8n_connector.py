"""Conector para n8n - Automatización de flujos."""

import os
from typing import Any

import requests


class N8NConnector:
    """Conector para la API de n8n."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url or os.getenv("N8N_URL", "http://localhost:5678")
        self.api_key = api_key or os.getenv("N8N_API_KEY", "")
        self.headers = {"X-N8N-API-KEY": self.api_key} if self.api_key else {}

    def health_check(self) -> bool:
        """Verifica que n8n está activo."""
        try:
            resp = requests.get(f"{self.base_url}/healthz", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def trigger_webhook(self, webhook_id: str, data: dict[str, Any]) -> bool:
        """Ejecuta un webhook de n8n."""
        try:
            resp = requests.post(
                f"{self.base_url}/webhook/{webhook_id}",
                json=data,
                headers=self.headers,
                timeout=30,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def get_workflows(self) -> list:
        """Obtiene la lista de workflows."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/v1/workflows",
                headers=self.headers,
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json().get("data", [])
        except Exception:
            pass
        return []
