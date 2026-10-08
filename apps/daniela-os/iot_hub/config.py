"""Configuracion IoT leida del entorno (.env via shared.env_loader).

Los valores se leen en cada acceso (atributos de modulo), de modo que los
tests pueden hacer ``monkeypatch.setattr(config, "HA_URL", ...)``.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Estado local (device_map.json SIEMPRE trackeado; el resto es runtime)
IOT_STATE_DIR = Path(os.getenv("IOT_STATE_DIR", str(REPO_ROOT / "data" / "iot")))
DEVICE_MAP_FILE = IOT_STATE_DIR / "device_map.json"
INVENTORY_FILE = IOT_STATE_DIR / "inventory.json"
MQTT_CACHE_FILE = IOT_STATE_DIR / "mqtt_cache.json"

# Home Assistant (externo, configurado en .env — nunca compuesto en repo)
HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")
HA_TIMEOUT = float(os.getenv("HA_TIMEOUT", "5"))

# MQTT (broker Mosquitto propio o externo)
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

# ESPHome (dashboard de dispositivos ESP)
ESPHOME_URL = os.getenv("ESPHOME_URL", "http://localhost:6053")

# Descubrimiento de intranet
IOT_SCAN_SUBNET = os.getenv("IOT_SCAN_SUBNET", "192.168.1.0/24")
IOT_SCAN_TIMEOUT = float(os.getenv("IOT_SCAN_TIMEOUT", "1"))
IOT_MQTT_TOPICS = [
    t.strip()
    for t in os.getenv("IOT_MQTT_TOPICS", "zigbee2mqtt/#,home/#,tele/#").split(",")
    if t.strip()
]
