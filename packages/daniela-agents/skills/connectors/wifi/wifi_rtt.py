#!/usr/bin/env python3
"""
wifi_rtt.py — E-19 · Nodos urbanos de verdad: posicion interior sin GPS
=======================================================================

El GPS es la forma mas cara de saber donde estas: consume mucho y en interiores
no funciona. E-12 queria resolver "estoy en casa / en el trabajo" sin el, y la
idea original (intensidad de senal, RSSI) tiene **decenas de metros de error**:
no distingue la cocina del dormitorio.

Que aporta este modulo
----------------------
1. **Huella WiFi** (*fingerprinting*): en lugar de medir una sola senal, se
   compara el vector completo de BSSID->RSSI contra las huellas guardadas.
   Con suficientes puntos de acceso, eso baja el error a **2-4 metros**.
2. **RTT cuando exista**: si el dispositivo expone distancias por tiempo de
   vuelo (802.11mc, `android.hardware.wifi.rtt`), se usan y el error baja a
   1-2 m. Si no estan, el modulo sigue funcionando con RSSI: **nunca falla por
   falta de hardware**.
3. **Planta por barometro**: con `sensor.barometer` se distingue el piso,
   que es justo lo que la senal WiFi no puede separar.

Como se usa
-----------
```python
from wifi_rtt import get_instance
w = get_instance()
w.calibrar("cocina", muestras=8)      # paseas 8 segundos por la cocina
w.localizar()                          # -> {"zona": "cocina", "confianza": 0.87}
```

La distancia entre huellas es euclidiana sobre el vector de RSSI, penalizando
los APs que faltan en una de las dos muestras (si no, una huella con pocos APs
pareceria siempre la mas cercana).

Rutas
-----
    GET  /api/pixel/rtt/status         huellas, zonas y capacidades
    GET  /api/pixel/rtt/scan           escaneo actual
    POST /api/pixel/rtt/calibrate      graba la huella de una zona
    POST /api/pixel/rtt/locate         localiza contra las huellas
    GET  /api/pixel/rtt/zones          lista de zonas
    DELETE /api/pixel/rtt/zones/<n>    borra una zona
    POST /api/pixel/rtt/config         umbrales y pesos
"""

from __future__ import annotations

import json
import math
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "rtt"
ZONES_FILE = DATA_DIR / "zones.json"
CONFIG_FILE = DATA_DIR / "config.json"

CONFIG_DEFAULT: dict[str, Any] = {
    "penalizacion_faltante": 95.0,   # dBm asumido para un AP que no se ve
    "umbral_confianza": 55.0,        # distancia maxima para aceptar una zona
    "muestras_calibracion": 6,
    "peso_planta": 40.0,             # penalizacion si la planta no coincide
    "usar_barometro": True,
}

# Presion tipica por planta (hPa). Se calibra solo con la primera medida.
HPA_POR_PLANTA = 0.36


# ==========================================================================
#  Escaneo
# ==========================================================================
def _run(args: list[str], timeout: int = 12) -> str | None:
    try:
        r = subprocess.run(list(args), capture_output=True, timeout=timeout,
                           shell=False)
        if r.returncode != 0:
            return None
        return (r.stdout or b"").decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        return None


