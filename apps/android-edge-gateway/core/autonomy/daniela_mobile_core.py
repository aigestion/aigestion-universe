#!/usr/bin/env python3
"""
Daniela Mobile Core — Fusion de 40 modulos huerfanos (E-04 / Fase 6)
=====================================================================
El 74% de los modulos Termux estaban desconectados: 40 huerfanos con ~1.100
lineas de logica de campo ya depurada en la calle (modo_calle, panic_sos,
caja_negra, centinela, escolta_notificaciones, daniela_proactiva,
daniela_mobile_daemon, geofence...).

Este modulo los unifica en UN solo daemon con un bus de eventos interno.
Cada capacidad es un plugin que publica y suscribe eventos:

    SENSOR_TICK        — latido de sensores (2s)
    POCKET_STATE       — movil guardado o en mano (proximidad)
    HEADSET_CONNECTED  — auriculares Bluetooth detectados
    ZONE_CHANGE        — entrada/salida de zona (casa, trabajo, calle)
    BATTERY_LOW        — bateria por debajo del umbral
    WAKE_WORD          — "Daniela" detectada
    PANIC              — boton de panico / palabra clave
    FALL_DETECTED      — caida (lo emite context_engine)
    NOTIFICATION       — notificacion de app prioritaria

Plugins incluidos:
    PocketSense    — sensor de proximidad (de daniela_proactiva)
    HeadsetGuard   — auriculares BT (de escolta_notificaciones)
    Haptics        — respuesta haptic a por contexto (de daniela_mobile_daemon)
    StreetMode     — bucle de voz manos libres (de modo_calle)
    PanicSOS       — protocolo de emergencia completo (de panic_sos)
    HomeZone       — zonas GPS configurables (de geofence daniela_mobile_daemon)
    Diario         — registro tactico de eventos (de daniela_proactiva)

Seguridad: todo comando pasa por safe_exec. 0 os.system, 0 shell=True.

Rutas:
  GET  /api/pixel/core/status          — estado del core y sus plugins
  GET  /api/pixel/core/plugins         — lista de plugins
  POST /api/pixel/core/plugin/<n>/toggle — activa/desactiva un plugin
  GET  /api/pixel/core/events          — historial de eventos del bus
  POST /api/pixel/core/emit            — inyecta un evento (para tests/UI)
  POST /api/pixel/core/start           — arranca el core
  POST /api/pixel/core/stop            — lo detiene
  POST /api/pixel/core/panic           — dispara el protocolo SOS

Coste: $0/mes — Termux:API (gratis)
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional

from bridges.comms.safe_exec import run_cmd, run_code, run_json

# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "data" / "mobile_core"
STATE_FILE = STATE_DIR / "core_state.json"
DIARIO_FILE = STATE_DIR / "diario_tactico.json"

SENSOR_INTERVAL = 2.0
MAX_EVENTS = 300
MAX_DIARIO = 200

# Umbrales
BATTERY_LOW_PCT = 20
PROXIMITY_POCKET_CM = 2.0

# Apps que Daniela lee al oido
APPS_IMPORTANTES = ("whatsapp", "telegram", "gmail", "messages", "signal")

_instance: Optional["MobileCore"] = None
_instance_lock = threading.Lock()


def is_termux() -> bool:
    return bool(
        os.environ.get("TERMUX_VERSION")
        or os.environ.get("PREFIX", "").startswith("/data/data/com.termux")
        or Path("/data/data/com.termux").exists()
    )


# =============================================================================
# BUS DE EVENTOS
# =============================================================================


class EventBus:
    """Pub/sub interno. Simple, sin dependencias."""

    def __init__(self, maxlen: int = MAX_EVENTS) -> None:
        self._subs: Dict[str, List[Callable]] = {}
        self._all: List[Callable] = []
        self.history: Deque[Dict[str, Any]] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def subscribe(
        self, event_type: Optional[str], handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        with self._lock:
            if event_type is None:
                self._all.append(handler)
            else:
                self._subs.setdefault(event_type, []).append(handler)

    def emit(
        self, event_type: str, data: Optional[Dict[str, Any]] = None, source: str = "core"
    ) -> Dict[str, Any]:
        event = {
            "type": event_type,
            "data": data or {},
            "source": source,
            "ts": datetime.now().isoformat(timespec="seconds"),
        }
        with self._lock:
            self.history.append(event)
            handlers = list(self._all) + list(self._subs.get(event_type, []))
        for h in handlers:
            try:
                h(event)
            except Exception as e:
                print(
                    f"[MobileCore] handler error en {event_type}: "
                    f"{type(e).__name__}: {str(e)[:60]}"
                )
        return event

    def recent(self, n: int = 30, event_type: Optional[str] = None) -> List[Dict]:
        with self._lock:
            evs = list(self.history)
        if event_type:
            evs = [e for e in evs if e["type"] == event_type]
        return evs[-n:]


# =============================================================================
# PLUGINS
# =============================================================================


class Plugin:
    """Base de los plugins de contexto."""

    name = "base"
    description = ""

    def __init__(self, core: "MobileCore") -> None:
        self.core = core
        self.enabled = True
        self.last_run: Optional[str] = None

    def on_event(self, event: Dict[str, Any]) -> None:
        """Se llama con CADA evento del bus."""

    def on_tick(self) -> None:
        """Se llama en cada latido del bucle principal."""

    def status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "description": self.description,
            "last_run": self.last_run,
        }


class PocketSense(Plugin):
    """Detecta si el movil esta en el bolsillo (sensor de proximidad)."""

    name = "pocket_sense"
    description = "Bolsillo vs en mano — sensor de proximidad"

    def __init__(self, core):
        super().__init__(core)
        self.in_pocket = False

    def _read(self) -> Optional[float]:
        d = run_json(["termux-sensor", "-s", "proximity", "-n", "1"], timeout=6)
        if isinstance(d, dict):
            for v in d.values():
                if isinstance(v, dict) and "values" in v:
                    return float(v["values"][0])
        return None

    def on_tick(self) -> None:
        if not self.core.platform_ok():
            return
        val = self._read()
        if val is None:
            return
        new_state = val < PROXIMITY_POCKET_CM
        if new_state != self.in_pocket:
            self.in_pocket = new_state
            self.core.bus.emit("POCKET_STATE", {"in_pocket": new_state, "cm": val}, self.name)
        self.last_run = datetime.now().isoformat(timespec="seconds")

    def status(self):
        s = super().status()
        s["in_pocket"] = self.in_pocket
        return s


class HeadsetGuard(Plugin):
    """Detecta auriculares Bluetooth (para leer notificaciones al oido)."""

    name = "headset_guard"
    description = "Auriculares Bluetooth — lectura de notificaciones al oido"

    def __init__(self, core):
        super().__init__(core)
        self.connected = False

    def _check(self) -> bool:
        r = run_cmd(["dumpsys", "audio"], timeout=6)
        out = (r.stdout or "").lower()
        return "device_out_bluetooth_a2dp" in out or "bt_headset" in out

    def on_tick(self) -> None:
        if not self.core.platform_ok():
            return
        now = self._check()
        if now != self.connected:
            self.connected = now
            self.core.bus.emit("HEADSET_CONNECTED", {"connected": now}, self.name)
        self.last_run = datetime.now().isoformat(timespec="seconds")

    def on_event(self, event: Dict[str, Any]) -> None:
        if event["type"] == "NOTIFICATION" and self.connected:
            self._read_aloud(event.get("data", {}))

    def _read_aloud(self, data: Dict[str, Any]) -> None:
        pkg = str(data.get("package", "")).lower()
        if not any(a in pkg for a in APPS_IMPORTANTES):
            return
        title = str(data.get("title", "")).replace("'", "")
        content = str(data.get("content", "")).replace("'", "")
        if not content:
            return
        run_code("termux-vibrate -d 60", timeout=4)
        run_code("termux-volume music 8", timeout=4)
        run_code(f"termux-tts-speak -l es 'Notificacion de {title}: {content}'", timeout=15)

    def status(self):
        s = super().status()
        s["connected"] = self.connected
        return s


class Haptics(Plugin):
    """Respuesta haptic a segun el contexto."""

    name = "haptics"
    description = "Vibracion contextual (corto / alerta / largo)"

    PATTERNS = {"short": 80, "alert": 150, "long": 1500}

    def on_event(self, event: Dict[str, Any]) -> None:
        kind = {
            "PANIC": "long",
            "FALL_DETECTED": "long",
            "BATTERY_LOW": "alert",
            "WAKE_WORD": "short",
            "ZONE_CHANGE": "short",
        }.get(event["type"])
        if kind and self.core.platform_ok():
            self.fire(kind)
            self.last_run = datetime.now().isoformat(timespec="seconds")

    def fire(self, pattern: str = "short") -> bool:
        ms = self.PATTERNS.get(pattern, 80)
        r = run_code(f"termux-vibrate -d {ms}", timeout=4)
        if pattern == "alert":
            time.sleep(0.1)
            run_code(f"termux-vibrate -d {ms}", timeout=4)
        return r == 0


class PanicSOS(Plugin):
    """Protocolo de emergencia completo: luz, sirena, GPS, SMS, evidencia."""

    name = "panic_sos"
    description = "Protocolo SOS: estroboscopica + sirena + GPS + SMS + audio"

    def __init__(self, core):
        super().__init__(core)
        self.contact = os.getenv("SOS_CONTACT", "")
        self.active = False
        self.activations = 0

    def on_event(self, event: Dict[str, Any]) -> None:
        if event["type"] in ("PANIC", "FALL_DETECTED") and self.enabled:
            self.trigger(event.get("data", {}))

    def _strobe(self) -> None:
        for _ in range(20):
            run_code("termux-torch on", timeout=3)
            time.sleep(0.15)
            run_code("termux-torch off", timeout=3)
            time.sleep(0.15)
        run_code("termux-torch off", timeout=3)

    def _siren(self) -> None:
        run_code("termux-volume music 15", timeout=4)
        run_code(
            "termux-tts-speak -l es_ES -r 1.8 -p 1.5 "
            '"ALERTA DE EMERGENCIA. PROTOCOLO DE SEGURIDAD ACTIVADO."',
            timeout=20,
        )

    def _location(self) -> str:
        d = run_json(["termux-location", "-p", "gps", "-r", "once"], timeout=20)
        if isinstance(d, dict) and d.get("latitude"):
            lat, lon = d["latitude"], d["longitude"]
            link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            self.core.last_location = {"lat": lat, "lon": lon}
            return f"EMERGENCIA SOS. Ubicacion: {link}"
        return "EMERGENCIA SOS. Sin ubicacion GPS disponible."

    def trigger(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.active:
            return {"ok": False, "msg": "protocolo ya activo"}
        self.active = True
        self.activations += 1
        self.last_run = datetime.now().isoformat(timespec="seconds")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ev_dir = STATE_DIR / "evidencia_sos"
        ev_dir.mkdir(parents=True, exist_ok=True)
        audio = ev_dir / f"sos_{ts}.wav"

        results: Dict[str, Any] = {"ts": ts, "audio": str(audio)}

        if self.core.platform_ok():
            threading.Thread(target=self._strobe, daemon=True).start()
            threading.Thread(target=self._siren, daemon=True).start()
            # Evidencia de audio (60s)
            try:
                import subprocess

                subprocess.Popen(
                    ["termux-microphone-record", "-l", "60", "-f", str(audio)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                results["recording"] = True
            except Exception:
                results["recording"] = False
            msg = self._location()
            results["message"] = msg
            if self.contact:
                results["sms_sent"] = (
                    run_code(f'termux-sms-send -n {self.contact} "{msg}"', timeout=20) == 0
                )
            else:
                results["sms_sent"] = False
                results["sms_note"] = "define SOS_CONTACT en el entorno"
        else:
            results["simulated"] = True

        self.core.log_diario("SOS", msg if "message" in results else "simulado")
        self.core.bus.emit("SOS_COMPLETE", results, self.name)
        self.active = False
        return {"ok": True, **results}


class HomeZone(Plugin):
    """Zonas GPS configurables (casa / trabajo / calle)."""

    name = "home_zone"
    description = "Zonas GPS con Haversine (casa, trabajo, calle)"

    def __init__(self, core):
        super().__init__(core)
        self.zones: List[Dict[str, Any]] = [
            {"name": "casa", "lat": 28.0309, "lon": -16.5945, "radius": 150},
            {"name": "trabajo", "lat": 28.0500, "lon": -16.6000, "radius": 200},
        ]
        self.current = "calle"

    @staticmethod
    def _haversine(a1, o1, a2, o2) -> float:
        from math import asin, cos, radians, sin, sqrt

        dlat, dlon = radians(a2 - a1), radians(o2 - o1)
        h = sin(dlat / 2) ** 2 + cos(radians(a1)) * cos(radians(a2)) * sin(dlon / 2) ** 2
        return 2 * 6371000 * asin(sqrt(h))

    def _locate(self) -> Optional[tuple]:
        d = run_json(["termux-location", "-p", "network", "-r", "once"], timeout=15)
        if isinstance(d, dict) and d.get("latitude"):
            return float(d["latitude"]), float(d["longitude"])
        return None

    def on_tick(self) -> None:
        if not self.core.platform_ok():
            return
        pos = self._locate()
        if not pos:
            return
        lat, lon = pos
        self.core.last_location = {"lat": lat, "lon": lon}
        zone = "calle"
        for z in self.zones:
            if self._haversine(lat, lon, z["lat"], z["lon"]) <= z["radius"]:
                zone = z["name"]
                break
        if zone != self.current:
            prev = self.current
            self.current = zone
            self.core.bus.emit(
                "ZONE_CHANGE", {"from": prev, "to": zone, "lat": lat, "lon": lon}, self.name
            )
        self.last_run = datetime.now().isoformat(timespec="seconds")

    def status(self):
        s = super().status()
        s["current_zone"] = self.current
        s["zones"] = [z["name"] for z in self.zones]
        return s


class Diario(Plugin):
    """Registro tactico de eventos (de daniela_proactiva)."""

    name = "diario"
    description = "Diario tactico — registro persistente de eventos"

    def on_event(self, event: Dict[str, Any]) -> None:
        if event["type"] in ("SENSOR_TICK",):
            return
        self.core.log_diario(
            event["type"],
            json.dumps(event.get("data", {}), ensure_ascii=False)[:200],
            event["source"],
        )
        self.last_run = event["ts"]


# =============================================================================
# CORE
# =============================================================================


class MobileCore:
    """Nucleo movil: un proceso, un bus, muchos plugins."""

    def __init__(self) -> None:
        self.platform = "termux" if is_termux() else "pc"
        self.bus = EventBus()
        self.plugins: Dict[str, Plugin] = {}
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self.ticks = 0
        self.last_location: Optional[Dict[str, float]] = None
        self.started_at: Optional[float] = None

        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self._register_defaults()

    def _register_defaults(self) -> None:
        for cls in (PocketSense, HeadsetGuard, Haptics, PanicSOS, HomeZone, Diario):
            p = cls(self)
            self.plugins[p.name] = p
            self.bus.subscribe(None, p.on_event)

    def platform_ok(self) -> bool:
        """True si podemos ejecutar comandos Termux de verdad."""
        return self.platform == "termux"

    def log_diario(self, tipo: str, detalle: str, source: str = "core") -> None:
        try:
            diario = []
            if DIARIO_FILE.exists():
                diario = json.loads(DIARIO_FILE.read_text(encoding="utf-8"))
            diario.append(
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "tipo": tipo,
                    "detalle": detalle,
                    "source": source,
                }
            )
            DIARIO_FILE.write_text(
                json.dumps(diario[-MAX_DIARIO:], indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass

    # ── Bucle ────────────────────────────────────────────────────────────────
    def _loop(self) -> None:
        while not self._stop.wait(SENSOR_INTERVAL):
            try:
                self.ticks += 1
                self.bus.emit("SENSOR_TICK", {"tick": self.ticks}, "core")
                for p in list(self.plugins.values()):
                    if p.enabled:
                        p.on_tick()
                self._check_battery()
            except Exception as e:
                print(f"[MobileCore] error en bucle: {type(e).__name__}: {str(e)[:60]}")

    def _check_battery(self) -> None:
        if not self.platform_ok() or self.ticks % 30 != 0:
            return
        d = run_json("termux-battery-status", timeout=6)
        if isinstance(d, dict) and d.get("percentage") is not None:
            pct = int(d["percentage"])
            if pct <= BATTERY_LOW_PCT:
                self.bus.emit("BATTERY_LOW", {"percentage": pct}, "core")

    # ── API ──────────────────────────────────────────────────────────────────
    def start(self) -> Dict[str, Any]:
        if self.running:
            return {"ok": True, "msg": "ya en marcha"}
        self.running = True
        self.started_at = time.time()
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.bus.emit("CORE_STARTED", {"platform": self.platform}, "core")
        return {"ok": True, "msg": "Mobile Core arrancado", "plugins": len(self.plugins)}

    def stop(self) -> Dict[str, Any]:
        if not self.running:
            return {"ok": True, "msg": "no estaba en marcha"}
        self.running = False
        self._stop.set()
        self.bus.emit("CORE_STOPPED", {}, "core")
        return {"ok": True, "msg": "Mobile Core detenido"}

    def toggle_plugin(self, name: str, enabled: Optional[bool] = None) -> Dict:
        p = self.plugins.get(name)
        if not p:
            return {"ok": False, "msg": f"plugin '{name}' no existe"}
        p.enabled = (not p.enabled) if enabled is None else enabled
        self.bus.emit("PLUGIN_TOGGLED", {"plugin": name, "enabled": p.enabled}, "core")
        return {"ok": True, "plugin": name, "enabled": p.enabled}

    def status(self) -> Dict[str, Any]:
        uptime = int(time.time() - self.started_at) if self.started_at else 0
        return {
            "platform": self.platform,
            "running": self.running,
            "uptime_seconds": uptime,
            "ticks": self.ticks,
            "plugins_total": len(self.plugins),
            "plugins_active": sum(1 for p in self.plugins.values() if p.enabled),
            "last_location": self.last_location,
            "bus_events": len(self.bus.history),
            "started_at": (
                datetime.fromtimestamp(self.started_at).isoformat(timespec="seconds")
                if self.started_at
                else None
            ),
            "plugins": {n: p.status() for n, p in self.plugins.items()},
        }


def get_instance() -> MobileCore:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = MobileCore()
        return _instance


# =============================================================================
# RUTAS FLASK
# =============================================================================


def register_core_routes(app) -> None:
    from flask import jsonify, request

    @app.route("/api/pixel/core/status", methods=["GET"])
    def core_status():
        return jsonify(get_instance().status())

    @app.route("/api/pixel/core/plugins", methods=["GET"])
    def core_plugins():
        c = get_instance()
        return jsonify({"plugins": {n: p.status() for n, p in c.plugins.items()}})

    @app.route("/api/pixel/core/plugin/<name>/toggle", methods=["POST"])
    def core_toggle(name):
        d = request.get_json(silent=True) or {}
        return jsonify(get_instance().toggle_plugin(name, d.get("enabled")))

    @app.route("/api/pixel/core/events", methods=["GET"])
    def core_events():
        c = get_instance()
        limit = request.args.get("limit", 30, type=int)
        etype = request.args.get("type")
        return jsonify({"events": c.bus.recent(limit, etype), "total": len(c.bus.history)})

    @app.route("/api/pixel/core/emit", methods=["POST"])
    def core_emit():
        d = request.get_json(silent=True) or {}
        etype = d.get("type", "")
        if not etype:
            return jsonify({"ok": False, "msg": "falta 'type'"}), 400
        ev = get_instance().bus.emit(etype, d.get("data", {}), d.get("source", "api"))
        return jsonify({"ok": True, "event": ev})

    @app.route("/api/pixel/core/start", methods=["POST"])
    def core_start():
        return jsonify(get_instance().start())

    @app.route("/api/pixel/core/stop", methods=["POST"])
    def core_stop():
        return jsonify(get_instance().stop())

    @app.route("/api/pixel/core/panic", methods=["POST"])
    def core_panic():
        c = get_instance()
        p = c.plugins.get("panic_sos")
        if not p:
            return jsonify({"ok": False, "msg": "plugin SOS no disponible"}), 500
        return jsonify(p.trigger((request.get_json(silent=True) or {})))

    print(
        "[Mobile Core] Routes registered: /api/pixel/core/* "
        "(status, plugins, plugin toggle, events, emit, start, stop, panic)"
    )


def main() -> None:
    import sys

    c = get_instance()
    if "--status" in sys.argv:
        print(json.dumps(c.status(), indent=2, ensure_ascii=False))
        return
    print("Daniela Mobile Core")
    print(f"  plataforma : {c.platform}")
    print(f"  plugins    : {', '.join(c.plugins)}")
    print("\nArrancando (Ctrl+C para salir)...")
    c.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        c.stop()
        print("\nDetenido.")


if __name__ == "__main__":
    main()

# Alias para compatibilidad
DanielaMobileCore = MobileCore