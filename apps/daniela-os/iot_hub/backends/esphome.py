"""Backend ESPHome — envuelve connectors.esphome_connector."""

from __future__ import annotations

from typing import Any

from iot_hub import config


def _connector():
    from connectors.iot.esphome_connector import ESPHomeConnector

    return ESPHomeConnector(base_url=config.ESPHOME_URL)


def status() -> dict[str, Any]:
    """Estado del dashboard ESPHome."""
    return {
        "url": config.ESPHOME_URL,
        "available": _connector().health_check(),
    }


def control_switch(device: str, switch_id: str, state: bool) -> dict[str, Any]:
    """Conecta/desconecta un switch ESPHome."""
    ok = _connector().control_switch(device, switch_id, state)
    return {"ok": ok, "device": device, "switch": switch_id, "state": state}