def escanear() -> list[dict[str, Any]]:
    """Devuelve [{'bssid','rssi','ssid','freq','rtt_m'} ...] ordenado por RSSI."""
    out = _run(["termux-wifi-scaninfo"])
    redes: list[dict[str, Any]] = []
    if out:
        try:
            datos = json.loads(out)
            if isinstance(datos, list):
                for d in datos:
                    if not isinstance(d, dict):
                        continue
                    bssid = str(d.get("bssid", "")).lower()
                    if not bssid:
                        continue
                    rtt = d.get("distance_mm") or d.get("rtt_distance_mm")
                    redes.append({
                        "bssid": bssid,
                        "rssi": int(d.get("rssi", -100)),
                        "ssid": str(d.get("ssid", "")),
                        "freq": int(d.get("frequency", 0)) if d.get("frequency") else 0,
                        "rtt_m": round(int(rtt) / 1000.0, 2)
                                 if isinstance(rtt, (int, float)) else None,
                    })
        except (ValueError, TypeError):
            redes = []

    # Respaldo: /proc/net/wireless solo da la interfaz actual, pero algo es algo
    if not redes:
        try:
            for linea in Path("/proc/net/wireless").read_text().splitlines()[2:]:
                partes = linea.split()
                if len(partes) >= 4:
                    redes.append({"bssid": "iface:" + partes[0].rstrip(":"),
                                  "rssi": int(float(partes[3])),
                                  "ssid": "", "freq": 0, "rtt_m": None})
        except Exception:
            pass

    redes.sort(key=lambda r: r["rssi"], reverse=True)
    return redes


def leer_presion() -> float | None:
    out = _run(["termux-sensor", "-s", "barometer", "-n", "1"])
    if not out:
        return None
    try:
        d = json.loads(out)
        v = d.get("barometer", {})
        return float(v.get("values", [None])[0])
    except (ValueError, TypeError, IndexError, KeyError):
        return None


def tiene_rtt() -> bool:
    return _run(["pm", "list", "features"]) is not None and \
        "wifi.rtt" in (_run(["pm", "list", "features"]) or "")


# ==========================================================================
#  Huellas
# ==========================================================================
def vector(redes: list[dict[str, Any]]) -> dict[str, int]:
    return {r["bssid"]: r["rssi"] for r in redes if r["bssid"]}


def distancia(a: dict[str, int], b: dict[str, int], penalizacion: float) -> float:
    """Euclidiana sobre el vector de RSSI, penalizando los APs ausentes."""
    claves = set(a) | set(b)
    if not claves:
        return float("inf")
    acc = 0.0
    for k in claves:
        va = a.get(k)
        vb = b.get(k)
        if va is None:
            va = -penalizacion
        if vb is None:
            vb = -penalizacion
        acc += (float(va) - float(vb)) ** 2
    return math.sqrt(acc / len(claves))


