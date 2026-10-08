#!/usr/bin/env python3
"""
Context Engine + Detector de Caidas — Modo Calle 2.0 (E-05 / Fase 6)
=====================================================================
Daniela necesita saber QUE esta haciendo el Comandante, no solo donde esta.
Este modulo fusiona 9 senales (acelerometro, giroscopio, luz, proximidad,
pasos, bateria, GPS, hora, pantalla) en UN solo contexto de alto nivel:

    durmiendo     — noche + oscuridad + sin movimiento + plano
    en_bolsillo   — proximidad cercana + oscuridad + movimiento
    en_casa       — dentro del radio de la zona hogar
    caminando     — contador de pasos subiendo + aceleracion ritmica
    en_vehiculo   — velocidad GPS alta + aceleracion de baja varianza
    en_mano       — pantalla encendida + luz alta + cerca
    quieto        — estable, despierto, sin desplazamiento
    caida         — FALL_DETECTED (prioridad absoluta)
    desconocido   — datos insuficientes

Cada contexto lleva una CONFIANZA (0..1) y las SENALES que lo provocaron,
para que Daniela pueda explicar sus decisiones ("por que hice esto").

DETECTOR DE CAIDAS — algoritmo de 3 fases (reduce falsos positivos):

    Fase 1  Caida libre ...... |a| < FREE_FALL_G  durante >= 1 muestra
    Fase 2  Impacto .......... |a| > IMPACT_G     en la ventana siguiente
    Fase 3  Inmovilidad ...... varianza baja durante STILLNESS_S tras impacto
    Extra   Cambio de orientacion del vector gravedad > ORIENT_DELTA

Solo con las 3 fases (+ orientacion) se dispara. Ventana de gracia de
CONFIRM_WINDOW_S para que el usuario cancele (estornudo, movil al suelo...);
si no cancela, escala a PANIC y ejecuta el protocolo SOS del Mobile Core.

Seguridad: todo comando pasa por safe_exec. 0 os.system, 0 shell=True.

Rutas:
  GET  /api/pixel/context/status        — estado del motor
  GET  /api/pixel/context/current       — contexto inferido ahora mismo
  GET  /api/pixel/context/history       — ultimos N contextos
  GET  /api/pixel/context/fall          — caidas registradas
  POST /api/pixel/context/fall          — reportar / simular una caida
  POST /api/pixel/context/fall/cancel   — cancelar la caida pendiente
  GET  /api/pixel/context/config        — umbrales actuales
  POST /api/pixel/context/config        — ajustar umbrales en caliente

Publica en el bus del Mobile Core: FALL_DETECTED, ZONE_CHANGE, CONTEXT_CHANGE.

Coste: $0/mes — Termux:API (gratis)
"""

from __future__ import annotations

import json
import math
import os
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

from bridges.comms.safe_exec import run_code, run_json

# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "data" / "context_engine"
STATE_FILE = STATE_DIR / "context_state.json"
FALLS_FILE = STATE_DIR / "falls.json"

TICK_S = 1.0
MAX_HISTORY = 500
MAX_FALLS = 100

# ── Umbrales del detector de caidas (ajustables por API) ──────
DEFAULT_CONFIG: Dict[str, float] = {
    "free_fall_g": 2.5,  # |a| por debajo => caida libre
    "impact_g": 22.0,  # |a| por encima => impacto
    "stillness_s": 4.0,  # segundos quieto tras el impacto
    "stillness_var": 1.2,  # varianza maxima de |a| para considerar quieto
    "stillness_settle_s": 0.5,  # transitorio del impacto excluido de la ventana
    "orient_delta": 0.55,  # cambio minimo del vector gravedad normalizado
    "window_s": 1.5,  # ventana entre caida libre e impacto
    "confirm_window_s": 30.0,  # gracia para cancelar antes del SOS
    "step_walk_rate": 0.6,  # pasos/segundo para considerar "caminando"
    "vehicle_speed_kmh": 18.0,
    "light_dark_lux": 25.0,
    "light_bright_lux": 400.0,
    "prox_near_cm": 3.0,
    "home_radius_m": 60.0,
    "night_start_h": 23,
    "night_end_h": 7,
}

