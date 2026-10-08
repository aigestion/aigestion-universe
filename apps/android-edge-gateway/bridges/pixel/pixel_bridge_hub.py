#!/usr/bin/env python3
"""
Pixel Bridge Hub (PA-01)
=========================
Controlador del lado del PC que descubre el Pixel en la WiFi,
llama al Termux API Gateway, y expone endpoints /api/pixel/*
en daniela_os.py con fallback graceful cuando el Pixel esta offline.

Funciones:
  - Discovery: intenta IPs conocidas + mDNS (zeroconf si disponible)
  - Cache: cachea respuestas por 10s para no saturar el Pixel
  - Fallback: si el Pixel no responde, retorna datos cached o error limpio
  - Sync: sincroniza estado del Pixel al PC (bateria, ubicacion, etc.)

Uso desde daniela_os.py:
    from bridges.pixel.pixel_bridge_hub import pixel_bridge, register_pixel_routes
    register_pixel_routes(app)  # anade /api/pixel/* a Flask

Cost: $0 — solo HTTP requests, no necesita servidor
"""

import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests

# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = PROJECT_ROOT / "data" / "pixel_bridge" / "pixel_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# IPs conocidas del Pixel (se actualizan con discovery)
# 2026-09-25: Lee KNOWN_IPS desde .env (PIXEL_IPS, PIXEL_IP) + fallback hardcoded
def _load_known_ips():
    """Carga IPs conocidas desde .env (PIXEL_IPS, PIXEL_IP) + fallback hardcoded."""
    ips = []
    # 1. PIXEL_IPS (comma-separated)
    pixel_ips = os.getenv("PIXEL_IPS", "")
    if pixel_ips:
        ips.extend([ip.strip() for ip in pixel_ips.split(",") if ip.strip()])
    # 2. PIXEL_IP (single)
    pixel_ip = os.getenv("PIXEL_IP", "")
    if pixel_ip and pixel_ip not in ips:
        ips.append(pixel_ip.strip())
    # 3. Fallback hardcoded
    fallback = ["192.168.1.133", "192.168.1.170", "192.168.1.100"]
    for ip in fallback:
        if ip not in ips:
            ips.append(ip)
    return ips


KNOWN_IPS = _load_known_ips()
GATEWAY_PORT = int(os.getenv("PIXEL_GATEWAY_PORT", "8082"))
AUTH_TOKEN = os.getenv("PIXEL_TOKEN", "")  # debe coincidir con termux_api_gateway.py
CACHE_TTL = 10  # segundos
DISCOVERY_TIMEOUT = 1.5  # segundos por IP
REQUEST_TIMEOUT = 5  # segundos para requests al Pixel


@dataclass
class PixelState:
    """Estado cached del Pixel."""

    online: bool = False
    ip: str = ""
    last_seen: str = ""
    last_health: Dict = field(default_factory=dict)
    battery: Dict = field(default_factory=dict)
    location: Dict = field(default_factory=dict)
    battery_updated: float = 0
    location_updated: float = 0


