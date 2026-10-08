#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
context_hub.py — E-21 · Daniela siempre encendida, el movil siempre durmiendo
=============================================================================

El problema real
----------------
El telefono llevaba **10 dias sin suspension profunda** por un `PARTIAL_WAKE_LOCK`
de Termux. Daniela seguia viva, pero la bateria (y la CPU a 77 C) pagaban la
cuenta. Mantener un daemon despierto es facil; mantenerlo despierto *solo cuando
toca* es el problema que este modulo resuelve.

La idea
-------
El wakelock deja de ser un interruptor fijo y pasa a ser una **decision
continua** tomada con cuatro senales:

    bateria        por debajo del umbral -> se suelta (o nunca se toma)
    temperatura    por encima del umbral -> se suelta (el calor dana la bateria)
    carga          enchufado             -> se puede mantener sin coste
    hora           horas de silencio     -> se suelta salvo emergencia

Y el trabajo periodico no se hace quemando CPU: se agenda con
`termux-job-scheduler`, que el sistema ejecuta en ventanas de mantenimiento
(aunque el proceso este muerto). Es la diferencia entre "estar despierto" y
"que te despierten cuando toca".

Degradacion honesta
-------------------
El verdadero Context Hub (el coprocesador de sensores de siempre-encendido) no
es accesible desde Termux: hace falta una app Android con `ContextHubManager`.
Lo que SI es accesible y resuelve el mismo problema es el **wakelock con
politica** + **job scheduling**, que es lo que este modulo implementa.
Cuando exista una app companion, el modulo la usara como sensor de bajo consumo;
mientras tanto, no bloquea nada.

Rutas
-----
    GET  /api/pixel/hub/status         estado, wakelock y ultima decision
    POST /api/pixel/hub/start          arranca el supervisor
    POST /api/pixel/hub/stop           lo para (y suelta el wakelock)
    POST /api/pixel/hub/config         umbrales en caliente
    POST /api/pixel/hub/wakelock       fuerza adquirir / soltar / auto
    POST /api/pixel/hub/policy         explica la decision actual
    POST /api/pixel/hub/emergency      ignora la politica durante N minutos
    GET  /api/pixel/hub/history        ultimas decisiones
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from datetime import datetime
from datetime import time as dtime
from pathlib import Path
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------
# Dependencias opcionales
# --------------------------------------------------------------------------
try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore


# --------------------------------------------------------------------------
# Constantes y politica por defecto
# --------------------------------------------------------------------------
# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "hub"
CONFIG_FILE = DATA_DIR / "config.json"
HISTORY_FILE = DATA_DIR / "history.json"

TICK_S = 60.0  # cada cuanto se reevalua la decision
MAX_HISTORY = 300

POLITICA_DEFAULT: Dict[str, Any] = {
    # Bateria
    "min_bateria": 25,  # por debajo -> soltar
    "min_bateria_cargando": 5,  # enchufado da igual casi todo
    # Temperatura (grados C)
    "max_temperatura": 42.0,
    # Horas de silencio (local del dispositivo)
    "silencio_inicio": "01:00",
    "silencio_fin": "07:00",
    # Comportamiento
    "respetar_silencio": True,
    "mantener_si_cargando": True,
    "usar_job_scheduler": True,
    # Ventana de la emergencia
    "emergencia_min": 15,
}


# ==========================================================================
#  Lectura del estado del dispositivo
# ==========================================================================
def _ejecutar(args: List[str], timeout: int = 8) -> Optional[str]:
    """Ejecuta sin shell. Devuelve la salida o None."""
    try:
        r = subprocess.run(list(args), capture_output=True, timeout=timeout, shell=False)
        if r.returncode != 0:
            return None
        return (r.stdout or b"").decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        return None


