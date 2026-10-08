#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
health_monitor.py — E-17 · Salud del nodo: los signos vitales del Pixel
======================================================================

La auditoria profunda del telefono encontro algo que ningun modulo sabia ver:
el movil estaba **enfermo** y nadie lo habia notado.

    swap al 98,5 %  (3.728 de 3.786 MB)   → thrashing, todo va a disco
    332 MB libres de 7.573 MB             → el sistema al borde
    wakelock `termux:service-wakelock`    → **10 dias 20 horas** sin soltar
    CPU LITTLE a 77 °C                    → thermal throttling
    com.android.vending al 59 % CPU       → Play Store comiendose la bateria

Cada uno de esos numeros por separado es "un dato". Juntos son un diagnostico.
Y lo importante: **ninguno fue un fallo repentino**. Fueron semanas de
degradacion lenta que se podian haber visto venir.

Este modulo es el que mira. Toma los signos vitales del nodo (RAM, swap,
bateria, temperatura, disco y wakelock), los convierte en una **puntuacion
con explicacion** y emite alertas cuando algo se sale de rango.

Diseno: sensores opcionales, nunca falla
----------------------------------------
Un movil, un portatil y un contenedor no exponen las mismas cosas. Por eso
cada senal es una funcion que devuelve ``None`` si no sabe medir, y la
puntuacion se calcula **solo con las senales disponibles**:

    cobertura: 4 de 6 sensores

En un PC de desarrollo sin Termux la cobertura sera baja, pero el modulo
arranca, responde y la demo pasa. En el Pixel dara el diagnostico completo.

Lo que este modulo NO hace
--------------------------
No mata procesos, no suelta wakelocks, no borra caches. Sugiere, no ejecuta.
Apagar algo en el telefono de una persona es una decision suya: un "Play Store
al 59 %" puede ser una descarga legitima. Ver `AUDITORIA_TELEFONO_PROFUNDA.md`.

Rutas
-----
    GET  /api/pixel/vitals/status    puntuacion, veredicto y resumen
    GET  /api/pixel/vitals/metrics   metricas crudas y cobertura
    GET  /api/pixel/vitals/history   serie temporal
    GET  /api/pixel/vitals/alerts    alertas activas con sugerencia
    POST /api/pixel/vitals/scan      fuerza un escaneo ahora
    POST /api/pixel/vitals/config    umbrales y muestreo
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore


# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "vitals"
CONFIG_FILE = DATA_DIR / "config.json"
HISTORY_FILE = DATA_DIR / "history.json"

# Cuantas muestras guardamos. A 60 s son ~12 h de historia; suficiente para
# ver una degradacion lenta sin llenar el disco del movil.
MAX_MUESTRAS = 720

CONFIG_DEFAULT: Dict[str, Any] = {
    "intervalo_s": 60.0,  # cada cuanto se toma una muestra
    "autoscan": True,  # hilo de fondo
    "swap_critico": 90.0,  # % de swap usado a partir del cual es critico
    "swap_aviso": 70.0,
    "ram_min_mb": 400.0,  # por debajo, aviso
    "temp_aviso_c": 60.0,
    "temp_critica_c": 75.0,
    "bateria_baja": 20.0,
    "bateria_critica": 8.0,
    "disco_min_pct": 10.0,  # % libre por debajo del cual avisa
    "wakelock_aviso_h": 6.0,  # horas que un wakelock lleva pidiendo atencion
    "wakelock_critico_h": 24.0,
}


# ==========================================================================
#  Utilidades de ejecucion — REGLA DURA: sin shell, sin os.system
# ==========================================================================
def _run(args: List[str], timeout: int = 12) -> Optional[str]:
    """Ejecuta una lista de argumentos. `shell=False` siempre, por diseno."""
    try:
        r = subprocess.run(list(args), capture_output=True, timeout=timeout, shell=False)
        if r.returncode != 0:
            return None
        return (r.stdout or b"").decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        return None


def es_android() -> bool:
    """`cmd` existe en Android (service tool) y en Windows (cmd.exe).

    En Windows devolveria 0 y una banner de Microsoft: un falso positivo que
    haria creer al modulo que esta leyendo sensores de un movil.
    """
    for ruta in ("/system/bin/app_process", "/system/build.prop", "/data/data/com.termux"):
        if Path(ruta).exists():
            return True
    return False