class PixelBridgeHub:
    """Controlador central para comunicar PC con Pixel."""

    def __init__(self):
        self._state = PixelState()
        self._cache: Dict[str, tuple] = {}  # endpoint -> (timestamp, data)
        self._discovered_ip: Optional[str] = None
        self._last_discovery = 0
        self._load_state()

    def _load_state(self):
        """Carga estado desde archivo."""
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self._discovered_ip = data.get("discovered_ip")
                self._state.online = data.get("online", False)
                self._state.ip = data.get("ip", "")
                self._state.last_seen = data.get("last_seen", "")
            except (json.JSONDecodeError, KeyError):
                pass

    def _save_state(self):
        """Guarda estado en archivo."""
        data = {
            "discovered_ip": self._discovered_ip,
            "online": self._state.online,
            "ip": self._state.ip,
            "last_seen": self._state.last_seen,
            "battery": self._state.battery,
            "location": self._state.location,
            "updated_at": datetime.now().isoformat(),
        }
        STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _discover(self) -> Optional[str]:
        """Descubre el Pixel en la red local. Intenta IPs conocidas + discovery."""
        now = time.time()
        # No re-descubrir si ya encontramos el Pixel hace menos de 60s
        if self._discovered_ip and (now - self._last_discovery) < 60:
            if self._ping(self._discovered_ip):
                return self._discovered_ip

        self._last_discovery = now

        # Intentar IPs conocidas
        for ip in KNOWN_IPS + ([self._discovered_ip] if self._discovered_ip else []):
            if self._ping(ip):
                self._discovered_ip = ip
                self._state.online = True
                self._state.ip = ip
                self._state.last_seen = datetime.now().isoformat()
                self._save_state()
                return ip

        # Intentar mDNS discovery (si zeroconf esta disponible)
        try:
            from zeroconf import (  # noqa: F401 — sonda de dependencia opcional (mDNS pendiente)
                ServiceBrowser,
                Zeroconf,
            )

            # Non-blocking approach: try direct socket
            pass  # mDNS es complejo, fallback a IPs conocidas
        except ImportError:
            pass

        self._state.online = False
        self._save_state()
        return None

    def _ping(self, ip: str) -> bool:
        """Hace un health check al Pixel."""
        try:
            url = f"http://{ip}:{GATEWAY_PORT}/api/pixel/health"
            headers = {"X-Pixel-Token": AUTH_TOKEN}
            r = requests.get(url, headers=headers, timeout=DISCOVERY_TIMEOUT)
            return r.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    def _get_cached(self, endpoint: str) -> Optional[Any]:
        """Retorna data cached si es fresca."""
        if endpoint in self._cache:
            ts, data = self._cache[endpoint]
            if time.time() - ts < CACHE_TTL:
                return data
        return None

    def _set_cached(self, endpoint: str, data: Any):
        """Guarda data en cache."""
        self._cache[endpoint] = (time.time(), data)

    def call(self, endpoint: str, method: str = "GET", data: Optional[dict] = None) -> Dict:
        """
        Llama a un endpoint del Termux API Gateway.
        Retorna dict con ok/error/data.
        """
        # Check cache para GET
        if method == "GET":
            cached = self._get_cached(endpoint)
            if cached is not None:
                return cached

        # Descubrir Pixel
        ip = self._discover()
        if not ip:
            return {"ok": False, "error": "Pixel not found on network", "online": False}

        # Hacer request
        url = f"http://{ip}:{GATEWAY_PORT}{endpoint}"
        headers = {"X-Pixel-Token": AUTH_TOKEN}

        try:
            if method == "GET":
                r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            elif method == "POST":
                r = requests.post(url, headers=headers, json=data or {}, timeout=REQUEST_TIMEOUT)
            else:
                return {"ok": False, "error": f"Unsupported method: {method}"}

            if r.status_code == 200:
                result = r.json()
                if method == "GET":
                    self._set_cached(endpoint, result)
                return result
            else:
                return {"ok": False, "error": f"HTTP {r.status_code}", "body": r.text[:200]}

        except requests.Timeout:
            self._state.online = False
            self._save_state()
            return {"ok": False, "error": "Request timeout", "online": False}
        except requests.ConnectionError:
            self._state.online = False
            self._save_state()
            return {"ok": False, "error": "Connection refused — Pixel may be offline"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ========================================================================
    # HIGH-LEVEL API — usada por daniela_os.py y otros modulos
    # ========================================================================

    def get_battery(self) -> Dict:
        """Estado de bateria del Pixel."""
        result = self.call("/api/pixel/battery")
        if result.get("ok"):
            self._state.battery = result.get("data", {})
            self._state.battery_updated = time.time()
            self._save_state()
        return result

    def get_location(self) -> Dict:
        """Coordenadas GPS del Pixel."""
        result = self.call("/api/pixel/location")
        if result.get("ok"):
            self._state.location = result.get("data", {})
            self._state.location_updated = time.time()
            self._save_state()
        return result

    def take_photo(self, filename: str = None, camera: int = 0) -> Dict:
        """Toma una foto con la camara del Pixel."""
        return self.call(
            "/api/pixel/camera", method="POST", data={"filename": filename, "camera": camera}
        )

    def torch(self, on: bool = True) -> Dict:
        """Controla la linterna."""
        return self.call("/api/pixel/torch", method="POST", data={"state": on})

    def speak(self, text: str, lang: str = "es") -> Dict:
        """TTS en el Pixel."""
        return self.call("/api/pixel/tts", method="POST", data={"text": text, "lang": lang})

    def vibrate(self, duration: int = 80) -> Dict:
        """Vibracion haptica."""
        return self.call("/api/pixel/vibrate", method="POST", data={"duration": duration})

    def get_notifications(self) -> Dict:
        """Notificaciones de Android."""
        return self.call("/api/pixel/notifications")

    def send_sms(self, number: str, message: str) -> Dict:
        """Envia SMS desde el Pixel."""
        return self.call(
            "/api/pixel/sms/send", method="POST", data={"number": number, "message": message}
        )

    def call_phone(self, number: str) -> Dict:
        """Hace una llamada desde el Pixel."""
        return self.call("/api/pixel/call", method="POST", data={"number": number})

    def get_status(self) -> Dict:
        """Estado completo del bridge."""
        return {
            "online": self._state.online,
            "ip": self._state.ip or self._discovered_ip or "",
            "last_seen": self._state.last_seen,
            "battery": self._state.battery,
            "location": self._state.location,
            "cache_size": len(self._cache),
            "endpoints_available": 20,
        }


# Singleton
pixel_bridge = PixelBridgeHub()


# ============================================================================
# FLASK ROUTE REGISTRATION
# ============================================================================


def register_pixel_routes(flask_app):
    """
    Registra todos los endpoints /api/pixel/* en una app Flask existente.

    Uso:
        from bridges.pixel.pixel_bridge_hub import register_pixel_routes
        register_pixel_routes(app)  # app = Flask instance from daniela_os.py
    """

    @flask_app.route("/api/pixel/status")
    def api_pixel_status():
        """Estado del bridge Pixel."""
        return _json_response(pixel_bridge.get_status())

    @flask_app.route("/api/pixel/battery")
    def api_pixel_battery():
        return _json_response(pixel_bridge.get_battery())

    @flask_app.route("/api/pixel/location")
    def api_pixel_location():
        return _json_response(pixel_bridge.get_location())

    @flask_app.route("/api/pixel/torch", methods=["POST"])
    def api_pixel_torch():
        import flask

        data = flask.request.get_json(silent=True) or {}
        return _json_response(pixel_bridge.torch(data.get("state", True)))

    @flask_app.route("/api/pixel/camera", methods=["POST"])
    def api_pixel_camera():
        import flask

        data = flask.request.get_json(silent=True) or {}
        return _json_response(pixel_bridge.take_photo(data.get("filename"), data.get("camera", 0)))

    @flask_app.route("/api/pixel/tts", methods=["POST"])
    def api_pixel_tts():
        import flask

        data = flask.request.get_json(silent=True) or {}
        return _json_response(pixel_bridge.speak(data.get("text", ""), data.get("lang", "es")))

    @flask_app.route("/api/pixel/vibrate", methods=["POST"])
    def api_pixel_vibrate():
        import flask

        data = flask.request.get_json(silent=True) or {}
        return _json_response(pixel_bridge.vibrate(data.get("duration", 80)))

    @flask_app.route("/api/pixel/notifications")
    def api_pixel_notifications():
        return _json_response(pixel_bridge.get_notifications())

    @flask_app.route("/api/pixel/sms", methods=["POST"])
    def api_pixel_sms():
        import flask

        data = flask.request.get_json(silent=True) or {}
        return _json_response(
            pixel_bridge.send_sms(data.get("number", ""), data.get("message", ""))
        )

    @flask_app.route("/api/pixel/call", methods=["POST"])
    def api_pixel_call():
        import flask

        data = flask.request.get_json(silent=True) or {}
        return _json_response(pixel_bridge.call_phone(data.get("number", "")))

    @flask_app.route("/api/pixel/discover")
    def api_pixel_discover():
        """Fuerza discovery del Pixel."""
        ip = pixel_bridge._discover()
        return _json_response(
            {
                "online": ip is not None,
                "ip": ip or "",
                "known_ips": KNOWN_IPS,
            }
        )

    # Background thread para discovery periodico
    def _bg_discovery():
        while True:
            try:
                pixel_bridge._discover()
            except Exception:
                pass
            time.sleep(120)  # cada 2 min

    thread = threading.Thread(target=_bg_discovery, daemon=True)
    thread.start()


def _json_response(data):
    """Helper para retornar JSON en Flask."""
    from flask import jsonify

    return jsonify(data)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import os
    import sys

    print("=" * 50)
    print("  PIXEL BRIDGE HUB (PA-01)")
    print("=" * 50)

    if len(sys.argv) < 2:
        print(
            "  Usage: python pixel_bridge_hub.py status|discover|battery|location|torch|photo|tts|sms|call"
        )
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "status":
        status = pixel_bridge.get_status()
        print(f"  Online: {status['online']}")
        print(f"  IP: {status['ip']}")
        print(f"  Last seen: {status['last_seen']}")
        if status["battery"]:
            print(f"  Battery: {status['battery']}")
        if status["location"]:
            print(f"  Location: {status['location']}")

    elif cmd == "discover":
        print("  Discovering Pixel...")
        ip = pixel_bridge._discover()
        if ip:
            print(f"  Found Pixel at {ip}:{GATEWAY_PORT}")
        else:
            print("  Pixel not found. Tried IPs:", KNOWN_IPS)

    elif cmd == "battery":
        result = pixel_bridge.get_battery()
        print(f"  {result}")

    elif cmd == "location":
        result = pixel_bridge.get_location()
        print(f"  {result}")

    elif cmd == "torch":
        on = len(sys.argv) < 3 or sys.argv[2] != "off"
        result = pixel_bridge.torch(on)
        print(f"  {'ON' if on else 'OFF'}: {result}")

    elif cmd == "photo":
        result = pixel_bridge.take_photo()
        print(f"  Photo: {result}")

    elif cmd == "tts":
        text = " ".join(sys.argv[2:]) or "Hola comandante"
        result = pixel_bridge.speak(text)
        print(f"  TTS: {result}")

    elif cmd == "sms":
        if len(sys.argv) < 4:
            print("  Usage: python pixel_bridge_hub.py sms <number> <message>")
        else:
            result = pixel_bridge.send_sms(sys.argv[2], " ".join(sys.argv[3:]))
            print(f"  SMS: {result}")

    elif cmd == "call":
        if len(sys.argv) < 3:
            print("  Usage: python pixel_bridge_hub.py call <number>")
        else:
            result = pixel_bridge.call_phone(sys.argv[2])
            print(f"  Call: {result}")

    else:
        print(f"  Unknown command: {cmd}")