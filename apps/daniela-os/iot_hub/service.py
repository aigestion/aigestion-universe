"""Fachada IoT: orquesta Home Assistant, aliases de voz y cache de dispositivos.

Canonica desde 2026-10-02 (ADR-IOT-HUB). La logica de control/voz/aliases es
una adaptacion de daniela-os/iot_real_integration.py (copias legacy intactas
para el telefono; consolidacion = fase posterior). El estado vive en
``data/iot`` (``device_map.json`` trackeado, el resto runtime).
"""

from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from iot_hub import config
from iot_hub.backends.homeassistant import HomeAssistantAPI

# Dominios controlables desde la UI/voz
CONTROLLABLE_DOMAINS = ("light", "switch", "climate", "media_player", "scene", "cover", "fan")

# accion -> servicio HA (el resto se pasa tal cual)
SERVICE_MAP = {
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

# alias de voz -> entity_id por defecto (se fusionan con device_map.json)
DEFAULT_ALIASES = {
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


@dataclass
class IoTDevice:
    entity_id: str
    name: str
    domain: str  # light, switch, climate, media_player, scene...
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


class IoTService:
    """Servicio IoT con cache de dispositivos y aliases persistentes."""

    def __init__(self, state_dir: Path | str | None = None):
        self._state_dir = Path(state_dir) if state_dir else config.IOT_STATE_DIR
        self._device_map_file = self._state_dir / "device_map.json"
        self._state = IoTState(ha_url=config.HA_URL)
        self._lock = threading.Lock()
        self._devices: dict[str, IoTDevice] = {}
        self._device_map: dict[str, str] = {}
        self._load_device_map()
        self._init_default_map()

    # ── aliases ───────────────────────────────────────────────

    def _load_device_map(self) -> None:
        if self._device_map_file.exists():
            try:
                self._device_map = json.loads(self._device_map_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                self._device_map = {}

    def _save_device_map(self) -> None:
        self._state_dir.mkdir(parents=True, exist_ok=True)
        content = json.dumps(self._device_map, indent=2, ensure_ascii=False)
        self._device_map_file.write_text(content + "\n", encoding="utf-8")

    def _init_default_map(self) -> None:
        """Fusiona los aliases por defecto; sólo escribe si falta alguno."""
        added = False
        for alias, entity in DEFAULT_ALIASES.items():
            if alias not in self._device_map:
                self._device_map[alias] = entity
                added = True
        if added or not self._device_map_file.exists():
            self._save_device_map()

    def get_device_map(self) -> dict[str, str]:
        return dict(self._device_map)

    def add_alias(self, alias: str, entity_id: str) -> dict[str, Any]:
        if not alias or not entity_id:
            return {"ok": False, "error": "alias y entity_id son obligatorios"}
        self._device_map[alias.lower()] = entity_id
        self._save_device_map()
        return {"ok": True, "alias": alias.lower(), "entity_id": entity_id}

    # ── Home Assistant ────────────────────────────────────────

    def _ha(self) -> HomeAssistantAPI:
        return HomeAssistantAPI(base_url=config.HA_URL, token=config.HA_TOKEN)

    def ha_status(self) -> dict[str, Any]:
        return self._ha().health_check()

    def sync_devices(self) -> dict[str, Any]:
        """Descarga y filtra los dispositivos desde Home Assistant."""
        data = self._ha().get_states()
        if not isinstance(data, list):
            error = (
                data.get("error", "Home Assistant no disponible o sin configurar")
                if data
                else ("Home Assistant no disponible o sin configurar")
            )
            with self._lock:
                self._state.ha_available = False
            return {"ok": False, "error": error}

        devices: dict[str, IoTDevice] = {}
        for entity in data:
            entity_id = entity.get("entity_id", "")
            domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
            if domain not in CONTROLLABLE_DOMAINS:
                continue
            devices[entity_id] = IoTDevice(
                entity_id=entity_id,
                name=entity_id,
                domain=domain,
                state=entity.get("state", "unknown"),
                friendly_name=entity.get("attributes", {}).get("friendly_name", entity_id),
                attributes=entity.get("attributes", {}),
            )

        with self._lock:
            self._devices = devices
            self._state.ha_available = True
            self._state.device_count = len(devices)
            self._state.last_sync = time.time()
        return {"ok": True, "count": len(devices), "devices": [asdict(d) for d in devices.values()]}

    def get_devices(self, domain: str = "") -> list[dict[str, Any]]:
        with self._lock:
            if domain:
                return [asdict(d) for d in self._devices.values() if d.domain == domain]
            return [asdict(d) for d in self._devices.values()]

    def control_device(
        self, entity_id: str, action: str, params: dict | None = None
    ) -> dict[str, Any]:
        """Controla un dispositivo HA (on/off/toggle/set_temperature/...)."""
        domain = entity_id.split(".")[0] if "." in entity_id else ""
        if not domain:
            return {"ok": False, "error": f"entity_id invalido: {entity_id}"}

        service = SERVICE_MAP.get(action, action)
        data: dict[str, Any] = {"entity_id": entity_id}
        if params:
            if "brightness" in params:  # 0-100 -> 0-255
                data["brightness"] = int(params["brightness"] * 2.55)
            if "temperature" in params:
                data["temperature"] = params["temperature"]
            if "color" in params:
                data["color_name"] = params["color"]
            if "volume" in params:
                data["volume_level"] = params["volume"] / 100.0
            if "hvac_mode" in params:
                data["hvac_mode"] = params["hvac_mode"]

        result = self._ha().call_service(domain, service, data)
        ok = not (isinstance(result, dict) and "error" in result)

        with self._lock:
            if ok:
                self._state.ha_available = True
                self._state.command_count += 1
                self._state.last_command = f"{action} {entity_id}"
            else:
                self._state.error_count += 1
                self._state.last_error = str((result or {}).get("error", ""))[:200]

        if ok:
            return {"ok": True, "entity_id": entity_id, "action": service, "params": params or {}}
        return {
            "ok": False,
            "entity_id": entity_id,
            "action": service,
            "error": str((result or {}).get("error", "fallo desconocido")),
        }

    def activate_scene(self, scene_id: str) -> dict[str, Any]:
        """Activa una escena HA."""
        if not scene_id:
            return {"ok": False, "error": "scene_id obligatorio"}
        result = self._ha().call_service("scene", "turn_on", {"entity_id": scene_id})
        if isinstance(result, dict) and "error" in result:
            return {"ok": False, "scene": scene_id, "error": str(result.get("error"))}
        return {"ok": True, "scene": scene_id}

    # ── comando de voz ────────────────────────────────────────

    def parse_voice_command(self, text: str) -> dict[str, Any]:
        """Convierte una frase natural en una accion IoT.

        "enciende la luz del salon" -> light.living_room turn_on
        "apaga todas las luces"     -> light.all turn_off
        "pon el termostato a 22"    -> climate.thermostat set_temperature 22
        "activa escena noche"       -> scene.night turn_on
        """
        text_lower = text.lower().strip()

        # Orden importa: la intencion de temperatura va ANTES de "pon"/"enciende"
        # (bug heredado: "pon el termostato a 22" acababa en turn_on sin temp)
        temp_intent = (
            "temperatura" in text_lower
            or bool(re.search(r"\d{1,2}\s*grados?", text_lower))
            or (
                any(w in text_lower for w in ("termostato", "clima", "calefacci", "aire acond"))
                and bool(re.search(r"\b\d{1,2}\b", text_lower))
            )
        )
        if temp_intent:
            action = "set_temperature"
        elif any(w in text_lower for w in ("enciende", "encender", "activa", "pon")):
            action = "on"
        elif any(w in text_lower for w in ("apaga", "apagar", "desactiva")):
            action = "off"
        elif "escena" in text_lower:
            action = "scene"
        elif any(w in text_lower for w in ("sube", "aumenta")):
            action = "volume_up"
        elif any(w in text_lower for w in ("baja", "diminuye")):
            action = "volume_down"
        else:
            return {"ok": False, "error": "No se pudo determinar la accion del comando"}

        entity_id = None
        # Match por tokens: "luz del salon" contiene {luz, salon} -> "luz salon"
        # (el substring a secas no matcheaba "luz del salon"; bug heredado)
        text_tokens = set(re.findall(r"[a-záéíóúñ0-9]+", text_lower))
        for alias, eid in sorted(self._device_map.items(), key=lambda kv: -len(kv[0])):
            alias_tokens = set(re.findall(r"[a-záéíóúñ0-9]+", alias))
            if alias_tokens and alias_tokens <= text_tokens:
                entity_id = eid
                break
        if not entity_id and action == "on" and "todas" in text_lower:
            entity_id = "light.all"
        if not entity_id:
            return {"ok": False, "error": f"No se encontro dispositivo para: {text}"}

        params: dict[str, Any] = {}
        if action == "set_temperature":
            temp_match = re.search(r"\b(\d{1,2})\b", text_lower)
            if not temp_match:
                return {"ok": False, "error": "No se encontro el valor de temperatura"}
            params["temperature"] = int(temp_match.group(1))

        if action == "scene":
            return self.activate_scene(entity_id)
        return self.control_device(entity_id, action, params)

    # ── estado agregado ───────────────────────────────────────

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            return asdict(self._state)


# ── Singleton (perezoso: nada de escritura en import ──────────

_service: IoTService | None = None
_service_lock = threading.Lock()


def get_service() -> IoTService:
    global _service
    with _service_lock:
        if _service is None:
            _service = IoTService()
        return _service