def leer_bateria() -> Dict[str, Any]:
    """Usa termux-battery-status y, si no esta, /sys/class/power_supply."""
    out = _ejecutar(["termux-battery-status"])
    if out:
        try:
            d = json.loads(out)
            return {
                "nivel": int(d.get("percentage", -1)),
                "cargando": str(d.get("status", "")).upper() in ("CHARGING", "FULL"),
                "temperatura": float(d.get("temperature", -1.0)),
                "salud": str(d.get("health", "")),
                "fuente": "termux-battery-status",
            }
        except (ValueError, TypeError):
            pass

    # Respaldo sin Termux:API
    base = Path("/sys/class/power_supply/battery")

    def _num(nombre: str) -> Optional[int]:
        try:
            return int((base / nombre).read_text().strip())
        except Exception:
            return None

    cap = _num("capacity")
    temp = _num("temp")
    return {
        "nivel": cap if cap is not None else -1,
        "cargando": False,
        "temperatura": round(temp / 10.0, 1) if temp is not None else -1.0,
        "salud": "desconocida",
        "fuente": "sysfs",
    }


def en_silencio(inicio: str, fin: str, ahora: Optional[datetime] = None) -> bool:
    """True si `ahora` cae dentro de la ventana de silencio (puede cruzar medianoche)."""
    try:
        h1, m1 = (int(x) for x in inicio.split(":")[:2])
        h2, m2 = (int(x) for x in fin.split(":")[:2])
    except (ValueError, AttributeError):
        return False
    a = ahora or datetime.now()
    t = dtime(a.hour, a.minute)
    t1, t2 = dtime(h1, m1), dtime(h2, m2)
    if t1 <= t2:
        return t1 <= t <= t2
    return t >= t1 or t <= t2  # cruza medianoche