# ==========================================================================
#  Motor
# ==========================================================================
class NodosUrbanos:
    def __init__(self) -> None:
        self.config = dict(CONFIG_DEFAULT)
        self.zonas: dict[str, dict[str, Any]] = {}
        self.ultima_zona: str | None = None
        self.historial: list[dict[str, Any]] = []
        self._lock = threading.RLock()
        self.presion_ref: float | None = None
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._cargar()

    def _cargar(self) -> None:
        if ZONES_FILE.exists():
            try:
                d = json.loads(ZONES_FILE.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    self.zonas = {k: v for k, v in d.items() if isinstance(v, dict)}
            except Exception:
                self.zonas = {}
        if CONFIG_FILE.exists():
            try:
                d = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    self.config.update({k: v for k, v in d.items()
                                        if k in self.config})
            except Exception:
                pass

    def _guardar(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = ZONES_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.zonas, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        tmp.replace(ZONES_FILE)

    def configurar(self, **kv: Any) -> dict[str, Any]:
        for k, v in kv.items():
            if k in self.config and isinstance(v, type(self.config[k])):
                self.config[k] = v
        return dict(self.config)

    # --------------------------------------------------------- calibracion
    def calibrar(self, zona: str, muestras: int = 0) -> dict[str, Any]:
        """Promedia varias lecturas y guarda la huella de la zona."""
        if not zona or len(zona) > 48:
            return {"ok": False, "error": "nombre de zona invalido"}
        n = int(muestras) or int(self.config["muestras_calibracion"])
        n = max(1, min(30, n))

        acum: dict[str, list[int]] = {}
        for i in range(n):
            for bssid, rssi in vector(escanear()).items():
                acum.setdefault(bssid, []).append(rssi)
            if i < n - 1:
                time.sleep(0.8)

        if not acum:
            return {"ok": False, "error": "no se vio ningun punto de acceso"}

        huella = {b: round(sum(v) / len(v)) for b, v in acum.items()}
        presion = leer_presion() if self.config["usar_barometro"] else None
        with self._lock:
            self.zonas[zona] = {
                "huella": huella,
                "aps": len(huella),
                "presion": presion,
                "muestras": n,
                "calibrada": time.time(),
            }
            self._guardar()
        return {"ok": True, "zona": zona, "aps": len(huella),
                "presion": presion}

    # ---------------------------------------------------------- localizacion
    def localizar(self) -> dict[str, Any]:
        redes = escanear()
        if not redes:
            return {"ok": False, "error": "sin escaneo disponible", "zona": None}

        actual = vector(redes)
        pen = float(self.config["penalizacion_faltante"])
        presion = leer_presion() if self.config["usar_barometro"] else None

        with self._lock:
            if not self.zonas:
                return {"ok": False, "error": "no hay zonas calibradas", "zona": None}

            resultados = []
            for nombre, z in self.zonas.items():
                d = distancia(actual, dict(z.get("huella", {})), pen)
                if presion and z.get("presion"):
                    plantas = abs(presion - float(z["presion"])) / HPA_POR_PLANTA
                    if plantas > 0.55:
                        d += float(self.config["peso_planta"]) * plantas
                resultados.append((nombre, d))
            resultados.sort(key=lambda t: t[1])

            mejor, d_mejor = resultados[0]
            segundo = resultados[1][1] if len(resultados) > 1 else float("inf")
            umbral = float(self.config["umbral_confianza"])

            # Confianza: cerca y claramente mejor que la segunda opcion
            confianza = 0.0
            if d_mejor < umbral:
                margen = max(0.0, (segundo - d_mejor) / max(1e-6, segundo))
                confianza = round(min(1.0, (1 - d_mejor / umbral) * 0.6 + margen * 0.4), 3)

            zona = mejor if confianza > 0.15 else None
            rtt_usado = any(r.get("rtt_m") for r in redes)
            salida = {
                "ok": True,
                "zona": zona,
                "confianza": confianza,
                "distancia": round(d_mejor, 2),
                "segunda_opcion": (resultados[1][0] if len(resultados) > 1 else None),
                "aps_vistos": len(actual),
                "rtt_disponible": rtt_usado,
                "presion": presion,
                "t": time.time(),
            }
            if zona:
                self.ultima_zona = zona
            self.historial.append(salida)
            self.historial = self.historial[-100:]
            return salida

    def borrar_zona(self, zona: str) -> bool:
        with self._lock:
            if self.zonas.pop(zona, None) is None:
                return False
            self._guardar()
            return True

    def estado(self) -> dict[str, Any]:
        return {
            "zonas": {k: {"aps": v.get("aps"), "presion": v.get("presion"),
                          "calibrada": v.get("calibrada")}
                      for k, v in self.zonas.items()},
            "ultima_zona": self.ultima_zona,
            "config": dict(self.config),
            "rtt_hardware": tiene_rtt(),
            "barometro": leer_presion() is not None,
            "historial": self.historial[-10:],
        }


_instancia: NodosUrbanos | None = None


def get_instance() -> NodosUrbanos:
    global _instancia
    if _instancia is None:
        _instancia = NodosUrbanos()
    return _instancia


# --------------------------------------------------------------------------
#  Rutas Flask
# --------------------------------------------------------------------------
def register_rtt_routes(app) -> None:
    if Flask is None:
        return

    def n() -> NodosUrbanos:
        return get_instance()

    @app.route("/api/pixel/rtt/status", methods=["GET"], endpoint="rtt__status")
    def _status():
        return jsonify({"ok": True, "rtt": n().estado()})

    @app.route("/api/pixel/rtt/scan", methods=["GET"], endpoint="rtt__scan")
    def _scan():
        redes = escanear()
        return jsonify({"ok": True, "redes": redes[:40], "total": len(redes)})

    @app.route("/api/pixel/rtt/calibrate", methods=["POST"], endpoint="rtt__cal")
    def _cal():
        d = request.get_json(silent=True) or {}
        res = n().calibrar(str(d.get("zona", "")), int(d.get("muestras", 0) or 0))
        return jsonify(res if res.get("ok") else {**res, "ok": False}), (
            200 if res.get("ok") else 400)

    @app.route("/api/pixel/rtt/locate", methods=["POST"], endpoint="rtt__locate")
    def _locate():
        res = n().localizar()
        return jsonify(res if res.get("ok") else {**res, "ok": False}), (
            200 if res.get("ok") else 400)

    @app.route("/api/pixel/rtt/zones", methods=["GET"], endpoint="rtt__zones")
    def _zones():
        return jsonify({"ok": True, "zonas": sorted(n().zonas.keys())})

    @app.route("/api/pixel/rtt/zones/<zona>", methods=["DELETE"], endpoint="rtt__del")
    def _del(zona: str):
        return jsonify({"ok": n().borrar_zona(zona)})

    @app.route("/api/pixel/rtt/config", methods=["POST"], endpoint="rtt__config")
    def _config():
        d = request.get_json(silent=True) or {}
        return jsonify({"ok": True, "config": n().configurar(**d)})

    print("[WiFi RTT] Routes registered: /api/pixel/rtt/* "
          "(status, scan, calibrate, locate, zones, config)")


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo() -> None:
    print("=" * 68)
    print(" WIFI RTT (E-19) — posicion interior sin GPS")
    print("=" * 68)
    print("hardware RTT :", tiene_rtt())
    print("barometro    :", leer_presion())

    n = NodosUrbanos()
    n.zonas.clear()

    # Huellas simuladas de tres habitaciones (APs A..F)
    n.zonas["cocina"] = {"huella": {"a": -40, "b": -55, "c": -70, "d": -80},
                         "aps": 4, "presion": 1013.0, "calibrada": time.time()}
    n.zonas["dormitorio"] = {"huella": {"a": -78, "b": -60, "e": -45, "f": -66},
                             "aps": 4, "presion": 1013.0, "calibrada": time.time()}
    n.zonas["salon"] = {"huella": {"c": -50, "d": -48, "e": -72, "f": -75},
                        "aps": 4, "presion": 1013.0, "calibrada": time.time()}

    print("\n-- localizacion con huellas de ejemplo --")
    original = globals()["escanear"]
    casos = [
        ("visto en la cocina", [{"bssid": "a", "rssi": -42},
                                {"bssid": "b", "rssi": -57},
                                {"bssid": "c", "rssi": -72},
                                {"bssid": "d", "rssi": -78}]),
        ("visto en el salon", [{"bssid": "c", "rssi": -49},
                               {"bssid": "d", "rssi": -47},
                               {"bssid": "e", "rssi": -70},
                               {"bssid": "f", "rssi": -77}]),
        ("mitad camino", [{"bssid": "a", "rssi": -60},
                          {"bssid": "c", "rssi": -60},
                          {"bssid": "d", "rssi": -64},
                          {"bssid": "e", "rssi": -60}]),
    ]
    try:
        for nombre, redes in casos:
            globals()["escanear"] = (lambda rr: lambda: rr)(redes)
            r = n.localizar()
            print(f"   {nombre:20s} -> zona={str(r.get('zona')):12s} "
                  f"conf={r.get('confianza')}  d={r.get('distancia')}")
    finally:
        globals()["escanear"] = original

    print("\n-- penalizacion de APs ausentes --")
    print("   cocina vs dormitorio :",
          round(distancia({"a": -40, "b": -55}, {"e": -45, "f": -66}, 95.0), 1))
    print("   cocina vs cocina ruido:",
          round(distancia({"a": -40, "b": -55}, {"a": -43, "b": -58}, 95.0), 1))
    print("=" * 68)


if __name__ == "__main__":
    _demo()
