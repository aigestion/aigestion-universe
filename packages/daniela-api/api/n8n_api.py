"""API segura para n8n."""

import os
from typing import Any

import requests

from .auth import APIKeyAuth


class N8NAPI:
    """API segura para n8n."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url or os.getenv("N8N_URL", "http://localhost:5678")
        self.api_key = api_key or os.getenv("N8N_API_KEY", "")
        self.auth = APIKeyAuth(self.api_key)
        self.headers = {"X-N8N-API-KEY": self.api_key} if self.api_key else {}

    def _request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Ejecuta una request HTTP con manejo de errores."""
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "error"}

    def health_check(self) -> dict[str, Any]:
        """Verifica que n8n está activo."""
        try:
            resp = requests.get(f"{self.base_url}/healthz", timeout=5)
            return {"status": "ok" if resp.status_code == 200 else "error"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_workflows(self) -> dict[str, Any]:
        """Obtiene todos los workflows."""
        return self._request("GET", "/api/v1/workflows")

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Obtiene un workflow por ID."""
        return self._request("GET", f"/api/v1/workflows/{workflow_id}")

    def execute_workflow(self, workflow_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta un workflow."""
        return self._request("POST", f"/api/v1/workflows/{workflow_id}/run", json=data)

    def trigger_webhook(self, webhook_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta un webhook."""
        return self._request("POST", f"/webhook/{webhook_id}", json=data)

    def create_workflow(self, name: str, nodes: list, connections: dict) -> dict[str, Any]:
        """Crea un workflow."""
        payload = {"name": name, "nodes": nodes, "connections": connections}
        return self._request("POST", "/api/v1/workflows", json=payload)

    def delete_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Elimina un workflow."""
        return self._request("DELETE", f"/api/v1/workflows/{workflow_id}")