# ==========================================================================
#  Supervisor
# ==========================================================================
class ContextHub:
    """Mantiene a Daniela viva sin mantener al movil despierto de mas."""

    def __init__(self) -> None:
        self.politica = dict(POLITICA_DEFAULT)
        self._lock = threading.RLock()
        self._hilo: Optional[threading.Thread] = None
        self.activo = False

        self.wakelock = "desconocido"  # adquirido | suelto | auto
        self.ultima_decision: Dict[str, Any] = {}
        self.historial: List[Dict[str, Any]] = []
        self.emergencia_hasta = 0.0
        self.bateria: Dict[str, Any] = {}
        self.estadisticas = {
            "ticks": 0,
            "adquisiciones": 0,
            "sueltas": 0,
            "segundos_con_wakelock": 0.0,
            "arrancado": time.time(),
        }
        self._wakelock_desde: Optional[float] = None

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._cargar()

    # ------------------------------------------------------- configuracion
    def configurar(self, **kv: Any) -> Dict[str, Any]:
        with self._lock:
            for k, v in kv.items():
                if k in self.politica and isinstance(v, type(self.politica[k])):
                    self.politica[k] = v
            self._guardar()
            return dict(self.politica)

    def _cargar(self) -> None:
        if not CONFIG_FILE.exists():
            return
        try:
            d = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                for k, v in d.items():
                    if k in self.politica:
                        self.politica[k] = v
        except Exception:
            pass

    def _guardar(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.politica, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(CONFIG_FILE)

    # ------------------------------------------------------------ decision
    def decidir(self, bateria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Evalua la politica y devuelve la decision con sus razones."""
        b = bateria or leer_bateria()
        self.bateria = b
        p = self.politica
        nivel = b.get("nivel", -1)
        temp = b.get("temperatura", -1.0)
        cargando = bool(b.get("cargando"))
        silencio = en_silencio(str(p["silencio_inicio"]), str(p["silencio_fin"]))
        emergencia = time.time() < self.emergencia_hasta

        mantener = True
        razones: List[str] = []

        if emergencia:
            razones.append("emergencia activa: se ignora la politica")
        else:
            if cargando and p["mantener_si_cargando"]:
                umbral = int(p["min_bateria_cargando"])
                razones.append(f"cargando (umbral rebajado a {umbral}%)")
            else:
                umbral = int(p["min_bateria"])
            if 0 <= nivel < umbral:
                mantener = False
                razones.append(f"bateria {nivel}% < {umbral}%")
            else:
                razones.append(f"bateria {nivel}% OK")

            if temp > float(p["max_temperatura"]):
                mantener = False
                razones.append(f"temperatura {temp} C > {p['max_temperatura']} C")
            elif temp > 0:
                razones.append(f"temperatura {temp} C OK")

            if silencio and p["respetar_silencio"]:
                mantener = False
                razones.append("horas de silencio")
            elif silencio:
                razones.append("silencio ignorado por politica")

        decision = {
            "t": time.time(),
            "mantener": mantener,
            "razones": razones,
            "bateria": nivel,
            "temperatura": temp,
            "cargando": cargando,
            "silencio": silencio,
            "emergencia": emergencia,
        }
        with self._lock:
            self.ultima_decision = decision
            self.historial.append(decision)
            self.historial = self.historial[-MAX_HISTORY:]
            self.estadisticas["ticks"] += 1
        return decision

    # ----------------------------------------------------------- wakelock
    def _aplicar(self, mantener: bool) -> None:
        """Lleva el estado real del wakelock a lo que dice la decision."""
        deseado = "adquirido" if mantener else "suelto"
        with self._lock:
            if self.wakelock == deseado:
                return
            cmd = "termux-wake-lock" if mantener else "termux-wake-unlock"
            r = _ejecutar([cmd])
            if r is None:
                # Sin Termux:API no hay wakelock que gestionar.
                self.wakelock = "no-disponible"
                return
            self.wakelock = deseado
            if mantener:
                self.estadisticas["adquisiciones"] += 1
                self._wakelock_desde = time.time()
            else:
                self.estadisticas["sueltas"] += 1
                if self._wakelock_desde:
                    self.estadisticas["segundos_con_wakelock"] += time.time() - self._wakelock_desde
                    self._wakelock_desde = None

    def forzar(self, modo: str) -> bool:
        """auto | adquirir | soltar."""
        if modo == "auto":
            d = self.decidir()
            self._aplicar(bool(d["mantener"]))
        elif modo == "adquirir":
            self._aplicar(True)
        elif modo == "soltar":
            self._aplicar(False)
        else:
            return False
        return True

    def emergencia(self, minutos: int) -> None:
        self.emergencia_hasta = time.time() + max(1, min(240, int(minutos))) * 60
        self._aplicar(True)

    # ------------------------------------------------------- job scheduler
    def programar(self, script: str, cada_min: int = 15) -> Dict[str, Any]:
        """Agenda trabajo periodico: el sistema lo ejecuta aunque el proceso muera.

        Es la alternativa de bajo consumo a mantener un hilo despierto.
        """
        if not self.politica.get("usar_job_scheduler", True):
            return {"ok": False, "error": "job scheduler desactivado por politica"}
        r = _ejecutar(
            ["termux-job-scheduler", "--script", script, "--period-ms", str(cada_min * 60_000)],
            timeout=10,
        )
        return {"ok": r is not None, "script": script, "cada_min": cada_min}

    # ------------------------------------------------------------ bucle
    def _bucle(self) -> None:
        while self.activo:
            try:
                d = self.decidir()
                self._aplicar(bool(d["mantener"]))
            except Exception:
                pass  # un fallo puntual no tumba el supervisor
            time.sleep(TICK_S)

    def start(self) -> bool:
        if self.activo:
            return True
        self.activo = True
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()
        return True

    def stop(self) -> bool:
        self.activo = False
        self._aplicar(False)  # nunca dejar el wakelock colgando
        return True

    # --------------------------------------------------------- informe
    def estado(self) -> Dict[str, Any]:
        with self._lock:
            segundos = self.estadisticas["segundos_con_wakelock"]
            if self._wakelock_desde:
                segundos += time.time() - self._wakelock_desde
            return {
                "activo": self.activo,
                "wakelock": self.wakelock,
                "bateria": self.bateria,
                "ultima_decision": self.ultima_decision,
                "emergencia_restante_s": max(0, int(self.emergencia_hasta - time.time())),
                "politica": dict(self.politica),
                "estadisticas": dict(self.estadisticas, segundos_con_wakelock=round(segundos, 1)),
                "historial": self.historial[-20:],
            }


# --------------------------------------------------------------------------
#  Singleton
# --------------------------------------------------------------------------
_instancia: Optional[ContextHub] = None


def get_instance() -> ContextHub:
    global _instancia
    if _instancia is None:
        _instancia = ContextHub()
    return _instancia


# --------------------------------------------------------------------------
#  Rutas Flask
# --------------------------------------------------------------------------
def register_hub_routes(app) -> None:
    if Flask is None:
        return

    def h() -> ContextHub:
        return get_instance()

    @app.route("/api/pixel/hub/status", methods=["GET"], endpoint="hub__status")
    def _status():
        return jsonify({"ok": True, "hub": h().estado()})

    @app.route("/api/pixel/hub/start", methods=["POST"], endpoint="hub__start")
    def _start():
        h().start()
        return jsonify({"ok": True, "activo": True})

    @app.route("/api/pixel/hub/stop", methods=["POST"], endpoint="hub__stop")
    def _stop():
        h().stop()
        return jsonify({"ok": True, "activo": False, "wakelock": "suelto"})

    @app.route("/api/pixel/hub/config", methods=["POST"], endpoint="hub__config")
    def _config():
        d = request.get_json(silent=True) or {}
        return jsonify({"ok": True, "politica": h().configurar(**d)})

    @app.route("/api/pixel/hub/wakelock", methods=["POST"], endpoint="hub__wakelock")
    def _wakelock():
        d = request.get_json(silent=True) or {}
        modo = str(d.get("modo", "auto")).lower()
        if not h().forzar(modo):
            return jsonify({"ok": False, "error": "modo invalido: auto|adquirir|soltar"}), 400
        return jsonify({"ok": True, "modo": modo, "wakelock": h().wakelock})

    @app.route("/api/pixel/hub/policy", methods=["POST"], endpoint="hub__policy")
    def _policy():
        return jsonify({"ok": True, "decision": h().decidir()})

    @app.route("/api/pixel/hub/emergency", methods=["POST"], endpoint="hub__emergency")
    def _emergency():
        d = request.get_json(silent=True) or {}
        h().emergencia(int(d.get("minutos", 15)))
        return jsonify({"ok": True, "emergencia_hasta": h().emergencia_hasta})

    @app.route("/api/pixel/hub/history", methods=["GET"], endpoint="hub__history")
    def _history():
        return jsonify({"ok": True, "historial": h().historial[-50:]})

    print(
        "[Context Hub] Routes registered: /api/pixel/hub/* "
        "(status, start, stop, config, wakelock, policy, emergency, history)"
    )


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo() -> None:
    print("=" * 68)
    print(" CONTEXT HUB (E-21) — Daniela viva, movil durmiendo")
    print("=" * 68)
    h = ContextHub()
    h.configurar(silencio_inicio="00:00", silencio_fin="23:59")
    h.configurar(respetar_silencio=False)

    print("\n-- bateria real --")
    b = leer_bateria()
    print("  ", b)

    print("\n-- matriz de decision (politica: min 25%, max 42 C) --")
    casos = [
        ("sano", {"nivel": 80, "temperatura": 30.0, "cargando": False}),
        ("bateria baja", {"nivel": 18, "temperatura": 30.0, "cargando": False}),
        ("caliente", {"nivel": 80, "temperatura": 45.0, "cargando": False}),
        ("enchufado", {"nivel": 80, "temperatura": 30.0, "cargando": True}),
        ("bajo y cargando", {"nivel": 3, "temperatura": 30.0, "cargando": True}),
    ]
    for nombre, bat in casos:
        d = h.decidir(bat)
        marca = "MANTENER" if d["mantener"] else "SOLTAR  "
        print(f"   {nombre:17s} -> {marca}   ({'; '.join(d['razones'])})")

    print("\n-- horas de silencio (01:00-07:00) --")
    for hh in (3, 12, 23):
        ahora = datetime.now().replace(hour=hh, minute=0)
        print(f"   {hh:02d}:00 -> en silencio: {en_silencio('01:00', '07:00', ahora)}")

    print("\n-- emergencia ignora la politica --")
    h.configurar(respetar_silencio=True, silencio_inicio="00:00", silencio_fin="23:59")
    print(
        "   antes  :",
        (
            "MANTENER"
            if h.decidir({"nivel": 80, "temperatura": 30.0, "cargando": False})["mantener"]
            else "SOLTAR"
        ),
    )
    h.emergencia(15)
    print(
        "   despues:",
        (
            "MANTENER"
            if h.decidir({"nivel": 80, "temperatura": 30.0, "cargando": False})["mantener"]
            else "SOLTAR"
        ),
    )
    print("=" * 68)


if __name__ == "__main__":
    _demo()