# ==========================================================================
#  Sensores — cada uno devuelve None si no sabe medir
# ==========================================================================
def _meminfo() -> Dict[str, float]:
    """Lee /proc/meminfo. Devuelve MB. Vacio si no existe (p. ej. Windows)."""
    try:
        txt = Path("/proc/meminfo").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    out: Dict[str, float] = {}
    for linea in txt.splitlines():
        if ":" not in linea:
            continue
        k, _, v = linea.partition(":")
        try:
            out[k.strip()] = float(v.split()[0]) / 1024.0  # kB -> MB
        except (ValueError, IndexError):
            continue
    return out


def sensor_ram_libre_mb() -> Optional[float]:
    m = _meminfo()
    if not m:
        return None
    # MemAvailable es la que importa: MemFree sola ignora la cache recuperable
    # y hace parecer que queda menos memoria de la que realmente hay.
    if "MemAvailable" in m:
        return round(m["MemAvailable"], 1)
    if "MemTotal" in m and "MemFree" in m:
        return round(m["MemFree"], 1)
    return None


def sensor_ram_total_mb() -> Optional[float]:
    m = _meminfo()
    return round(m["MemTotal"], 1) if "MemTotal" in m else None


def sensor_swap_pct() -> Optional[float]:
    m = _meminfo()
    total = m.get("SwapTotal")
    if not total:  # sin swap configurado: no es un problema
        return 0.0
    libre = m.get("SwapFree", total)
    return round(max(0.0, min(100.0, (total - libre) / total * 100.0)), 1)


def sensor_disco_libre_pct(ruta: str = "/") -> Optional[float]:
    try:
        u = shutil.disk_usage(ruta)
    except OSError:
        return None
    if u.total <= 0:
        return None
    return round(u.free / u.total * 100.0, 1)


