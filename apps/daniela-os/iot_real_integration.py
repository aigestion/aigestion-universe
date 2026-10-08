#!/usr/bin/env python3
"""
PA-05: IoT Real Integration - Home Assistant local
=====================================================
Reemplaza el stub de iot_controller.py con integracion real a Home Assistant.

Home Assistant (gratis, open source, corre en Raspberry Pi o PC):
  - REST API: http://homeassistant.local:8123/api/
  - Long-lived access token (gratis, se genera en HA Settings)
  - Control: luces, switches, clima, media players, escenas

Comandos de Daniela -> IoT:
  - "enciende la luz del salon" -> light.living_room turn_on
  - "apaga todas las luces" -> light.turn_off all
  - "pon el termostato a 22" -> climate.set_temperature
  - "activa escena noche" -> scene.activate scene.night

Rutas en daniela_os.py:
  - GET  /api/iot/status           (estado HA + devices)
  - GET  /api/iot/devices           (lista de dispositivos)
  - POST /api/iot/control           (controlar dispositivo)
  - POST /api/iot/scene             (activar escena)
  - POST /api/iot/voice             (comando de voz -> accion IoT)

Coste: $0/mes (Home Assistant es gratis y local)
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any

import requests

# ── Config ───────────────────────────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(PROJECT_ROOT, "data", "iot")
STATE_FILE = os.path.join(STATE_DIR, "iot_state.json")
DEVICE_MAP_FILE = os.path.join(STATE_DIR, "device_map.json")

# Home Assistant config (from .env or defaults)
HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")
HA_TIMEOUT = 5

# ── Data classes ─────────────────────────────────────────────


@dataclass
class IoTDevice:
    entity_id: str
    name: str
    domain: str  # light, switch, climate, media_player, scene
    state: str = "unknown"
    friendly_name: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class IoTState:
    ha_available: bool = False
    ha_url: str = ""
    device_count: int = 0
    last_sync: float = 0.0
    command_count: int = 0
    error_count: int = 0
    last_command: str = ""
    last_error: str = ""


# ── IoT Real Integration ─────────────────────────────────────


class IoTRealIntegration:
    """Real IoT control via Home Assistant REST API."""

    def __init__(self):
        self._state = IoTState(ha_url=HA_URL)
        self._lock = threading.Lock()
        self._devices: dict[str, IoTDevice] = {}
        self._device_map: dict[str, str] = {}  # alias -> entity_id
        self._load_device_map()
        self._init_default_map()

    def _load_device_map(self):
        if os.path.exists(DEVICE_MAP_FILE):
            try:
                with open(DEVICE_MAP_FILE, encoding="utf-8") as f:
                    self._device_map = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

    def _save_device_map(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(DEVICE_MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(self._device_map, f, indent=2, ensure_ascii=False)

    def _init_default_map(self):
        """Default voice-command aliases -> HA entity IDs."""
        defaults = {
            "luz salon": "light.living_room",
            "luz cocina": "light.kitchen",
            "luz dormitorio": "light.bedroom",
            "luz baño": "light.bathroom",
            "luz entrada": "light.entrance",
            "todas las luces": "light.all",
            "termostato": "climate.thermostat",
            "tv": "media_player.tv",
            "musica": "media_player.spotify",
            "enchufe": "switch.smart_plug",
        }
        for alias, entity in defaults.items():
            if alias not in self._device_map:
                self._device_map[alias] = entity
        self._save_device_map()

    # ── HA API ────────────────────────────────────────────────

    def _ha_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json",
        }

    def _ha_get(self, path: str) -> dict | None:
        if not HA_TOKEN:
            return None
        url = f"{HA_URL}{path}"
        try:
            r = requests.get(url, headers=self._ha_headers(), timeout=HA_TIMEOUT)
            if r.status_code == 200:
                self._state.ha_available = True
                return r.json()
            self._state.ha_available = False
        except requests.RequestException:
            self._state.ha_available = False
        return None

    def _ha_post(self, path: str, data: dict) -> dict:
        if not HA_TOKEN:
            return {"ok": False, "error": "HA_TOKEN not set. Configure in .env"}
        url = f"{HA_URL}{path}"
        try:
            r = requests.post(url, headers=self._ha_headers(), json=data, timeout=HA_TIMEOUT)
            if r.status_code in (200, 201):
                self._state.ha_available = True
                return {"ok": True}
            return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
        except requests.RequestException as e:
            self._state.ha_available = False
            return {"ok": False, "error": str(e)}

    # ── Device discovery ─────────────────────────────────────

    def sync_devices(self) -> dict:
        """Fetch all devices from Home Assistant."""
        data = self._ha_get("/api/states")
        if not data:
            return {"ok": False, "error": "Home Assistant not available or not configured"}

        devices = {}
        for entity in data:
            entity_id = entity.get("entity_id", "")
            domain = entity_id.split(".")[0] if "." in entity_id else "unknown"

            # Only keep controllable domains
            if domain in ("light", "switch", "climate", "media_player", "scene", "cover", "fan"):
                dev = IoTDevice(
                    entity_id=entity_id,
                    name=entity_id,
                    domain=domain,
                    state=entity.get("state", "unknown"),
                    friendly_name=entity.get("attributes", {}).get("friendly_name", entity_id),
                    attributes=entity.get("attributes", {}),
                )
                devices[entity_id] = dev

        with self._lock:
            self._devices = devices
            self._state.device_count = len(devices)
            self._state.last_sync = time.time()

        return {"ok": True, "count": len(devices), "devices": [asdict(d) for d in devices.values()]}

    def get_devices(self, domain: str = "") -> list[dict]:
        with self._lock:
            if domain:
                return [asdict(d) for d in self._devices.values() if d.domain == domain]
            return [asdict(d) for d in self._devices.values()]

    # ── Control ──────────────────────────────────────────────

    def control_device(self, entity_id: str, action: str, params: dict | None = None) -> dict:
        """Control a device.

        Args:
            entity_id: HA entity ID (e.g. "light.living_room")
            action: on, off, toggle, set_temperature, play, pause, etc.
            params: Additional parameters (brightness, color, temperature, etc.)
        """
        domain = entity_id.split(".")[0] if "." in entity_id else ""

        service_map = {
            "on": "turn_on",
            "off": "turn_off",
            "toggle": "toggle",
            "set_temperature": "set_temperature",
            "set_hvac": "set_hvac_mode",
            "play": "media_play",
            "pause": "media_pause",
            "stop": "media_stop",
            "next": "media_next_track",
            "volume_up": "volume_up",
            "volume_down": "volume_down",
        }

        service = service_map.get(action, action)
        path = f"/api/services/{domain}/{service}"
        data = {"entity_id": entity_id}

        if params:
            # Brightness 0-100 -> 0-255
            if "brightness" in params:
                data["brightness"] = int(params["brightness"] * 2.55)
            if "temperature" in params:
                data["temperature"] = params["temperature"]
            if "color" in params:
                data["color_name"] = params["color"]
            if "volume" in params:
                data["volume_level"] = params["volume"] / 100.0
            if "hvac_mode" in params:
                data["hvac_mode"] = params["hvac_mode"]

        result = self._ha_post(path, data)

        with self._lock:
            if result.get("ok"):
                self._state.command_count += 1
                self._state.last_command = f"{action} {entity_id}"
            else:
                self._state.error_count += 1
                self._state.last_error = result.get("error", "")

        return result

    def activate_scene(self, scene_id: str) -> dict:
        """Activate a Home Assistant scene."""
        return self._ha_post("/api/services/scene/turn_on", {"entity_id": scene_id})

    # ── Voice command parsing ────────────────────────────────

    def parse_voice_command(self, text: str) -> dict:
        """Parse a natural language command into an IoT action.

        Examples:
            "enciende la luz del salon" -> light.living_room turn_on
            "apaga todas las luces" -> light.all turn_off
            "pon el termostato a 22" -> climate.thermostat set_temperature 22
            "activa escena noche" -> scene.night activate
        """
        text_lower = text.lower().strip()

        # Detect action
        if any(w in text_lower for w in ["enciende", "encender", "activa", "pon"]):
            action = "on"
        elif any(w in text_lower for w in ["apaga", "apagar", "desactiva"]):
            action = "off"
        elif "temperatura" in text_lower:
            action = "set_temperature"
        elif "escena" in text_lower:
            action = "scene"
        elif any(w in text_lower for w in ["sube", "aumenta"]):
            action = "volume_up"
        elif any(w in text_lower for w in ["baja", "diminuye"]):
            action = "volume_down"
        else:
            return {"ok": False, "error": "Could not determine action from command"}

        # Find entity by alias
        entity_id = None
        for alias, eid in self._device_map.items():
            if alias in text_lower:
                entity_id = eid
                break

        if not entity_id and action == "on" and "todas" in text_lower:
            entity_id = "light.all"

        if not entity_id:
            return {"ok": False, "error": f"No device found for: {text}"}

        # Extract temperature if applicable
        params = {}
        if action == "set_temperature":
            temp_match = re.search(r"(\d+)\s*grados?", text_lower)
            if temp_match:
                params["temperature"] = int(temp_match.group(1))
            else:
                return {"ok": False, "error": "Could not find temperature value"}

        # Execute
        if action == "scene":
            return self.activate_scene(entity_id)
        else:
            return self.control_device(entity_id, action, params)

    # ── State ────────────────────────────────────────────────

    def get_state(self) -> dict:
        with self._lock:
            return asdict(self._state)

    def get_device_map(self) -> dict:
        return dict(self._device_map)

    def add_alias(self, alias: str, entity_id: str) -> dict:
        self._device_map[alias.lower()] = entity_id
        self._save_device_map()
        return {"ok": True, "alias": alias, "entity_id": entity_id}

    def save_state(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.get_state(), f, indent=2, ensure_ascii=False)


# ── Singleton ─────────────────────────────────────────────────

_instance: IoTRealIntegration | None = None


def get_instance() -> IoTRealIntegration:
    global _instance
    if _instance is None:
        _instance = IoTRealIntegration()
    return _instance


# ── Flask route registration ──────────────────────────────────


def register_iot_routes(flask_app):
    """Register IoT routes in daniela_os.py."""

    @flask_app.route("/api/iot/status")
    def iot_status():
        return flask_app.jsonify(get_instance().get_state())

    @flask_app.route("/api/iot/devices")
    def iot_devices():
        domain = flask_app.request.args.get("domain", "")
        return flask_app.jsonify({"devices": get_instance().get_devices(domain)})

    @flask_app.route("/api/iot/sync", methods=["POST"])
    def iot_sync():
        return flask_app.jsonify(get_instance().sync_devices())

    @flask_app.route("/api/iot/control", methods=["POST"])
    def iot_control():
        data = flask_app.request.json or {}
        entity_id = data.get("entity_id", "")
        action = data.get("action", "")
        params = data.get("params", {})
        if not entity_id or not action:
            return flask_app.jsonify({"ok": False, "error": "Missing entity_id or action"}), 400
        return flask_app.jsonify(get_instance().control_device(entity_id, action, params))

    @flask_app.route("/api/iot/scene", methods=["POST"])
    def iot_scene():
        scene_id = (flask_app.request.json or {}).get("scene_id", "")
        return flask_app.jsonify(get_instance().activate_scene(scene_id))

    @flask_app.route("/api/iot/voice", methods=["POST"])
    def iot_voice():
        text = (flask_app.request.json or {}).get("text", "")
        return flask_app.jsonify(get_instance().parse_voice_command(text))

    @flask_app.route("/api/iot/aliases")
    def iot_aliases():
        return flask_app.jsonify(get_instance().get_device_map())

    @flask_app.route("/api/iot/alias", methods=["POST"])
    def iot_add_alias():
        data = flask_app.request.json or {}
        return flask_app.jsonify(
            get_instance().add_alias(data.get("alias", ""), data.get("entity_id", ""))
        )

    print(
        "[IoT Integration] Routes registered: /api/iot/* (status, devices, sync, control, scene, voice, aliases)"
    )


# ── CLI ───────────────────────────────────────────────────────


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python iot_real_integration.py [status|devices|voice <text>|aliases]")
        return

    cmd = sys.argv[1]
    iot = get_instance()

    if cmd == "status":
        print(json.dumps(iot.get_state(), indent=2))
    elif cmd == "devices":
        iot.sync_devices()
        devs = iot.get_devices()
        print(f"Devices: {len(devs)}")
        for d in devs[:20]:
            print(f"  {d['entity_id']}: {d['state']} ({d['friendly_name']})")
    elif cmd == "voice":
        text = " ".join(sys.argv[2:])
        if not text:
            text = "enciende la luz del salon"
        result = iot.parse_voice_command(text)
        print(f"Command: {text}")
        print(json.dumps(result, indent=2))
    elif cmd == "aliases":
        print(json.dumps(iot.get_device_map(), indent=2))
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
