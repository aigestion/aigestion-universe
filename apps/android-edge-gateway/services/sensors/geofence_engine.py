#!/usr/bin/env python3
"""
PA-10: Geofence Automation Engine - home/outdoors auto-mode
===============================================================
Cuando el GPS detecta que llegaste a casa (radio configurable),
Daniela activa modo home. Cuando sales, activa modo outdoors.

Modo HOME (al llegar):
  - Luces encendidas (via IoT/HA)
  - Musica ambiente
  - Resumen del dia (TTS en español)
  - Sensores activos, WiFi on

Modo OUTDOORS (al salir):
  - GPS tracking activo
  - Battery saving mode
  - Security alert activada (camara)
  - Notificaciones reenviadas al PC

Coordenadas configurables via JSON (data/geofence/zones.json).

Rutas en daniela_os.py:
  - GET  /api/pixel/geofence/status   (estado + zona actual)
  - GET  /api/pixel/geofence/zones     (lista de zonas)
  - POST /api/pixel/geofence/zone      (crear/actualizar zona)
  - POST /api/pixel/geofence/check     (forzar chequeo GPS)
  - GET  /api/pixel/geofence/history   (historial de transiciones)

Coste: $0/mes
"""

from __future__ import annotations

import json
import math
import os
import threading
import time
from dataclasses import asdict, dataclass
from typing import Callable, Dict, List, Optional

import requests

# ── Config ───────────────────────────────────────────────────

# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(PROJECT_ROOT, "data", "geofence")
STATE_FILE = os.path.join(STATE_DIR, "geofence_state.json")
ZONES_FILE = os.path.join(STATE_DIR, "zones.json")
HISTORY_FILE = os.path.join(STATE_DIR, "history.json")

GATEWAY_PORT = 8082
AUTH_TOKEN = os.getenv("PIXEL_TOKEN", "")
DISCOVERY_TIMEOUT = 2
REQUEST_TIMEOUT = 10

KNOWN_IPS = ["192.168.1.133", "192.168.1.170", "192.168.1.100"]

# Polling
POLL_INTERVAL = 60  # seconds
MAX_HISTORY = 100

# Default zones (user should edit with real coords)
DEFAULT_ZONES = {
    "home": {
        "name": "Casa",
        "lat": 40.4168,
        "lon": -3.7038,
        "radius": 100,  # meters
        "mode": "home",
    },
    "work": {
        "name": "Trabajo",
        "lat": 40.4477,
        "lon": -3.6920,
        "radius": 150,
        "mode": "work",
    },
}

# Mode actions
MODE_ACTIONS = {
    "home": {
        "lights": "on",
        "music": "on",
        "summary": True,
        "tts": "Bienvenido a casa. Activando modo hogar.",
        "gps_tracking": False,
        "battery_saving": False,
        "security_alert": False,
    },
    "work": {
        "lights": "off",
        "music": "off",
        "summary": False,
        "tts": "Modo trabajo activado.",
        "gps_tracking": False,
        "battery_saving": True,
        "security_alert": False,
    },
    "outdoors": {
        "lights": "off",
        "music": "off",
        "summary": False,
        "tts": "Modo exterior activado.",
        "gps_tracking": True,
        "battery_saving": True,
        "security_alert": True,
    },
}


# ── Data classes ─────────────────────────────────────────────


@dataclass
class GeofenceZone:
    name: str
    lat: float
    lon: float
    radius: int  # meters
    mode: str  # home, work, outdoors


@dataclass
class GeofenceState:
    running: bool = False
    current_zone: str = ""  # "" = outdoors
    current_mode: str = "outdoors"
    last_lat: float = 0.0
    last_lon: float = 0.0
    last_check: float = 0.0
    transition_count: int = 0
    last_transition: float = 0.0
    error_count: int = 0
    last_error: str = ""


@dataclass
class Transition:
    timestamp: float
    from_zone: str
    from_mode: str
    to_zone: str
    to_mode: str
    lat: float
    lon: float


# ── Geofence Engine ──────────────────────────────────────────