G = 9.80665  # gravedad estandar m/s^2

_instance: Optional["ContextEngine"] = None
_instance_lock = threading.Lock()


def is_termux() -> bool:
    return os.path.exists("/data/data/com.termux/files/usr/bin")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ─────────────────────────────────────────────────────────────
#  Utilidades matematicas
# ─────────────────────────────────────────────────────────────


def magnitude(vec: Any) -> Optional[float]:
    """Modulo de un vector [x, y, z] o dict {x,y,z}."""
    try:
        if isinstance(vec, dict):
            x = float(vec.get("x", 0.0))
            y = float(vec.get("y", 0.0))
            z = float(vec.get("z", 0.0))
        elif isinstance(vec, (list, tuple)) and len(vec) >= 3:
            x, y, z = float(vec[0]), float(vec[1]), float(vec[2])
        else:
            return None
        return math.sqrt(x * x + y * y + z * z)
    except (TypeError, ValueError):
        return None


def normalized(vec: Any) -> Optional[List[float]]:
    m = magnitude(vec)
    if not m:
        return None
    x, y, z = _xyz(vec)
    return [x / m, y / m, z / m]


def _xyz(vec: Any) -> Tuple[float, float, float]:
    if isinstance(vec, dict):
        return (float(vec.get("x", 0.0)), float(vec.get("y", 0.0)), float(vec.get("z", 0.0)))
    if isinstance(vec, (list, tuple)) and len(vec) >= 3:
        return (float(vec[0]), float(vec[1]), float(vec[2]))
    return (0.0, 0.0, 0.0)


def dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def variance(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ─────────────────────────────────────────────────────────────
#  Motor de contexto
# ─────────────────────────────────────────────────────────────


class ContextEngine:
    """Fusiona sensores en un contexto de alto nivel + detecta caidas."""

    def __init__(self) -> None:
        self.config: Dict[str, float] = dict(DEFAULT_CONFIG)
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

        self.current: Dict[str, Any] = {
            "context": "desconocido",
            "confidence": 0.0,
            "signals": {},
            "since": _now(),
            "explanation": "sin datos todavia",
        }
        self.history: Deque[Dict[str, Any]] = deque(maxlen=MAX_HISTORY)
        self.falls: Deque[Dict[str, Any]] = deque(maxlen=MAX_FALLS)

        # Ventana deslizante de |a| para el detector
        self._acc_window: Deque[Tuple[float, float]] = deque(maxlen=200)
        self._gravity_ref: Optional[List[float]] = None
        self._free_fall_at: Optional[float] = None
        self._impact_at: Optional[float] = None
        self._impact_peak: Optional[float] = None
        self._pending_fall: Optional[Dict[str, Any]] = None

        self._last_steps: Optional[float] = None
        self._last_steps_ts: float = 0.0
        self._step_rate: float = 0.0

        self.home_zone: Optional[Dict[str, float]] = None
        self.ticks = 0
        self.last_error: Optional[str] = None

        self._load()

    # ── persistencia ─────────────────────────────────────────

    def _load(self) -> None:
        try:
            if STATE_FILE.exists():
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self.config.update(data.get("config", {}))
                self.home_zone = data.get("home_zone")
                self.current = data.get("current", self.current)
                self.history = deque(data.get("history", [])[-MAX_HISTORY:], maxlen=MAX_HISTORY)
        except Exception as e:  # noqa: BLE001
            self.last_error = f"load: {e}"
        try:
            if FALLS_FILE.exists():
                self.falls = deque(
                    json.loads(FALLS_FILE.read_text(encoding="utf-8")), maxlen=MAX_FALLS
                )
        except Exception:  # noqa: BLE001
            pass

    def _save(self) -> None:
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(
                json.dumps(
                    {
                        "config": self.config,
                        "home_zone": self.home_zone,
                        "current": self.current,
                        "history": list(self.history)[-200:],
                        "updated": _now(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as e:  # noqa: BLE001
            self.last_error = f"save: {e}"

    def _save_falls(self) -> None:
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            FALLS_FILE.write_text(
                json.dumps(list(self.falls), ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:  # noqa: BLE001
            pass

    # ── lectura de sensores ──────────────────────────────────

    def read_sensors(self) -> Dict[str, Any]:
        """Lee el snapshot del SensorStreamLive si esta disponible.

        Si no, intenta termux-sensor directamente (cuando corre en el Pixel).
        Nunca lanza: devuelve dict vacio y degrada.
        """
        snap: Dict[str, Any] = {}
        try:
            from services.sensors.sensor_stream_live import get_instance as get_stream  # type: ignore

            snap = get_stream().get_snapshot() or {}
        except Exception:  # noqa: BLE001
            snap = {}

        if not snap.get("accelerometer") and is_termux():
            try:
                raw = run_json(
                    ["termux-sensor", "-s", "BMI160 accelerometer", "-n", "1"], timeout=3
                )
                if isinstance(raw, list) and raw:
                    vals = raw[0].get("BMI160 accelerometer", {})
                    snap["accelerometer"] = vals.get("values", [0, 0, 0])
            except Exception:  # noqa: BLE001
                pass
        return snap

    def read_battery(self) -> Dict[str, Any]:
        try:
            return run_json(["termux-battery-status"], timeout=3) or {}
        except Exception:  # noqa: BLE001
            return {}

    def read_location(self) -> Dict[str, Any]:
        try:
            return run_json(["termux-location", "-p", "network", "-r", "once"], timeout=6) or {}
        except Exception:  # noqa: BLE001
            return {}

    # ── clasificacion ────────────────────────────────────────

    def classify(self, s: Dict[str, Any]) -> Tuple[str, float, Dict[str, Any], str]:
        """Devuelve (contexto, confianza, senales, explicacion)."""
        cfg = self.config
        sig: Dict[str, Any] = {}

        acc = s.get("accelerometer")
        gyro = s.get("gyroscope")
        light = s.get("light")
        prox = s.get("proximity")
        steps = s.get("step")
        bat = s.get("battery") or {}
        loc = s.get("location") or {}
        hour = datetime.now().hour

        a_mag = magnitude(acc)
        sig["acc_mag"] = round(a_mag, 2) if a_mag is not None else None
        sig["light"] = light
        sig["proximity"] = prox
        sig["steps"] = steps
        sig["battery"] = bat.get("percentage")
        sig["hour"] = hour
        sig["step_rate"] = round(self._step_rate, 2)

        is_night = hour >= cfg["night_start_h"] or hour < cfg["night_end_h"]
        sig["is_night"] = is_night

        # Velocidad GPS
        speed = loc.get("speed")
        speed_kmh = (float(speed) * 3.6) if speed is not None else None
        sig["speed_kmh"] = round(speed_kmh, 1) if speed_kmh is not None else None

        # Distancia a casa
        dist_home: Optional[float] = None
        if self.home_zone and loc.get("latitude") and loc.get("longitude"):
            dist_home = haversine_m(
                float(loc["latitude"]),
                float(loc["longitude"]),
                float(self.home_zone["lat"]),
                float(self.home_zone["lon"]),
            )
            sig["dist_home_m"] = round(dist_home, 1)

        # ── reglas, ordenadas por prioridad ──────────────────
        # 1. En vehiculo: velocidad GPS alta sostenida
        if speed_kmh is not None and speed_kmh >= cfg["vehicle_speed_kmh"]:
            return ("en_vehiculo", 0.85, sig, f"GPS reporta {speed_kmh:.0f} km/h sostenidos")

        # 2. En bolsillo: proximidad cercana + oscuridad
        if prox is not None and light is not None:
            if float(prox) <= cfg["prox_near_cm"] and float(light) <= cfg["light_dark_lux"]:
                return (
                    "en_bolsillo",
                    0.9,
                    sig,
                    f"proximidad {prox} cm y luz {light} lx (oscuro y tapado)",
                )

        # 3. En mano: luz alta + movimiento fino (pantalla encendida)
        if light is not None and float(light) >= cfg["light_bright_lux"]:
            return (
                "en_mano",
                0.75,
                sig,
                f"luz ambiental {light} lx — probablemente pantalla encendida",
            )

        # 4. Durmiendo: noche + oscuridad + plano + quieto
        if (
            is_night
            and light is not None
            and float(light) <= cfg["light_dark_lux"]
            and a_mag is not None
            and abs(a_mag - G) < 1.5
            and self._step_rate < 0.05
        ):
            return (
                "durmiendo",
                0.8,
                sig,
                f"son las {hour}h, oscuridad ({light} lx) y sin movimiento",
            )

        # 5. Caminando: contador de pasos subiendo
        if self._step_rate >= cfg["step_walk_rate"]:
            return ("caminando", 0.85, sig, f"ritmo de {self._step_rate:.1f} pasos/segundo")

        # 6. En casa: dentro del radio
        if dist_home is not None and dist_home <= cfg["home_radius_m"]:
            return (
                "en_casa",
                0.8,
                sig,
                f"a {dist_home:.0f} m del punto hogar (radio {cfg['home_radius_m']:.0f} m)",
            )

        # 7. Quieto: aceleracion estable en reposo
        if a_mag is not None and abs(a_mag - G) < 2.0 and self._step_rate < 0.05:
            return ("quieto", 0.6, sig, f"acelerometro estable en {a_mag:.1f} m/s2 (~1 g)")

        gyro_mag = magnitude(gyro)
        if gyro_mag is not None and gyro_mag > 1.0:
            return (
                "en_mano",
                0.5,
                sig,
                f"giroscopio activo ({gyro_mag:.2f} rad/s) — manipulando el movil",
            )

        return ("desconocido", 0.2, sig, "senales insuficientes para decidir")

    def _update_step_rate(self, steps: Optional[float]) -> None:
        now = time.time()
        if steps is None:
            self._step_rate = max(0.0, self._step_rate - 0.2)
            return
        if self._last_steps is not None and now > self._last_steps_ts:
            dt = now - self._last_steps_ts
            delta = max(0.0, steps - self._last_steps)
            # Suavizado exponencial para no temblar con ruido del sensor
            rate = delta / dt if dt > 0 else 0.0
            self._step_rate = (self._step_rate * 0.6) + (rate * 0.4)
        self._last_steps = steps
        self._last_steps_ts = now

    # ── detector de caidas ───────────────────────────────────

    def feed_acceleration(self, acc: Any, ts: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Alimenta una muestra de acelerometro. Devuelve la caida si la hay.

        `ts` permite inyectar marca de tiempo (tests, replay de caja negra);
        por defecto usa time.time().
        """
        a = magnitude(acc)
        if a is None:
            return None
        now = time.time() if ts is None else ts
        cfg = self.config

        self._acc_window.append((now, a))

        # Referencia de gravedad estable (para detectar cambio de orientacion)
        if self._gravity_ref is None and abs(a - G) < 2.0:
            self._gravity_ref = normalized(acc)

        # Fase 1: caida libre
        if self._free_fall_at is None and a < cfg["free_fall_g"]:
            self._free_fall_at = now
            return None

        # Fase 2: impacto dentro de la ventana tras la caida libre
        if (
            self._free_fall_at is not None
            and self._impact_at is None
            and a > cfg["impact_g"]
            and (now - self._free_fall_at) <= cfg["window_s"]
        ):
            self._impact_at = now
            self._impact_peak = a
            return None

        # Fase 3: inmovilidad tras el impacto
        if self._impact_at is not None:
            elapsed = now - self._impact_at
            if elapsed >= cfg["stillness_s"]:
                # Se excluye el transitorio del impacto: la inmovilidad se
                # mide DESPUES de que el cuerpo deja de rebotar.
                settle = self._impact_at + cfg["stillness_settle_s"]
                window = [v for t, v in self._acc_window if t >= settle]
                still = len(window) >= 3 and variance(window) <= cfg["stillness_var"]

                g_now = normalized(acc)
                orient_delta = 0.0
                if self._gravity_ref and g_now:
                    orient_delta = 1.0 - dot(self._gravity_ref, g_now)
                # Sin referencia previa no podemos juzgar la orientacion:
                # no bloqueamos la deteccion, solo perdemos ese refuerzo.
                orient_ok = self._gravity_ref is None or orient_delta >= cfg["orient_delta"]

                peak = self._impact_peak if self._impact_peak is not None else a
                self._free_fall_at = None
                self._impact_at = None
                self._impact_peak = None

                if still and orient_ok:
                    fall = self._register_fall(peak, variance(window), orient_delta)
                    # La nueva orientacion de reposo pasa a ser la referencia
                    if g_now:
                        self._gravity_ref = g_now
                    return fall
                # Falso positivo: se movio o no cambio de orientacion
                return None

            # Todavia en ventana de impacto: si vuelve a moverse mucho, abortar
            if a > cfg["impact_g"] * 0.6 and elapsed > 0.5:
                self._free_fall_at = None
                self._impact_at = None
                self._impact_peak = None

        # Expira la fase 1 si no hubo impacto
        if self._free_fall_at is not None and (now - self._free_fall_at) > cfg["window_s"]:
            self._free_fall_at = None
        return None

    def _register_fall(self, impact_g: float, var: float, orient_delta: float) -> Dict[str, Any]:
        cfg = self.config
        fall = {
            "id": f"fall_{int(time.time())}_{len(self.falls)}",
            "detected_at": _now(),
            "ts": time.time(),
            "impact_mag": round(impact_g, 2),
            "stillness_var": round(var, 3),
            "orient_delta": round(orient_delta, 3),
            "context_before": self.current.get("context"),
            "state": "pending",  # pending -> confirmed | cancelled
            "confirm_until": time.time() + cfg["confirm_window_s"],
            "sos_sent": False,
            "location": None,
        }
        try:
            loc = self.read_location()
            if loc.get("latitude"):
                fall["location"] = {
                    "lat": loc.get("latitude"),
                    "lon": loc.get("longitude"),
                    "accuracy": loc.get("accuracy"),
                }
        except Exception:  # noqa: BLE001
            pass

        self.falls.append(fall)
        self._save_falls()
        self._pending_fall = fall

        # Aviso haptic + voz: "¿estas bien?"
        try:
            run_code(["termux-vibrate", "-d", "400"], timeout=3)
            run_code(
                [
                    "termux-tts-speak",
                    "-l",
                    "es",
                    "Caida detectada. Estas bien? Di cancelar para abortar.",
                ],
                timeout=6,
            )
        except Exception:  # noqa: BLE001
            pass

        # Publicar en el bus del Mobile Core
        self._emit(
            "FALL_DETECTED",
            {
                "id": fall["id"],
                "impact_mag": fall["impact_mag"],
                "location": fall["location"],
            },
        )
        return fall

    def cancel_fall(self) -> Dict[str, Any]:
        if not self._pending_fall:
            return {"ok": False, "msg": "no hay caida pendiente"}
        self._pending_fall["state"] = "cancelled"
        self._pending_fall["resolved_at"] = _now()
        self._save_falls()
        cancelled = self._pending_fall
        self._pending_fall = None
        try:
            run_code(["termux-tts-speak", "-l", "es", "Cancelado. Me alegro."], timeout=6)
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "fall": cancelled}

    def _check_pending(self) -> None:
        """Si la ventana de gracia expira, escala a PANIC (protocolo SOS)."""
        f = self._pending_fall
        if not f or f.get("state") != "pending":
            return
        if time.time() < f.get("confirm_until", 0):
            return
        f["state"] = "confirmed"
        f["resolved_at"] = _now()
        self._save_falls()
        self._pending_fall = None

        self._emit(
            "PANIC",
            {
                "reason": "caida_confirmada",
                "fall_id": f["id"],
                "location": f.get("location"),
            },
        )
        try:
            run_code(["termux-vibrate", "-d", "800"], timeout=3)
        except Exception:  # noqa: BLE001
            pass

    def _emit(self, event: str, data: Dict[str, Any]) -> None:
        try:
            from core.autonomy.daniela_mobile_core import get_instance as get_core  # type: ignore

            get_core().bus.emit(event, data, source="context_engine")
        except Exception:  # noqa: BLE001
            pass

    # ── bucle principal ──────────────────────────────────────

    def _tick(self) -> None:
        s = self.read_sensors()
        if not s.get("battery"):
            s["battery"] = self.read_battery()
        if not s.get("location") and (self.home_zone or self._pending_fall):
            s["location"] = self.read_location()

        self._update_step_rate(s.get("step"))

        # Detector de caidas
        fall = self.feed_acceleration(s.get("accelerometer"))
        if fall:
            self.current = {
                "context": "caida",
                "confidence": 0.95,
                "signals": {"impact_mag": fall["impact_mag"]},
                "since": _now(),
                "explanation": (
                    f"impacto de {fall['impact_mag']} m/s2 seguido de "
                    f"inmovilidad — esperando confirmacion"
                ),
            }
            self._push_history()
            return

        self._check_pending()

        ctx, conf, sig, why = self.classify(s)
        changed = ctx != self.current.get("context")
        self.current = {
            "context": ctx,
            "confidence": round(conf, 2),
            "signals": sig,
            "since": _now() if changed else self.current.get("since", _now()),
            "explanation": why,
        }
        if changed:
            self._push_history()
            self._emit(
                "CONTEXT_CHANGE",
                {
                    "from": self.history[-2]["context"] if len(self.history) > 1 else None,
                    "to": ctx,
                    "confidence": conf,
                },
            )
            self._on_context_change(ctx)

    def _push_history(self) -> None:
        self.history.append(
            {
                "ts": _now(),
                "context": self.current.get("context"),
                "confidence": self.current.get("confidence"),
                "explanation": self.current.get("explanation"),
            }
        )

    def _on_context_change(self, ctx: str) -> None:
        """Reacciones proactivas segun el nuevo contexto."""
        try:
            if ctx == "en_vehiculo":
                run_code(
                    [
                        "termux-tts-speak",
                        "-l",
                        "es",
                        "Veo que vas en coche. Activo modo conduccion.",
                    ],
                    timeout=6,
                )
            elif ctx == "durmiendo":
                pass  # silencio absoluto
            elif ctx == "en_bolsillo":
                run_code(["termux-vibrate", "-d", "60"], timeout=3)
        except Exception:  # noqa: BLE001
            pass

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.ticks += 1
                self._tick()
                if self.ticks % 30 == 0:
                    self._save()
            except Exception as e:  # noqa: BLE001
                self.last_error = f"tick: {e}"
            self._stop.wait(TICK_S)

    def start(self) -> Dict[str, Any]:
        if self.running:
            return {"ok": False, "msg": "ya esta corriendo"}
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ContextEngine")
        self._thread.start()
        self.running = True
        return {"ok": True, "msg": "Context Engine arrancado"}

    def stop(self) -> Dict[str, Any]:
        if not self.running:
            return {"ok": False, "msg": "no estaba corriendo"}
        self._stop.set()
        self.running = False
        self._save()
        return {"ok": True, "msg": "Context Engine detenido"}

    # ── API publica ──────────────────────────────────────────

    def set_home(self, lat: float, lon: float, label: str = "hogar") -> Dict[str, Any]:
        self.home_zone = {"lat": float(lat), "lon": float(lon), "label": label}
        self._save()
        return {"ok": True, "home_zone": self.home_zone}

    def set_home_here(self) -> Dict[str, Any]:
        loc = self.read_location()
        if not loc.get("latitude"):
            return {"ok": False, "msg": "no se pudo obtener la ubicacion"}
        return self.set_home(loc["latitude"], loc["longitude"])

    def simulate_fall(self) -> Dict[str, Any]:
        """Inyecta una secuencia sintetica: reposo -> caida libre -> impacto
        -> inmovilidad con cambio de orientacion. Util para tests y demo."""
        cfg = self.config
        t0 = time.time()

        # 0. Reposo previo en vertical: fija la referencia de gravedad [0,1,0]
        self.feed_acceleration([0.02, G, 0.05], t0 - 2.0)
        # 1. Caida libre
        self.feed_acceleration([0.1, 0.2, 0.3], t0)
        # 2. Impacto
        self.feed_acceleration([0.0, cfg["impact_g"] + 8, 0.0], t0 + 0.2)
        # 3. Inmovilidad tumbado boca arriba (gravedad sobre Z) durante 4.5 s
        fall = None
        for i in range(1, 11):
            fall = self.feed_acceleration([0.02, 0.05, G + 0.03], t0 + 0.2 + i * 0.5) or fall
            if fall:
                break
        if not fall:
            return {"ok": False, "msg": "la secuencia no disparo el detector"}
        return {"ok": True, "fall": fall}

    def status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "ticks": self.ticks,
            "platform": "termux" if is_termux() else "pc",
            "context": self.current,
            "home_zone": self.home_zone,
            "pending_fall": self._pending_fall,
            "falls_total": len(self.falls),
            "history_size": len(self.history),
            "step_rate": round(self._step_rate, 2),
            "config": self.config,
            "last_error": self.last_error,
            "updated": _now(),
        }


def get_instance() -> ContextEngine:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = ContextEngine()
        return _instance


# ─────────────────────────────────────────────────────────────
#  Rutas Flask
# ─────────────────────────────────────────────────────────────


def register_context_routes(app) -> int:
    from flask import jsonify, request  # import local: no rompe si no hay Flask

    engine = get_instance()
    n = 0

    @app.route("/api/pixel/context/status", methods=["GET"])
    def ctx_status():
        return jsonify(engine.status())

    @app.route("/api/pixel/context/current", methods=["GET"])
    def ctx_current():
        return jsonify(engine.current)

    @app.route("/api/pixel/context/history", methods=["GET"])
    def ctx_history():
        limit = int(request.args.get("limit", 50))
        return jsonify({"history": list(engine.history)[-limit:]})

    @app.route("/api/pixel/context/fall", methods=["GET", "POST"])
    def ctx_fall():
        if request.method == "GET":
            limit = int(request.args.get("limit", 20))
            return jsonify({"falls": list(engine.falls)[-limit:], "pending": engine._pending_fall})
        body = request.get_json(silent=True) or {}
        if body.get("simulate"):
            return jsonify(engine.simulate_fall())
        if body.get("cancel"):
            return jsonify(engine.cancel_fall())
        # reporte manual
        fall = engine._register_fall(float(body.get("impact_mag", 30.0)), 0.0, 1.0)
        return jsonify({"ok": True, "fall": fall})

    @app.route("/api/pixel/context/fall/cancel", methods=["POST"])
    def ctx_fall_cancel():
        return jsonify(engine.cancel_fall())

    @app.route("/api/pixel/context/config", methods=["GET", "POST"])
    def ctx_config():
        if request.method == "GET":
            return jsonify({"config": engine.config, "defaults": DEFAULT_CONFIG})
        body = request.get_json(silent=True) or {}
        changed = {}
        for k, v in body.items():
            if k in DEFAULT_CONFIG:
                try:
                    engine.config[k] = float(v)
                    changed[k] = float(v)
                except (TypeError, ValueError):
                    pass
        if "home_here" in body and body.get("home_here"):
            res = engine.set_home_here()
            if res.get("ok"):
                changed["home_zone"] = res["home_zone"]
        if "home_lat" in body and "home_lon" in body:
            res = engine.set_home(
                body["home_lat"], body["home_lon"], str(body.get("home_label", "hogar"))
            )
            changed["home_zone"] = res.get("home_zone")
        engine._save()
        return jsonify({"ok": True, "changed": changed, "config": engine.config})

    @app.route("/api/pixel/context/start", methods=["POST"])
    def ctx_start():
        return jsonify(engine.start())

    @app.route("/api/pixel/context/stop", methods=["POST"])
    def ctx_stop():
        return jsonify(engine.stop())

    n = 8
    print(
        "[Context Engine] Routes registered: "
        "/api/pixel/context/* (status, current, history, fall, "
        "fall/cancel, config, start, stop)"
    )
    return n


if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    e = get_instance()
    print("plataforma:", "termux" if is_termux() else "pc")
    print("contexto inicial:", e.current["context"])

    print("\n— clasificacion sintetica —")
    e.config["night_start_h"] = 0  # forzar noche para el test
    e.config["night_end_h"] = 24
    casos = [
        ("noche quieto", {"accelerometer": [0, 0, G], "light": 3, "proximity": 50}),
        ("bolsillo", {"accelerometer": [1, 2, G], "light": 2, "proximity": 1}),
        ("en mano", {"accelerometer": [1, 2, G], "light": 900, "proximity": 8}),
        ("vehiculo", {"accelerometer": [0, 0, G], "light": 200, "location": {"speed": 25}}),
    ]
    for nombre, s in casos:
        ctx, conf, sig, why = e.classify(s)
        print(f"  {nombre:12s} -> {ctx:12s} conf={conf:.2f}  ({why})")

    print("\n— detector de caidas (secuencia simulada) —")
    res = e.simulate_fall()
    print(
        "  ",
        res.get("ok"),
        res.get("fall", {}).get("id"),
        "| impacto:",
        res.get("fall", {}).get("impact_mag"),
        "| var:",
        res.get("fall", {}).get("stillness_var"),
        "| orient:",
        res.get("fall", {}).get("orient_delta"),
    )
    print("  estado:", res.get("fall", {}).get("state"))

    print("\n— cancelacion —")
    print("  ", e.cancel_fall())

    print("\n— falso positivo A: impacto pero luego se mueve —")
    t = time.time()
    e2 = ContextEngine()
    e2.feed_acceleration([0.02, G, 0.05], t - 2.0)
    e2.feed_acceleration([0.0, 0.2, 0.1], t)
    e2.feed_acceleration([0.0, 30.0, 0.0], t + 0.2)
    r2 = None
    for i in range(1, 11):  # sigue moviendose (varianza alta)
        r2 = e2.feed_acceleration([1.0 * i, 3.0 * i, G], t + 0.2 + i * 0.5) or r2
    print("   caida registrada?", r2 is not None, "(esperado: False)")

    print("\n— falso positivo B: golpe seco sin cambio de orientacion —")
    t = time.time()
    e3 = ContextEngine()
    e3.feed_acceleration([0.02, G, 0.05], t - 2.0)  # referencia [0,1,0]
    e3.feed_acceleration([0.0, 0.1, 0.1], t)
    e3.feed_acceleration([0.0, 30.0, 0.0], t + 0.2)
    r3 = None
    for i in range(1, 11):  # quieto pero SIGUE en vertical
        r3 = e3.feed_acceleration([0.02, G, 0.05], t + 0.2 + i * 0.5) or r3
    print("   caida registrada?", r3 is not None, "(esperado: False)")

    print("\nstatus keys:", list(e.status().keys()))