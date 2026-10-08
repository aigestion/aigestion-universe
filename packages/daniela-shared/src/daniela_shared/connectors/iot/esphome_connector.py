"""Conector para ESPHome - Firmware ESP32/ESP8266."""

import os
from typing import Any

import requests


class ESPHomeConnector:
    """Conector para la API de ESPHome."""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("ESPHOME_URL", "http://localhost:6053")

    def health_check(self) -> bool:
        """Verifica que ESPHome está activo."""
        try:
            resp = requests.get(f"{self.base_url}/", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def get_devices(self) -> list:
        """Obtiene la lista de dispositivos."""
        try:
            resp = requests.get(f"{self.base_url}/devices", timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    def get_sensors(self, device: str) -> dict[str, Any]:
        """Obtiene los sensores de un dispositivo."""
        try:
            resp = requests.get(f"{self.base_url}/{device}/sensors", timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {}

    def control_switch(self, device: str, switch_id: str, state: bool) -> bool:
        """Controla un switch."""
        try:
            resp = requests.post(
                f"{self.base_url}/{device}/{switch_id}/turn_{'on' if state else 'off'}",
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False