def sensor_bateria_pct() -> Optional[float]:
    """`dumpsys battery` es la unica fuente fiable sin root en Android."""
    if not es_android():
        return None
    out = _run(["dumpsys", "battery"])
    if not out:
        return None
    for linea in out.splitlines():
        if "level" in linea and ":" in linea:
            try:
                return float(linea.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def sensor_temp_c() -> Optional[float]:
    """Maxima de las zonas termicas. Algunos kernels dan miligrados."""
    zonas = (
        sorted(Path("/sys/class/thermal").glob("thermal_zone*/temp"))
        if Path("/sys/class/thermal").exists()
        else []
    )
    mejor: Optional[float] = None
    for z in zonas:
        try:
            v = float(z.read_text(encoding="utf-8", errors="replace").strip())
        except (OSError, ValueError):
            continue
        if v > 1000:  # miligrados -> grados
            v /= 1000.0
        if v > 200:  # lectura absurda, ignorar
            continue
        mejor = v if mejor is None else max(mejor, v)
    return round(mejor, 1) if mejor is not None else None


def sensor_wakelock_h() -> Optional[float]:
    """Horas que lleva pedido el wakelock mas antiguo.

    Es la senal que delata al daemon que se olvido de soltar: en la auditoria
    salio **10 dias 20 horas**, y era la causa real del calor y del gasto.
    """
    if not es_android():
        return None
    out = _run(["dumpsys", "power"])
    if not out:
        return None
    peor = 0.0
    # El formato real incluye marcas tipo "(+1d2h3m4s)" o "(+3h12m)".
    for m in re.finditer(r"\(([+-]?)(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?", out):
        signo, d, h, mi = m.group(1), m.group(2), m.group(3), m.group(4)
        if signo == "-":
            continue
        seg = (int(d or 0) * 86400) + (int(h or 0) * 3600) + (int(mi or 0) * 60)
        peor = max(peor, seg / 3600.0)
    return round(peor, 2) if peor > 0 else 0.0


SENSORES: Dict[str, Callable[[], Optional[float]]] = {
    "ram_libre_mb": sensor_ram_libre_mb,
    "swap_pct": sensor_swap_pct,
    "disco_libre_pct": sensor_disco_libre_pct,
    "bateria_pct": sensor_bateria_pct,
    "temp_c": sensor_temp_c,
    "wakelock_h": sensor_wakelock_h,
}


# ==========================================================================
#  Puntuacion y alertas
# ==========================================================================
def _escala(valor: float, bueno: float, malo: float) -> float:
    """De 'bueno' (100 puntos) a 'malo' (0 puntos), lineal y acotado.

    `bueno` puede ser menor que `malo` (mas RAM libre = mejor) o al reves.
    """
    if bueno == malo:
        return 100.0
    x = (valor - malo) / (bueno - malo)
    return max(0.0, min(100.0, x * 100.0))


class MonitorSalud:
    """Toma muestras, puntua y explica. Nunca ejecuta acciones correctoras."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config: Dict[str, Any] = dict(CONFIG_DEFAULT)
        self._lock = threading.RLock()
        self._hilo: Optional[threading.Thread] = None
        self._parar = threading.Event()
        self.ultima: Optional[Dict[str, Any]] = None
        self.historia: List[Dict[str, Any]] = []
        self.alertas: List[Dict[str, Any]] = []
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.cargar()
        if config:
            self.config.update({k: v for k, v in config.items() if k in CONFIG_DEFAULT})

    # ------------------------------------------------------------------ IO
    def cargar(self) -> None:
        try:
            if CONFIG_FILE.exists():
                d = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    self.config.update({k: v for k, v in d.items() if k in CONFIG_DEFAULT})
        except (OSError, ValueError):
            pass
        try:
            if HISTORY_FILE.exists():
                h = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                if isinstance(h, list):
                    self.historia = h[-MAX_MUESTRAS:]
        except (OSError, ValueError):
            pass

    def guardar(self) -> None:
        try:
            CONFIG_FILE.write_text(
                json.dumps(self.config, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            HISTORY_FILE.write_text(
                json.dumps(self.historia[-MAX_MUESTRAS:], ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass

    # --------------------------------------------------------------- muestreo
    def medir(self) -> Dict[str, Any]:
        """Lee todos los sensores. Los que no responden salen como None."""
        m: Dict[str, Optional[float]] = {}
        for nombre, fn in SENSORES.items():
            try:
                m[nombre] = fn()
            except Exception:  # un sensor roto no tumba el muestreo
                m[nombre] = None
        m["ram_total_mb"] = sensor_ram_total_mb()
        return m

    def evaluar(self, m: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convierte metricas en puntuacion, veredicto y alertas."""
        c = self.config
        m = m if m is not None else self.medir()

        notas: List[Dict[str, Any]] = []
        alertas: List[Dict[str, Any]] = []

        def nota(sensor: str, puntos: float, peso: float, detalle: str) -> None:
            notas.append(
                {"sensor": sensor, "puntos": round(puntos, 1), "peso": peso, "detalle": detalle}
            )

        # --- RAM libre -----------------------------------------------------
        ram = m.get("ram_libre_mb")
        if ram is not None:
            puntos = _escala(ram, max(c["ram_min_mb"] * 3, 1500.0), 0.0)
            nota("ram_libre_mb", puntos, 2.0, f"{ram:.0f} MB libres")
            if ram < c["ram_min_mb"]:
                alertas.append(
                    {
                        "id": "ram_baja",
                        "severidad": "critico" if ram < c["ram_min_mb"] / 2 else "aviso",
                        "titulo": "Memoria RAM baja",
                        "detalle": f"{ram:.0f} MB libres (umbral {c['ram_min_mb']:.0f})",
                        "sugerencia": "Cierra apps en segundo plano o revisa el swap.",
                    }
                )

        # --- Swap ----------------------------------------------------------
        swap = m.get("swap_pct")
        if swap is not None:
            puntos = _escala(swap, 0.0, 100.0)
            nota("swap_pct", puntos, 2.0, f"swap usado {swap:.1f} %")
            if swap >= c["swap_critico"]:
                alertas.append(
                    {
                        "id": "swap_critico",
                        "severidad": "critico",
                        "titulo": "Swap casi lleno — el sistema va a disco",
                        "detalle": f"{swap:.1f} % usado",
                        "sugerencia": "Reduce procesos en memoria; el thrashing "
                        "calienta el telefono y gasta bateria.",
                    }
                )
            elif swap >= c["swap_aviso"]:
                alertas.append(
                    {
                        "id": "swap_alto",
                        "severidad": "aviso",
                        "titulo": "Swap alto",
                        "detalle": f"{swap:.1f} % usado",
                        "sugerencia": "Vigilalo: suele ir a mas.",
                    }
                )

        # --- Disco ---------------------------------------------------------
        disco = m.get("disco_libre_pct")
        if disco is not None:
            puntos = _escala(disco, 30.0, 0.0)
            nota("disco_libre_pct", puntos, 1.0, f"{disco:.1f} % libre")
            if disco < c["disco_min_pct"]:
                alertas.append(
                    {
                        "id": "disco_lleno",
                        "severidad": "critico",
                        "titulo": "Disco casi lleno",
                        "detalle": f"{disco:.1f} % libre",
                        "sugerencia": "Limpia caches y videos generados.",
                    }
                )

        # --- Bateria -------------------------------------------------------
        bat = m.get("bateria_pct")
        if bat is not None:
            puntos = _escala(bat, 60.0, 0.0)
            nota("bateria_pct", puntos, 1.5, f"{bat:.0f} % bateria")
            if bat <= c["bateria_critica"]:
                alertas.append(
                    {
                        "id": "bateria_critica",
                        "severidad": "critico",
                        "titulo": "Bateria critica",
                        "detalle": f"{bat:.0f} %",
                        "sugerencia": "Baja la frecuencia de muestreo o carga ya.",
                    }
                )
            elif bat <= c["bateria_baja"]:
                alertas.append(
                    {
                        "id": "bateria_baja",
                        "severidad": "aviso",
                        "titulo": "Bateria baja",
                        "detalle": f"{bat:.0f} %",
                        "sugerencia": "Reduce muestreo y brillo.",
                    }
                )

        # --- Temperatura ---------------------------------------------------
        temp = m.get("temp_c")
        if temp is not None:
            puntos = _escala(temp, 35.0, c["temp_critica_c"])
            nota("temp_c", puntos, 1.5, f"{temp:.1f} \u00b0C")
            if temp >= c["temp_critica_c"]:
                alertas.append(
                    {
                        "id": "temperatura_critica",
                        "severidad": "critico",
                        "titulo": "Temperatura critica",
                        "detalle": f"{temp:.1f} \u00b0C",
                        "sugerencia": "Thermal throttling: el movil se frena solo. "
                        "Suelta wakelocks y deja de cargar.",
                    }
                )
            elif temp >= c["temp_aviso_c"]:
                alertas.append(
                    {
                        "id": "temperatura_alta",
                        "severidad": "aviso",
                        "titulo": "Temperatura alta",
                        "detalle": f"{temp:.1f} \u00b0C",
                        "sugerencia": "Revisa wakelocks y procesos al 100 % CPU.",
                    }
                )

        # --- Wakelock ------------------------------------------------------
        wl = m.get("wakelock_h")
        if wl is not None:
            puntos = _escala(wl, 0.0, c["wakelock_critico_h"])
            nota("wakelock_h", puntos, 1.5, f"wakelock {wl:.1f} h")
            if wl >= c["wakelock_critico_h"]:
                alertas.append(
                    {
                        "id": "wakelock_atascado",
                        "severidad": "critico",
                        "titulo": "Wakelock sin soltar",
                        "detalle": f"{wl:.1f} horas seguidas",
                        "sugerencia": "Algun proceso no libera el wake-lock: asi el "
                        "telefono nunca entra en suspension profunda.",
                    }
                )
            elif wl >= c["wakelock_aviso_h"]:
                alertas.append(
                    {
                        "id": "wakelock_largo",
                        "severidad": "aviso",
                        "titulo": "Wakelock prolongado",
                        "detalle": f"{wl:.1f} horas",
                        "sugerencia": "Comprueba que el daemon lo suelta al terminar.",
                    }
                )

        # --- Puntuacion ----------------------------------------------------
        if notas:
            total_peso = sum(n["peso"] for n in notas)
            puntos = sum(n["puntos"] * n["peso"] for n in notas) / total_peso
        else:
            puntos = 0.0
            alertas.append(
                {
                    "id": "sin_sensores",
                    "severidad": "aviso",
                    "titulo": "Ningun sensor disponible",
                    "detalle": "No se pudo leer ninguna senal del sistema",
                    "sugerencia": "En PC es normal: las senales de bateria, "
                    "temperatura y wakelock solo existen en Android.",
                }
            )

        # El peor sensor limita la nota global: una media taparia un critico.
        peor = min((n["puntos"] for n in notas), default=0.0)
        if peor <= 20.0:
            puntos = min(puntos, 45.0)

        disponibles = [k for k, v in m.items() if v is not None and k in SENSORES]

        # Una nota de 100 con dos sensores no significa nada: en un PC sin
        # Termux solo responden swap y disco, y saldria "excelente" por pura
        # falta de datos. Por debajo de la mitad no nos creemos la nota.
        confiable = len(disponibles) >= (len(SENSORES) + 1) // 2
        if not confiable and disponibles:
            alertas.append(
                {
                    "id": "cobertura_baja",
                    "severidad": "info",
                    "titulo": "Pocos sensores disponibles",
                    "detalle": f"solo {len(disponibles)} de {len(SENSORES)}",
                    "sugerencia": "La puntuacion es orientativa: bateria, "
                    "temperatura y wakelock solo existen en Android.",
                }
            )

        if any(a["severidad"] == "critico" for a in alertas):
            veredicto = "critico"
        elif not confiable:
            veredicto = "parcial"
        elif puntos >= 80:
            veredicto = "excelente"
        elif puntos >= 60:
            veredicto = "bueno"
        elif puntos >= 40:
            veredicto = "regular"
        else:
            veredicto = "malo"

        return {
            "ok": True,
            "puntuacion": round(puntos, 1),
            "veredicto": veredicto,
            "confiable": confiable,
            "metricas": m,
            "cobertura": f"{len(disponibles)} de {len(SENSORES)} sensores",
            "sensores_disponibles": disponibles,
            "notas": notas,
            "alertas": alertas,
            "ts": time.time(),
        }

    def escanear(self) -> Dict[str, Any]:
        with self._lock:
            res = self.evaluar()
            self.ultima = res
            self.alertas = res["alertas"]
            self.historia.append(
                {
                    "ts": res["ts"],
                    "puntuacion": res["puntuacion"],
                    "veredicto": res["veredicto"],
                    "swap_pct": res["metricas"].get("swap_pct"),
                    "ram_libre_mb": res["metricas"].get("ram_libre_mb"),
                    "temp_c": res["metricas"].get("temp_c"),
                    "bateria_pct": res["metricas"].get("bateria_pct"),
                }
            )
            if len(self.historia) > MAX_MUESTRAS:
                self.historia = self.historia[-MAX_MUESTRAS:]
            if len(self.historia) % 10 == 0:
                self.guardar()
            return res

    # ------------------------------------------------------------------ hilo
    def iniciar(self) -> Dict[str, Any]:
        with self._lock:
            if self._hilo and self._hilo.is_alive():
                return {"ok": True, "ya_activo": True}
            self._parar.clear()
            self._hilo = threading.Thread(target=self._bucle, daemon=True)
            self._hilo.start()
            return {"ok": True, "intervalo_s": self.config["intervalo_s"]}

    def detener(self) -> Dict[str, Any]:
        self._parar.set()
        with self._lock:
            self.guardar()
        return {"ok": True}

    def _bucle(self) -> None:
        while not self._parar.wait(self.config["intervalo_s"]):
            try:
                self.escanear()
            except Exception:
                pass

    def estado(self) -> Dict[str, Any]:
        with self._lock:
            res = self.ultima or self.evaluar()
            return {
                **res,
                "autoscan": bool(self._hilo and self._hilo.is_alive()),
                "muestras": len(self.historia),
                "config": dict(self.config),
            }

    def configurar(self, **kv: Any) -> Dict[str, Any]:
        with self._lock:
            for k, v in kv.items():
                if k in CONFIG_DEFAULT and v is not None:
                    self.config[k] = v
        self.guardar()
        return dict(self.config)


# ==========================================================================
#  Singleton
# ==========================================================================
_INSTANCIA: Optional[MonitorSalud] = None
_LOCK = threading.Lock()


def get_instance() -> MonitorSalud:
    global _INSTANCIA
    with _LOCK:
        if _INSTANCIA is None:
            _INSTANCIA = MonitorSalud()
        return _INSTANCIA


# ==========================================================================
#  Rutas Flask
# ==========================================================================
def register_vitals_routes(app) -> None:
    if Flask is None:
        return

    def m() -> MonitorSalud:
        return get_instance()

    @app.route("/api/pixel/vitals/status", methods=["GET"], endpoint="vitals__status")
    def _status():
        return jsonify(m().estado())

    @app.route("/api/pixel/vitals/metrics", methods=["GET"], endpoint="vitals__metrics")
    def _metrics():
        return jsonify({"ok": True, "metricas": m().medir()})

    @app.route("/api/pixel/vitals/history", methods=["GET"], endpoint="vitals__history")
    def _history():
        try:
            n = int(request.args.get("n", 60))
        except (TypeError, ValueError):
            n = 60
        with m()._lock:  # noqa: SLF001
            return jsonify({"ok": True, "muestras": m().historia[-max(1, n) :]})

    @app.route("/api/pixel/vitals/alerts", methods=["GET"], endpoint="vitals__alerts")
    def _alerts():
        with m()._lock:  # noqa: SLF001
            return jsonify({"ok": True, "alertas": m().alertas})

    @app.route("/api/pixel/vitals/scan", methods=["POST"], endpoint="vitals__scan")
    def _scan():
        return jsonify(m().escanear())

    @app.route("/api/pixel/vitals/config", methods=["POST"], endpoint="vitals__config")
    def _config():
        d = request.get_json(silent=True) or {}
        if d.get("autoscan") is True:
            m().iniciar()
        elif d.get("autoscan") is False:
            m().detener()
        return jsonify({"ok": True, "config": m().configurar(**d)})

    print(
        "[Health Monitor] Routes registered: /api/pixel/vitals/* "
        "(status, metrics, history, alerts, scan, config)"
    )


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo() -> None:
    print("=" * 68)
    print(" HEALTH MONITOR (E-17) — signos vitales del nodo")
    print("=" * 68)

    print("es android  :", es_android())
    print("sensores    :", ", ".join(SENSORES))

    mon = MonitorSalud()
    metricas = mon.medir()
    print("\n-- metricas crudas --")
    for k, v in metricas.items():
        print(f"   {k:<18} {v}")

    res = mon.evaluar(metricas)
    print("\n-- evaluacion --")
    print("   cobertura  :", res["cobertura"])
    print("   puntuacion :", res["puntuacion"])
    print("   veredicto  :", res["veredicto"])
    print("   confiable  :", res["confiable"])
    print("   sensores   :", ", ".join(res["sensores_disponibles"]) or "ninguno")
    for n in res["notas"]:
        print(f"     - {n['sensor']:<18} {n['puntos']:>5.1f}  {n['detalle']}")

    print("\n-- alertas --")
    if not res["alertas"]:
        print("   ninguna")
    for a in res["alertas"]:
        print(f"   [{a['severidad']:<7}] {a['titulo']} — {a['detalle']}")
        print(f"              -> {a['sugerencia']}")

    print("\n-- caso sintetico: el telefono de la auditoria --")
    # Estos son los numeros REALES que salieron en AUDITORIA_TELEFONO_PROFUNDA
    enfermo = {
        "ram_libre_mb": 332.0,
        "swap_pct": 98.5,
        "disco_libre_pct": 42.0,
        "bateria_pct": 92.0,
        "temp_c": 77.0,
        "wakelock_h": 260.0,  # 10 d 20 h
        "ram_total_mb": 7573.0,
    }
    r2 = mon.evaluar(enfermo)
    print("   puntuacion :", r2["puntuacion"])
    print("   veredicto  :", r2["veredicto"])
    for a in r2["alertas"]:
        print(f"   [{a['severidad']:<7}] {a['titulo']} — {a['detalle']}")

    criticos = [a for a in r2["alertas"] if a["severidad"] == "critico"]
    print("\n   alertas criticas detectadas:", len(criticos))
    print("   diagnostica thrashing     :", any(a["id"] == "swap_critico" for a in criticos))
    print("   detecta wakelock atascado :", any(a["id"] == "wakelock_atascado" for a in criticos))
    print("   detecta temperatura       :", any(a["id"] == "temperatura_critica" for a in criticos))

    print("\n-- sano (para contrastar) --")
    sano = {
        "ram_libre_mb": 4200.0,
        "swap_pct": 0.0,
        "disco_libre_pct": 55.0,
        "bateria_pct": 88.0,
        "temp_c": 33.0,
        "wakelock_h": 0.0,
        "ram_total_mb": 7573.0,
    }
    r3 = mon.evaluar(sano)
    print(
        "   puntuacion:",
        r3["puntuacion"],
        "veredicto:",
        r3["veredicto"],
        "alertas:",
        len(r3["alertas"]),
    )

    print("\n-- el peor sensor limita la nota (no se tapa con la media) --")
    mixto = {
        "ram_libre_mb": 6000.0,
        "swap_pct": 99.0,
        "disco_libre_pct": 80.0,
        "bateria_pct": 95.0,
        "temp_c": 30.0,
        "wakelock_h": 0.0,
        "ram_total_mb": 7573.0,
    }
    r4 = mon.evaluar(mixto)
    print("   swap al 99 % pero todo lo demas perfecto ->", r4["puntuacion"], r4["veredicto"])

    print("=" * 68)


if __name__ == "__main__":
    _demo()


class HealthMonitor:
    pass