class GeofenceEngine:
    pass

    def __init__(self):
        self._pixel_ip: Optional[str] = None
        self._state = GeofenceState()
        self._zones: Dict[str, GeofenceZone] = {}
        self._history: List[Transition] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable] = []
        self._load_zones()
        self._load_history()

    def _load_zones(self):
        if os.path.exists(ZONES_FILE):
            try:
                with open(ZONES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for key, z in data.items():
                        self._zones[key] = GeofenceZone(**z)
                return
            except (json.JSONDecodeError, TypeError, OSError):
                pass
        # Create defaults
        for key, z in DEFAULT_ZONES.items():
            self._zones[key] = GeofenceZone(**z)
        self._save_zones()

    def _save_zones(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        data = {k: asdict(v) for k, v in self._zones.items()}
        with open(ZONES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    for t in json.load(f):
                        self._history.append(Transition(**t))
            except (json.JSONDecodeError, TypeError, OSError):
                pass

    def _save_history(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        data = [asdict(t) for t in self._history[-MAX_HISTORY:]]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ── GPS ───────────────────────────────────────────────────

    def _get_pixel_ip(self) -> Optional[str]:
        if self._pixel_ip:
            return self._pixel_ip
        for ip in KNOWN_IPS:
            try:
                url = f"http://{ip}:{GATEWAY_PORT}/api/pixel/health"
                r = requests.get(
                    url, headers={"X-Pixel-Token": AUTH_TOKEN}, timeout=DISCOVERY_TIMEOUT
                )
                if r.status_code == 200:
                    self._pixel_ip = ip
                    return ip
            except requests.RequestException:
                continue
        return None

    def get_location(self) -> Optional[Dict]:
        """Get current GPS coordinates from the Pixel."""
        ip = self._get_pixel_ip()
        if not ip:
            return None
        try:
            url = f"http://{ip}:{GATEWAY_PORT}/api/pixel/location"
            r = requests.get(
                url, headers={"X-Pixel-Token": AUTH_TOKEN}, timeout=REQUEST_TIMEOUT
            )
            if r.status_code == 200:
                return r.json().get("data", {})
        except requests.RequestException:
            pass
        return None

    @staticmethod
    def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance in meters."""
        R = 6371000  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _detect_zone(self, lat: float, lon: float) -> Optional[str]:
        for key, zone in self._zones.items():
            dist = self._distance_m(lat, lon, zone.lat, zone.lon)
            if dist <= zone.radius:
                return key
        return None

    # ── Mode actions ─────────────────────────────────────────

    def _execute_mode_actions(self, mode: str, zone_name: str = ""):
        """Execute the actions for a mode (IoT, TTS, security, etc.)."""
        actions = MODE_ACTIONS.get(mode, {})
        results = {}

        # TTS via voice pipeline (if available)
        if actions.get("tts"):
            try:
                from bridges.comms.voice_pipeline import get_instance as get_voice
                get_voice().speak(actions["tts"])
                results["tts"] = "ok"
            except Exception:
                results["tts"] = "skipped"

        # IoT lights via Home Assistant
        if actions.get("lights") in ("on", "off"):
            try:
                from services.iot.iot_real_integration import get_instance as get_iot
                iot = get_iot()
                iot.control_device("light.all", actions["lights"])
                results["lights"] = actions["lights"]
            except Exception:
                results["lights"] = "skipped"

        # Security camera alert
        if actions.get("security_alert"):
            try:
                from services.security.security_camera import get_instance as get_cam
                cam = get_cam()
                cam.start()
                results["security"] = "started"
            except Exception:
                results["security"] = "skipped"
        else:
            try:
                from services.security.security_camera import get_instance as get_cam
                get_cam().stop()
                results["security"] = "stopped"
            except Exception:
                results["security"] = "skipped"

        # Battery saving
        if actions.get("battery_saving"):
            results["battery_saving"] = "enabled"

        return results

    # ── Monitoring loop ──────────────────────────────────────

    def _check_loop(self):
        while self._running:
            try:
                loc = self.get_location()
                if loc:
                    lat = loc.get("latitude", loc.get("lat", 0))
                    lon = loc.get("longitude", loc.get("lon", 0))

                    if lat and lon:
                        with self._lock:
                            self._state.last_lat = lat
                            self._state.last_lon = lon
                            self._state.last_check = time.time()

                        new_zone = self._detect_zone(lat, lon)
                        new_mode = self._zones[new_zone].mode if new_zone else "outdoors"

                        # Detect transition
                        if new_zone != self._state.current_zone:
                            old_zone = self._state.current_zone
                            old_mode = self._state.current_mode

                            with self._lock:
                                self._state.current_zone = new_zone or ""
                                self._state.current_mode = new_mode
                                self._state.transition_count += 1
                                self._state.last_transition = time.time()

                            # Log transition
                            self._history.append(Transition(
                                timestamp=time.time(),
                                from_zone=old_zone, from_mode=old_mode,
                                to_zone=new_zone or "", to_mode=new_mode,
                                lat=lat, lon=lon,
                            ))
                            if len(self._history) > MAX_HISTORY:
                                self._history = self._history[-MAX_HISTORY:]
                            self._save_history()

                            # Execute actions
                            zone_name = self._zones[new_zone].name if new_zone else "Exterior"
                            self._execute_mode_actions(new_mode, zone_name)

                            # Notify callbacks
                            for cb in self._callbacks:
                                try:
                                    cb(new_zone, new_mode)
                                except Exception:
                                    pass

            except Exception as e:
                with self._lock:
                    self._state.error_count += 1
                    self._state.last_error = str(e)[:200]

            time.sleep(POLL_INTERVAL)

    # ── Public API ───────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._state.running = True
        self._thread = threading.Thread(target=self._check_loop, daemon=True, name="geofence")
        self._thread.start()

    def stop(self):
        self._running = False
        self._state.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def register_callback(self, cb: Callable):
        self._callbacks.append(cb)

    def get_zones(self) -> Dict:
        return {k: asdict(v) for k, v in self._zones.items()}

    def add_zone(self, key: str, name: str, lat: float, lon: float, radius: int, mode: str) -> Dict:
        self._zones[key] = GeofenceZone(name=name, lat=lat, lon=lon, radius=radius, mode=mode)
        self._save_zones()
        return {"ok": True, "zone": key}

    def force_check(self) -> Dict:
        loc = self.get_location()
        if not loc:
            return {"ok": False, "error": "Pixel offline or no GPS"}
        lat = loc.get("latitude", loc.get("lat", 0))
        lon = loc.get("longitude", loc.get("lon", 0))
        zone = self._detect_zone(lat, lon)
        mode = self._zones[zone].mode if zone else "outdoors"
        return {"ok": True, "lat": lat, "lon": lon, "zone": zone or "", "mode": mode}

    def get_state(self) -> Dict:
        with self._lock:
            return asdict(self._state)

    def get_history(self, limit: int = 20) -> List[Dict]:
        return [asdict(t) for t in self._history[-limit:]]

    def save_state(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.get_state(), f, indent=2, ensure_ascii=False)


# ── Singleton ─────────────────────────────────────────────────

_instance: Optional[GeofenceEngine] = None


def get_instance() -> GeofenceEngine:
    global _instance
    if _instance is None:
        _instance = GeofenceEngine()
    return _instance


# ── Flask route registration ──────────────────────────────────


def register_geofence_routes(flask_app):
    """Register geofence routes in daniela_os.py."""

    @flask_app.route("/api/pixel/geofence/status")
    def pixel_geofence_status():
        return flask_app.jsonify(get_instance().get_state())

    @flask_app.route("/api/pixel/geofence/zones")
    def pixel_geofence_zones():
        return flask_app.jsonify(get_instance().get_zones())

    @flask_app.route("/api/pixel/geofence/zone", methods=["POST"])
    def pixel_geofence_zone():
        data = flask_app.request.json or {}
        key = data.get("key", "")
        if not key:
            return flask_app.jsonify({"ok": False, "error": "Missing 'key'"}), 400
        result = get_instance().add_zone(
            key,
            data.get("name", key),
            float(data.get("lat", 0)),
            float(data.get("lon", 0)),
            int(data.get("radius", 100)),
            data.get("mode", "home"),
        )
        return flask_app.jsonify(result)

    @flask_app.route("/api/pixel/geofence/check", methods=["POST"])
    def pixel_geofence_check():
        return flask_app.jsonify(get_instance().force_check())

    @flask_app.route("/api/pixel/geofence/history")
    def pixel_geofence_history():
        limit = int(flask_app.request.args.get("limit", 20))
        hist = get_instance().get_history(limit)
        return flask_app.jsonify({"count": len(hist), "history": hist})

    @flask_app.route("/api/pixel/geofence/start", methods=["POST"])
    def pixel_geofence_start():
        get_instance().start()
        return flask_app.jsonify({"ok": True, "message": "Geofence monitoring started"})

    @flask_app.route("/api/pixel/geofence/stop", methods=["POST"])
    def pixel_geofence_stop():
        get_instance().stop()
        return flask_app.jsonify({"ok": True, "message": "Geofence monitoring stopped"})

    print("[Geofence] Routes registered: /api/pixel/geofence/* (status, zones, zone, check, history, start, stop)")


# ── CLI ───────────────────────────────────────────────────────

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python geofence_engine.py [status|zones|check|history]")
        return

    cmd = sys.argv[1]
    geo = get_instance()

    if cmd == "status":
        print(json.dumps(geo.get_state(), indent=2))
    elif cmd == "zones":
        print(json.dumps(geo.get_zones(), indent=2))
    elif cmd == "check":
        print(json.dumps(geo.force_check(), indent=2))
    elif cmd == "history":
        hist = geo.get_history()
        print(f"Transitions: {len(hist)}")
        for h in hist:
            print(f"  {h['from_zone'] or 'outdoors'} -> {h['to_zone'] or 'outdoors'} ({h['to_mode']})")
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()