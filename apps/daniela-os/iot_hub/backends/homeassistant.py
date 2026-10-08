"""API segura para Home Assistant — implementacion canonica (ADR-001).

Promovida desde ``api/homeassistant_api.py`` (que queda como shim); tests
existentes parchean ``api.homeassistant_api.requests.*`` y siguen operando
porque el modulo shim reimporta ``requests`` como atributo.
"""

from __future__ import annotations

import os
from typing import Any

import requests


class HomeAssistantAPI:
    """API segura para Home Assistant."""

    def __init__(self, base_url: str | None = None, token: str | None = None):
        self.base_url = base_url or os.getenv("HA_URL", "http://localhost:8123")
        self.token = token or os.getenv("HA_TOKEN", "")
        self.headers = (
            {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            if self.token
            else {}
        )

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
        """Verifica que Home Assistant está activo."""
        try:
            resp = requests.get(f"{self.base_url}/api/", headers=self.headers, timeout=5)
            return {"status": "ok" if resp.status_code == 200 else "error"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_states(self) -> dict[str, Any]:
        """Obtiene el estado de todas las entidades."""
        return self._request("GET", "/api/states")

    def get_state(self, entity_id: str) -> dict[str, Any]:
        """Obtiene el estado de una entidad."""
        return self._request("GET", f"/api/states/{entity_id}")

    def set_state(
        self, entity_id: str, state: str, attributes: dict | None = None
    ) -> dict[str, Any]:
        """Establece el estado de una entidad."""
        payload = {"state": state, "attributes": attributes or {}}
        return self._request("POST", f"/api/states/{entity_id}", json=payload)

    def call_service(self, domain: str, service: str, data: dict | None = None) -> dict[str, Any]:
        """Ejecuta un servicio."""
        return self._request("POST", f"/api/services/{domain}/{service}", json=data or {})

    def get_services(self) -> dict[str, Any]:
        """Obtiene todos los servicios disponibles."""
        return self._request("GET", "/api/services")

    def get_config(self) -> dict[str, Any]:
        """Obtiene la configuración."""
        return self._request("GET", "/api/config")

    def fire_event(self, event_type: str, event_data: dict | None = None) -> dict[str, Any]:
        """Dispara un evento."""
        return self._request("POST", f"/api/events/{event_type}", json=event_data or {})

    def get_history(self, entity_id: str | None = None, days: int = 1) -> dict[str, Any]:
        """Obtiene el historial de estados."""
        params = {"filter_entity_id": entity_id} if entity_id else {}
        return self._request("GET", f"/api/history/period/{days}d", params=params)
