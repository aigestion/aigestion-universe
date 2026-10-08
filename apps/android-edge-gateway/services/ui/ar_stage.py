#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ar_stage.py — E-18 · Daniela AR: del metaverso al bolsillo
==========================================================

El problema
-----------
Neural City 3D y Decentraland viven en el PC. En el movil, Daniela sigue
siendo una pantalla plana: `static/daniela_hologram.html` ya dibujaba un
holograma con three.js, pero **no era AR**: no sabia donde estabas, no estaba
anclada a nada y no reaccionaba a donde mirabas.

Que anade esto
--------------
1. **Escena WebXR de verdad** (`immersive-ar`): Daniela anclada en el espacio,
   con el movil como ventana. Se genera sola en `/api/ar/scene`.
2. **Anclas espaciales**: sitios del mundo real con lat/lon y orientacion.
   Daniela se coloca ahi y te recuerda que llevas N visitas.
3. **Mirada**: con el yaw/pitch reales de la cabeza (los da el propio WebXR a
   60 fps, y si no, el giroscopio por el gateway), Daniela sabe QUE estas
   mirando y reacciona.

🔴 El detalle que nadie cuenta: WebXR solo arranca en contexto seguro
--------------------------------------------------------------------
`navigator.xr` NO existe si abres `http://192.168.1.50:5000/...` en el movil:
los navegadores solo lo exponen en **https** o en **localhost**. Como no
tenemos certificado ni dominio, la solucion es gratis y funciona:

    adb reverse tcp:5000 tcp:5000

...y abrir en el movil **`http://localhost:5000/api/ar/scene`**. Para el
navegador eso ES localhost → contexto seguro → WebXR arranca. Sin tunnels,
sin Cloudflare, sin pagar nada. `GET /api/ar/plan` lo explica paso a paso.

Si aun asi no hay WebXR (navegador sin soporte, PC de escritorio...), la
escena degrada a un holograma 3D plano que gira solo. Nunca se rompe.

Reglas de seguridad
-------------------
1. **Cero `os.system()`, cero `shell=True`**: todo es HTTP con `requests`, o
   `subprocess.run(lista)` sin shell cuando hay que hablar con adb.
2. **La URL del gateway sale del `.env`, nunca de la peticion** (SSRF).
3. Solo entran **numeros** y se validan con rango. Los textos (nombre, color)
   se recortan y se limpian: el nombre va dentro de un JSON que se inyecta en
   la pagina, asi que se escapan `<`, `>`, `&`, `"` y `'`.
4. Las peticiones al movil van **sin proxy**: con `HTTP_PROXY` puesto,
   `localhost` rebota y devuelve 502.
5. El token del gateway se compara con `hmac.compare_digest` en **fail-closed**
   por el propio gateway. Aqui solo se reenvia, nunca se decide con el.

Uso
---
    GET  /api/ar/status      capacidades, sensores, anclas, gateway
    GET  /api/ar/scene       la escena WebXR (HTML autocontenido)
    GET  /api/ar/anchors     anclas conocidas
    POST /api/ar/anchors     crear / visitar / etiquetar / borrar
    GET  /api/ar/pose        ultima pose conocida de la cabeza
    POST /api/ar/pose        el movil empuja su pose (yaw/pitch/posicion)
    GET  /api/ar/sensors     sensores reales del Pixel por el gateway
    GET  /api/ar/gaze        que estas mirando y que dice Daniela
    GET  /api/ar/config      configuracion
    POST /api/ar/config      cambiar escala / cono de mirada / altura
    GET  /api/ar/plan        como abrirlo en el movil (adb reverse incluido)
"""

from __future__ import annotations

import json
import math
import os
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, Response, jsonify, request

try:  # requests puede no estar en un Termux minimal
    import requests
except Exception:  # noqa: BLE001
    requests = None  # type: ignore[assignment]

# --------------------------------------------------------------------------
#  Rutas y constantes
# --------------------------------------------------------------------------
# Fase 2: el codigo vive en pixel/, los datos siguen en la raiz.
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "ar_stage"
ANCHORS_FILE = DATA_DIR / "anclas.json"
POSE_FILE = DATA_DIR / "pose.json"
CONFIG_FILE = DATA_DIR / "config.json"
SCENE_FILE = DATA_DIR / "escena.html"

# Nada de proxy para hablar con el movil o con nosotros mismos.
SIN_PROXY: Dict[str, Optional[str]] = {"http": None, "https": None}
TIMEOUT_GW = 8.0

CONO_MIRADA_DEF = 35.0  # grados: medio cono para considerar "lo estoy mirando"
ESCALA_DEF = 1.0
ALTURA_DEF = 1.55  # metros a los que flota Daniela
COLOR_DEF = "#4dd0e1"
RADIO_ANCLA = 60.0  # m: si creas un ancla a menos de esto de otra, es visita
MAX_HISTORIAL = 200

SENSORES = (
    "accelerometer",
    "gyroscope",
    "orientation",
    "magnetometer",
    "gravity",
    "light",
    "proximity",
)

# Solo se permiten estos caracteres en los textos que viajan al HTML.
TEXTO_SEGURO = re.compile(r"[^\w\s\-.áéíóúüñÁÉÍÓÚÜÑ,:;()#/&+]", re.UNICODE)


# --------------------------------------------------------------------------
#  Utilidades
# --------------------------------------------------------------------------
def _num(valor: Any, minimo: float, maximo: float, defecto: float) -> float:
    """Convierte a float acotando al rango. Nunca lanza excepcion."""
    try:
        x = float(valor)
    except Exception:  # noqa: BLE001
        return defecto
    if math.isnan(x) or math.isinf(x):
        return defecto
    if x < minimo:
        return minimo
    if x > maximo:
        return maximo
    return x


def _texto(valor: Any, maximo: int = 60, defecto: str = "") -> str:
    """Recorta y limpia un texto que acabara dentro de un HTML/JSON."""
    s = "" if valor is None else str(valor)
    s = TEXTO_SEGURO.sub("", s).strip()
    if len(s) > maximo:
        s = s[:maximo].strip()
    return s or defecto


def _ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros entre dos puntos."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _rumbo(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Rumbo inicial en grados (0 = norte) desde el punto 1 al 2."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def _dif_angular(a: float, b: float) -> float:
    """Diferencia minima entre dos angulos, en grados (0..180)."""
    d = abs((a - b) % 360.0)
    return d if d <= 180.0 else 360.0 - d


# --------------------------------------------------------------------------
#  Modelo
# --------------------------------------------------------------------------
@dataclass
class Ancla:
    """Un sitio del mundo real donde Daniela se ancla."""

    id: str
    nombre: str
    lat: float
    lon: float
    alt: float = 0.0
    yaw: float = 0.0
    escala: float = ESCALA_DEF
    color: str = COLOR_DEF
    creado: str = field(default_factory=_ahora)
    visitas: int = 1
    vista: str = ""
    nota: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------
#  Motor
# --------------------------------------------------------------------------
class ArStage:
    """Escena WebXR + anclas espaciales + mirada."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.cfg: Dict[str, Any] = {
            "escala": ESCALA_DEF,
            "cono_mirada": CONO_MIRADA_DEF,
            "altura": ALTURA_DEF,
            "color": COLOR_DEF,
            "auto_habla": True,
        }
        self.anclas: Dict[str, Ancla] = {}
        self.pose: Dict[str, Any] = {}
        self.historial: List[Dict[str, Any]] = []
        self.gateway_url = (
            os.getenv("PIXEL_GATEWAY_URL") or os.getenv("PIXEL_GATEWAY") or ""
        ).strip()
        self.token = (os.getenv("PIXEL_TOKEN") or os.getenv("PIXEL_GATEWAY_TOKEN") or "").strip()
        self._cargar()

    # ---------------- persistencia ----------------
    def _cargar(self) -> None:
        try:
            if CONFIG_FILE.exists():
                self.cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            pass
        try:
            if ANCHORS_FILE.exists():
                crudo = json.loads(ANCHORS_FILE.read_text(encoding="utf-8"))
                for k, v in (crudo or {}).items():
                    try:
                        self.anclas[k] = Ancla(**v)
                    except Exception:  # noqa: BLE001
                        continue
        except Exception:  # noqa: BLE001
            pass
        try:
            if POSE_FILE.exists():
                datos = json.loads(POSE_FILE.read_text(encoding="utf-8"))
                self.pose = datos.get("pose") or {}
                self.historial = list(datos.get("historial") or [])[-MAX_HISTORIAL:]
        except Exception:  # noqa: BLE001
            pass

    def _guardar(self, que: str = "todo") -> None:
        with self._lock:
            try:
                if que in ("todo", "cfg"):
                    CONFIG_FILE.write_text(
                        json.dumps(self.cfg, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                if que in ("todo", "anclas"):
                    ANCHORS_FILE.write_text(
                        json.dumps(
                            {k: v.to_dict() for k, v in self.anclas.items()},
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
                if que in ("todo", "pose"):
                    POSE_FILE.write_text(
                        json.dumps(
                            {"pose": self.pose, "historial": self.historial[-MAX_HISTORIAL:]},
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
            except Exception:  # noqa: BLE001
                pass

    # ---------------- gateway ----------------
    def _gateway(
        self, ruta: str, cuerpo: Optional[Dict[str, Any]] = None, timeout: float = TIMEOUT_GW
    ) -> Dict[str, Any]:
        """Llama al gateway del movil. Nunca lanza: devuelve {'ok': False}."""
        if not self.gateway_url:
            return {"ok": False, "error": "sin gateway: define PIXEL_GATEWAY_URL en el .env"}
        if requests is None:
            return {"ok": False, "error": "requests no disponible"}
        url = self.gateway_url.rstrip("/") + ruta
        headers = {"X-Pixel-Token": self.token}
        try:
            if cuerpo is None:
                r = requests.get(url, headers=headers, timeout=timeout, proxies=SIN_PROXY)
            else:
                r = requests.post(
                    url, headers=headers, json=cuerpo, timeout=timeout, proxies=SIN_PROXY
                )
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"gateway inaccesible: {e}"}
        try:
            return dict(r.json())
        except Exception:  # noqa: BLE001
            return {"ok": False, "error": f"respuesta no JSON (HTTP {r.status_code})"}

    def sensores(self, nombre: str = "orientation") -> Dict[str, Any]:
        """Lee un sensor real del Pixel через el gateway de Termux."""
        if nombre not in SENSORES:
            return {
                "ok": False,
                "error": f"sensor no permitido: {nombre}",
                "permitidos": list(SENSORES),
            }
        r = self._gateway("/api/pixel/sensor", {"sensor": nombre, "delay": 100, "count": 1})
        if not r.get("ok"):
            return r
        datos = r.get("data")
        valores: List[float] = []
        # termux-sensor devuelve {"<nombre>": {"values": [x, y, z]}}
        if isinstance(datos, dict):
            for v in datos.values():
                if isinstance(v, dict) and isinstance(v.get("values"), list):
                    valores = [float(x) for x in v["values"] if isinstance(x, (int, float))]
                    break
        return {
            "ok": True,
            "sensor": nombre,
            "valores": valores,
            "crudo": datos if not isinstance(datos, str) else datos[:200],
            "cuando": _ahora(),
        }

    # ---------------- pose ----------------
    def registrar_pose(self, cuerpo: Dict[str, Any]) -> Dict[str, Any]:
        """Guarda la pose que manda el movil (WebXR o giroscopio)."""
        yaw = _num(cuerpo.get("yaw"), 0.0, 360.0, 0.0)
        pitch = _num(cuerpo.get("pitch"), -90.0, 90.0, 0.0)
        roll = _num(cuerpo.get("roll"), -180.0, 180.0, 0.0)
        pose = {
            "yaw": round(yaw, 2),
            "pitch": round(pitch, 2),
            "roll": round(roll, 2),
            "x": round(_num(cuerpo.get("x"), -100000, 100000, 0.0), 3),
            "y": round(_num(cuerpo.get("y"), -100000, 100000, self.cfg["altura"]), 3),
            "z": round(_num(cuerpo.get("z"), -100000, 100000, 0.0), 3),
            "lat": _num(cuerpo.get("lat"), -90, 90, 0.0),
            "lon": _num(cuerpo.get("lon"), -180, 180, 0.0),
            "origen": _texto(cuerpo.get("origen"), 20, "webxr"),
            "cuando": _ahora(),
        }
        with self._lock:
            self.pose = pose
            self.historial.append(pose)
            if len(self.historial) > MAX_HISTORIAL:
                self.historial = self.historial[-MAX_HISTORIAL:]
        self._guardar("pose")
        return {"ok": True, "pose": pose, "muestras": len(self.historial)}

    # ---------------- anclas ----------------
    def crear_ancla(self, cuerpo: Dict[str, Any]) -> Dict[str, Any]:
        lat = _num(cuerpo.get("lat"), -90, 90, 0.0)
        lon = _num(cuerpo.get("lon"), -180, 180, 0.0)
        if not lat and not lon:
            return {"ok": False, "error": "falta lat/lon"}
        with self._lock:
            for a in self.anclas.values():
                if _haversine(lat, lon, a.lat, a.lon) <= RADIO_ANCLA:
                    a.visitas += 1
                    a.vista = _ahora()
                    self._guardar("anclas")
                    return {
                        "ok": True,
                        "accion": "visita",
                        "ancla": a.to_dict(),
                        "nota": f"a {_haversine(lat, lon, a.lat, a.lon):.0f} m de " f"'{a.nombre}'",
                    }
            aid = "a" + str(int(time.time()))
            nombre = _texto(cuerpo.get("nombre"), 60, f"Ancla {aid[-4:]}")
            a = Ancla(
                id=aid,
                nombre=nombre,
                lat=lat,
                lon=lon,
                alt=_num(cuerpo.get("alt"), -500, 9000, 0.0),
                yaw=_num(cuerpo.get("yaw"), 0, 360, 0.0),
                escala=_num(cuerpo.get("escala"), 0.1, 10.0, self.cfg["escala"]),
                color=_texto(cuerpo.get("color"), 9, self.cfg["color"]) or COLOR_DEF,
                nota=_texto(cuerpo.get("nota"), 200, ""),
            )
            self.anclas[aid] = a
            self._guardar("anclas")
        return {"ok": True, "accion": "creada", "ancla": a.to_dict()}

    def borrar_ancla(self, aid: str) -> bool:
        with self._lock:
            if aid in self.anclas:
                del self.anclas[aid]
                self._guardar("anclas")
                return True
        return False

    def etiquetar(self, aid: str, cuerpo: Dict[str, Any]) -> Optional[Ancla]:
        with self._lock:
            a = self.anclas.get(aid)
            if not a:
                return None
            nombre = _texto(cuerpo.get("nombre"), 60, "")
            if nombre:
                a.nombre = nombre
            if cuerpo.get("nota") is not None:
                a.nota = _texto(cuerpo.get("nota"), 200, "")
            if cuerpo.get("color") is not None:
                a.color = _texto(cuerpo.get("color"), 9, a.color) or a.color
            self._guardar("anclas")
            return a

    def listar(self, limite: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            out = [a.to_dict() for a in self.anclas.values()]
        out.sort(key=lambda d: -int(d.get("visitas") or 0))
        return out[:limite]

    # ---------------- mirada ----------------
    def mirada(self, lat: float, lon: float, yaw: float, pitch: float) -> Dict[str, Any]:
        """Que ancla cae dentro del cono de mirada y que diria Daniela."""
        cono = float(self.cfg.get("cono_mirada") or CONO_MIRADA_DEF)
        vistos: List[Dict[str, Any]] = []
        with self._lock:
            for a in self.anclas.values():
                d = _haversine(lat, lon, a.lat, a.lon)
                if d > 5000:  # mas de 5 km: fuera de juego
                    continue
                rumbo = _rumbo(lat, lon, a.lat, a.lon)
                dif = _dif_angular(rumbo, yaw)
                if dif <= cono:
                    vistos.append(
                        {
                            "id": a.id,
                            "nombre": a.nombre,
                            "distancia_m": round(d, 1),
                            "desvio_grados": round(dif, 1),
                            "visitas": a.visitas,
                        }
                    )
        vistos.sort(key=lambda x: x["desvio_grados"])
        enfocado = vistos[0] if vistos else None
        if enfocado:
            # Si estas ENCIMA del ancla el rumbo no significa nada: no tiene
            # sentido decir "lo ves a 0 m mirando al norte".
            if enfocado["distancia_m"] < 2.0:
                frase = (
                    f"Estas justo en '{enfocado['nombre']}'. Van " f"{enfocado['visitas']} visitas."
                )
            elif abs(pitch) > 55:
                frase = (
                    f"Estas mirando al suelo, pero '{enfocado['nombre']}' "
                    f"sigue ahi, a {enfocado['distancia_m']:.0f} m."
                )
            elif enfocado["visitas"] > 3:
                frase = f"Otra vez en '{enfocado['nombre']}'. Van " f"{enfocado['visitas']}."
            else:
                frase = f"Veo '{enfocado['nombre']}' a " f"{enfocado['distancia_m']:.0f} m."
        else:
            frase = "No veo ninguna ancla por donde miras."
            if not self.anclas:
                frase = (
                    "No hay anclas todavia. Crea una con "
                    "POST /api/ar/anchors o di 'ancla este sitio'."
                )
        return {
            "ok": True,
            "yaw": round(yaw, 1),
            "pitch": round(pitch, 1),
            "cono_grados": cono,
            "en_cono": len(vistos),
            "enfocado": enfocado,
            "visibles": vistos[:10],
            "frase": frase,
            "cuando": _ahora(),
        }

    # ---------------- estado y plan ----------------
    def estado(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "modulo": "ar_stage",
            "epica": "E-18",
            "anclas": len(self.anclas),
            "visitas_totales": sum(int(a.visitas) for a in self.anclas.values()),
            "pose": self.pose or None,
            "muestras_pose": len(self.historial),
            "gateway": {
                "url": self.gateway_url or "",
                "configurado": bool(self.gateway_url),
                "token_ok": bool(self.token),
            },
            "config": dict(self.cfg),
            "sensores_permitidos": list(SENSORES),
            "escena_html": str(SCENE_FILE.relative_to(ROOT)).replace("\\", "/"),
        }

    def plan(self, puerto: int = 5000) -> Dict[str, Any]:
        return {
            "ok": True,
            "por_que": (
                "WebXR solo funciona en contexto seguro (https o "
                "localhost). Sin dominio ni certificado, usamos adb "
                "reverse: el movil ve TU puerto como si fuera suyo."
            ),
            "pasos": [
                "1. Conecta el Pixel por USB (o adb connect IP:5555 por WiFi).",
                f"2. En el PC:  adb reverse tcp:{puerto} tcp:{puerto}",
                f"3. Abre en el movil:  http://localhost:{puerto}/api/ar/scene",
                "4. Pulsa 'Entrar en AR'. Si Chrome no ofrece AR, activa "
                "chrome://flags/#webxr-incubations y reinicia.",
                "5. Mueve la cabeza: la pose se envia a /api/ar/pose y Daniela "
                "te dice que estas mirando.",
            ],
            "alternativa_sin_adb": (
                "Sirve la escena por https con un certificado "
                "autofirmado y acepta la advertencia, o usa "
                "Tailscale + un tunel local. Nada de eso hace "
                "falta con adb reverse."
            ),
            "degradacion": (
                "Sin WebXR la escena sigue funcionando como holograma "
                "3D plano en el navegador. En PC de escritorio es lo "
                "normal."
            ),
            "comando_adb": ["adb", "reverse", f"tcp:{puerto}", f"tcp:{puerto}"],
            "url_movil": f"http://localhost:{puerto}/api/ar/scene",
            "nota": "Este modulo NO ejecuta adb por ti: es tu movil y tu sesion.",
        }

    def configurar(self, cuerpo: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            if "escala" in cuerpo:
                self.cfg["escala"] = _num(cuerpo.get("escala"), 0.1, 10.0, ESCALA_DEF)
            if "cono_mirada" in cuerpo:
                self.cfg["cono_mirada"] = _num(cuerpo.get("cono_mirada"), 5, 180, CONO_MIRADA_DEF)
            if "altura" in cuerpo:
                self.cfg["altura"] = _num(cuerpo.get("altura"), 0.2, 5.0, ALTURA_DEF)
            if "color" in cuerpo:
                self.cfg["color"] = _texto(cuerpo.get("color"), 9, COLOR_DEF)
            if "auto_habla" in cuerpo:
                self.cfg["auto_habla"] = bool(cuerpo.get("auto_habla"))
        self._guardar("cfg")
        return {"ok": True, "config": dict(self.cfg)}

    # ---------------- la escena ----------------
    def escena(self) -> str:
        """Devuelve el HTML de la escena WebXR (y lo deja en disco)."""
        with self._lock:
            anclas = [a.to_dict() for a in self.anclas.values()]
            cfg = dict(self.cfg)
        html = _PLANTILLA.replace("__ANCLAS__", json.dumps(anclas, ensure_ascii=False)).replace(
            "__CFG__", json.dumps(cfg, ensure_ascii=False)
        )
        try:
            SCENE_FILE.write_text(html, encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
        return html


# --------------------------------------------------------------------------
#  Plantilla de la escena (HTML + three.js + WebXR)
# --------------------------------------------------------------------------
# Ojo: se inyecta con .replace(), NO con f-strings: el codigo JS esta lleno de
# llaves y las romperia.
_PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Daniela AR — E-18</title>
<style>
  * { box-sizing: border-box; }
  body { margin:0; background:#07080d; color:#e8f6f8;
         font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
         overflow:hidden; }
  #hud { position:fixed; left:0; right:0; top:0; padding:14px; z-index:10;
         pointer-events:none; text-shadow:0 1px 3px #000; }
  #hud .chip { display:inline-block; background:rgba(0,0,0,.45);
               border:1px solid rgba(77,208,225,.35); border-radius:999px;
               padding:6px 12px; margin:0 6px 6px 0; font-size:13px; }
  #frase { margin-top:8px; font-size:16px; line-height:1.35; max-width:34em; }
  #pie { position:fixed; left:0; right:0; bottom:0; padding:14px; z-index:10;
         display:flex; gap:10px; justify-content:center; }
  button { pointer-events:auto; background:#0e7490; color:#fff; border:0;
           border-radius:10px; padding:12px 18px; font-size:15px; font-weight:600; }
  button:disabled { opacity:.45; }
  #aviso { position:fixed; inset:auto 12px 68px 12px; background:rgba(120,0,0,.55);
           border:1px solid #ff8a80; border-radius:10px; padding:10px; font-size:13px;
           display:none; z-index:11; }
  canvas { display:block; }
</style>
</head>
<body>
<div id="hud">
  <span class="chip" id="chipEstado">comprobando WebXR…</span>
  <span class="chip" id="chipPose">sin pose</span>
  <div id="frase">Daniela AR — pulsá “Entrar en AR”.</div>
</div>
<div id="aviso"></div>
<div id="pie">
  <button id="btnAR" disabled>Entrar en AR</button>
  <button id="btnPlano">Holograma plano</button>
  <button id="btnAncla">Anclar aquí</button>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function () {
  var ANCLAS = __ANCLAS__;
  var CFG = __CFG__;
  var API = "";                       // mismo origen: rutas relativas
  var estado = document.getElementById("chipEstado");
  var chipPose = document.getElementById("chipPose");
  var fraseEl = document.getElementById("frase");
  var aviso = document.getElementById("aviso");
  var btnAR = document.getElementById("btnAR");
  var btnPlano = document.getElementById("btnPlano");
  var btnAncla = document.getElementById("btnAncla");

  function decir(t) { fraseEl.textContent = t; }
  function avisar(t) { aviso.style.display = "block"; aviso.textContent = t; }

  if (!window.isSecureContext) {
    avisar("Esta página no está en contexto seguro: WebXR no arrancará. " +
           "Abre http://localhost:PUERTO/api/ar/scene desde el móvil " +
           "(adb reverse), no por IP.");
  }

  // ---------- three.js ----------
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(70, innerWidth / innerHeight, 0.01, 100);
  camera.position.set(0, CFG.altura, 0);
  var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(innerWidth, innerHeight);
  renderer.xr.enabled = true;
  document.body.appendChild(renderer.domElement);

  scene.add(new THREE.HemisphereLight(0xbfefff, 0x202030, 1.1));
  var punto = new THREE.PointLight(0x4dd0e1, 1.2, 12);
  punto.position.set(0, CFG.altura + 0.4, 0.6);
  scene.add(punto);

  // ---------- Daniela: anillos + núcleo + etiqueta ----------
  var daniela = new THREE.Group();
  var color = new THREE.Color(CFG.color || "#4dd0e1");
  for (var i = 0; i < 3; i++) {
    var geo = new THREE.TorusGeometry(0.16 + i * 0.055, 0.005 + i * 0.002, 12, 64);
    var mat = new THREE.MeshBasicMaterial({ color: color, transparent: true,
                                            opacity: 0.85 - i * 0.2 });
    var anillo = new THREE.Mesh(geo, mat);
    anillo.rotation.x = Math.PI / 2 * (i % 2);
    daniela.add(anillo);
  }
  var nucleo = new THREE.Mesh(
    new THREE.SphereGeometry(0.045, 24, 24),
    new THREE.MeshBasicMaterial({ color: color }));
  daniela.add(nucleo);
  daniela.position.set(0, CFG.altura, -1.1);
  daniela.scale.setScalar(CFG.escala || 1);
  scene.add(daniela);

  function etiqueta(texto) {
    var c = document.createElement("canvas");
    c.width = 512; c.height = 128;
    var g = c.getContext("2d");
    g.fillStyle = "rgba(0,0,0,0)"; g.fillRect(0, 0, 512, 128);
    g.font = "600 44px system-ui, sans-serif";
    g.fillStyle = "#e8f6f8"; g.textAlign = "center";
    g.fillText(String(texto).slice(0, 28), 256, 74);
    var tex = new THREE.CanvasTexture(c);
    var spr = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
    spr.scale.set(0.6, 0.15, 1);
    spr.position.set(0, 0.28, 0);
    return spr;
  }
  var rotulo = etiqueta("Daniela");
  daniela.add(rotulo);

  // ---------- anclas del mundo real ----------
  var grupoAnclas = new THREE.Group();
  scene.add(grupoAnclas);
  function pintarAnclas() {
    while (grupoAnclas.children.length) grupoAnclas.remove(grupoAnclas.children[0]);
    ANCLAS.forEach(function (a, i) {
      var ang = (i / Math.max(ANCLAS.length, 1)) * Math.PI * 2;
      var r = 2.2;
      var m = new THREE.Mesh(
        new THREE.OctahedronGeometry(0.08),
        new THREE.MeshBasicMaterial({ color: new THREE.Color(a.color || "#4dd0e1"),
                                      wireframe: true }));
      m.position.set(Math.cos(ang) * r, CFG.altura - 0.2 + (i % 3) * 0.12,
                     Math.sin(ang) * r);
      m.add(etiqueta(a.nombre + " (" + a.visitas + ")"));
      grupoAnclas.add(m);
    });
  }
  pintarAnclas();

  // ---------- envío de pose ----------
  var ultimoEnvio = 0;
  function extraerPose() {
    var dir = new THREE.Vector3();
    camera.getWorldDirection(dir);
    var yaw = (Math.atan2(dir.x, -dir.z) * 180 / Math.PI + 360) % 360;
    var pitch = Math.asin(Math.max(-1, Math.min(1, dir.y))) * 180 / Math.PI;
    var p = camera.getWorldPosition(new THREE.Vector3());
    return { yaw: yaw, pitch: pitch, roll: 0,
             x: p.x, y: p.y, z: p.z, origen: renderer.xr.isPresenting ? "webxr" : "plano" };
  }
  function enviarPose(forzar) {
    var ahora = performance.now();
    if (!forzar && ahora - ultimoEnvio < 250) return;   // ~4 Hz
    ultimoEnvio = ahora;
    var pose = extraerPose();
    chipPose.textContent = "yaw " + pose.yaw.toFixed(0) + "° · pitch " +
                           pose.pitch.toFixed(0) + "°";
    fetch(API + "/api/ar/pose", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pose)
    }).then(function (r) { return r.json(); })
      .then(function (d) { if (d && d.ok) actualizarMirada(pose); })
      .catch(function () { });
  }
  function actualizarMirada(pose) {
    fetch(API + "/api/ar/gaze?yaw=" + encodeURIComponent(pose.yaw) +
          "&pitch=" + encodeURIComponent(pose.pitch))
      .then(function (r) { return r.json(); })
      .then(function (d) { if (d && d.frase) decir(d.frase); })
      .catch(function () { });
  }

  // ---------- bucle ----------
  var t0 = performance.now();
  renderer.setAnimationLoop(function () {
    var t = (performance.now() - t0) / 1000;
    for (var i = 0; i < daniela.children.length; i++) {
      var h = daniela.children[i];
      if (h.geometry && h.geometry.type === "TorusGeometry") h.rotation.z = t * (0.4 + i * 0.2);
    }
    nucleo.scale.setScalar(1 + Math.sin(t * 2.2) * 0.12);
    grupoAnclas.rotation.y = Math.sin(t * 0.15) * 0.05;
    if (!renderer.xr.isPresenting) {
      // Modo plano: orbita suave para que se vea algo en PC.
      var r = 2.6, a = t * 0.25;
      camera.position.set(Math.sin(a) * r, CFG.altura, Math.cos(a) * r);
      camera.lookAt(daniela.position);
    }
    enviarPose(false);
    renderer.render(scene, camera);
  });

  addEventListener("resize", function () {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
  });

  // ---------- WebXR ----------
  var sesion = null;
  if (navigator.xr) {
    navigator.xr.isSessionSupported("immersive-ar").then(function (soportado) {
      if (soportado) {
        btnAR.disabled = false;
        estado.textContent = "WebXR immersive-ar listo";
      } else {
        estado.textContent = "sin immersive-ar (modo plano)";
        avisar("Este navegador no ofrece immersive-ar. Puedes seguir en modo " +
               "holograma plano.");
      }
    }).catch(function () {
      estado.textContent = "WebXR no disponible";
    });
  } else {
    estado.textContent = "navigator.xr ausente";
    avisar("Sin navigator.xr. Comprueba que abres la página por http://localhost " +
           "(adb reverse) y no por IP.");
  }

  btnAR.addEventListener("click", function () {
    if (!navigator.xr) return;
    navigator.xr.requestSession("immersive-ar", {
      optionalFeatures: ["local-floor", "dom-overlay"],
      domOverlay: { root: document.getElementById("hud") }
    }).then(function (s) {
      sesion = s;
      estado.textContent = "en AR";
      return renderer.xr.setSession(s);
    }).then(function () {
      decir("Daniela anclada. Mueve la cabeza: te digo qué estás mirando.");
      s = null;
    }).catch(function (e) {
      avisar("No se pudo entrar en AR: " + (e && e.message ? e.message : e));
    });
    var s = null;
  });

  btnPlano.addEventListener("click", function () {
    if (sesion) { sesion.end(); sesion = null; }
    estado.textContent = "holograma plano";
    decir("Modo plano. Sin WebXR Daniela sigue aquí, flotando.");
  });

  btnAncla.addEventListener("click", function () {
    if (!navigator.geolocation) { avisar("Sin geolocalización en el navegador."); return; }
    navigator.geolocation.getCurrentPosition(function (pos) {
      fetch(API + "/api/ar/anchors", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accion: "crear",
                               lat: pos.coords.latitude, lon: pos.coords.longitude,
                               alt: pos.coords.altitude || 0,
                               nombre: "Ancla " + new Date().toLocaleTimeString() })
      }).then(function (r) { return r.json(); })
        .then(function (d) {
          if (d && d.ok) {
            decir(d.accion === "visita"
              ? ("Ya conocía este sitio: " + d.ancla.nombre + " (" + d.ancla.visitas + " visitas)")
              : ("Ancla creada: " + d.ancla.nombre));
            fetch(API + "/api/ar/anchors").then(function (r) { return r.json(); })
              .then(function (l) { if (l && l.anclas) { ANCLAS = l.anclas; pintarAnclas(); } })
              .catch(function () { });
          } else { avisar("No se pudo anclar: " + (d && d.error ? d.error : "?")); }
        }).catch(function (e) { avisar("Error de red al anclar: " + e); });
    }, function (e) { avisar("Geolocalización denegada: " + e.message); },
       { enableHighAccuracy: true, timeout: 10000 });
  });
})();
</script>
</body>
</html>
"""


# --------------------------------------------------------------------------
#  Instancia y rutas
# --------------------------------------------------------------------------
_instancia: Optional[ArStage] = None
_lock = threading.RLock()


def get_instance() -> ArStage:
    global _instancia
    with _lock:
        if _instancia is None:
            _instancia = ArStage()
        return _instancia


ar_bp = Blueprint("ar_stage", __name__)


def _coords() -> Tuple[float, float]:
    """lat/lon de la query, del .env, o de la ultima pose conocida."""
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if lat is not None and lon is not None:
        return (_num(lat, -90, 90, 0.0), _num(lon, -180, 180, 0.0))
    inst = get_instance()
    p = inst.pose or {}
    if p.get("lat") or p.get("lon"):
        return (float(p.get("lat") or 0.0), float(p.get("lon") or 0.0))
    hlat = os.getenv("HOME_LAT")
    hlon = os.getenv("HOME_LON")
    if hlat and hlon:
        return (_num(hlat, -90, 90, 0.0), _num(hlon, -180, 180, 0.0))
    return (0.0, 0.0)


@ar_bp.route("/api/ar/status", methods=["GET"])
def ar_status():
    return jsonify(
        {
            "ok": True,
            **get_instance().estado(),
            "rutas": [
                "/api/ar/scene",
                "/api/ar/anchors",
                "/api/ar/pose",
                "/api/ar/sensors",
                "/api/ar/gaze",
                "/api/ar/config",
                "/api/ar/plan",
            ],
        }
    )


@ar_bp.route("/api/ar/scene", methods=["GET"])
def ar_scene():
    return Response(get_instance().escena(), mimetype="text/html; charset=utf-8")


@ar_bp.route("/api/ar/anchors", methods=["GET"])
def ar_anchors_get():
    limite = int(_num(request.args.get("limit", 100), 1, 1000, 100))
    return jsonify(
        {"ok": True, "total": len(get_instance().anclas), "anclas": get_instance().listar(limite)}
    )


@ar_bp.route("/api/ar/anchors", methods=["POST"])
def ar_anchors_post():
    cuerpo = request.get_json(silent=True) or {}
    accion = _texto(cuerpo.get("accion"), 20, "crear").lower()
    if accion == "borrar":
        return jsonify({"ok": get_instance().borrar_ancla(_texto(cuerpo.get("id"), 40, ""))})
    if accion == "etiquetar":
        a = get_instance().etiquetar(_texto(cuerpo.get("id"), 40, ""), cuerpo)
        if not a:
            return jsonify({"ok": False, "error": "ancla no encontrada"}), 404
        return jsonify({"ok": True, "ancla": a.to_dict()})
    return jsonify(get_instance().crear_ancla(cuerpo))


@ar_bp.route("/api/ar/pose", methods=["GET"])
def ar_pose_get():
    inst = get_instance()
    return jsonify(
        {
            "ok": True,
            "pose": inst.pose or None,
            "muestras": len(inst.historial),
            "ultimas": inst.historial[-10:],
        }
    )


@ar_bp.route("/api/ar/pose", methods=["POST"])
def ar_pose_post():
    cuerpo = request.get_json(silent=True) or {}
    if not cuerpo:
        return jsonify({"ok": False, "error": "cuerpo vacio"}), 400
    return jsonify(get_instance().registrar_pose(cuerpo))


@ar_bp.route("/api/ar/sensors", methods=["GET"])
def ar_sensors():
    nombre = _texto(request.args.get("sensor"), 30, "orientation").lower()
    return jsonify(get_instance().sensores(nombre))


@ar_bp.route("/api/ar/gaze", methods=["GET"])
def ar_gaze():
    lat, lon = _coords()
    inst = get_instance()
    yaw = _num(request.args.get("yaw"), 0, 360, (inst.pose or {}).get("yaw", 0.0))
    pitch = _num(request.args.get("pitch"), -90, 90, (inst.pose or {}).get("pitch", 0.0))
    return jsonify(inst.mirada(lat, lon, yaw, pitch))


@ar_bp.route("/api/ar/config", methods=["GET"])
def ar_config_get():
    return jsonify({"ok": True, "config": dict(get_instance().cfg)})


@ar_bp.route("/api/ar/config", methods=["POST"])
def ar_config_post():
    cuerpo = request.get_json(silent=True) or {}
    return jsonify(get_instance().configurar(cuerpo))


@ar_bp.route("/api/ar/plan", methods=["GET"])
def ar_plan():
    puerto = int(_num(request.args.get("port", 5000), 1, 65535, 5000))
    return jsonify(get_instance().plan(puerto))


def register_ar_routes(app) -> int:
    """Registra las rutas de AR. Devuelve cuantas se han anadido."""
    app.register_blueprint(ar_bp)
    return 8


# --------------------------------------------------------------------------
#  Demo: tiene que funcionar en el PC, sin movil
# --------------------------------------------------------------------------
if __name__ == "__main__":
    st = ArStage()
    print("── E-18 · Daniela AR ──────────────────────────────")
    e = st.estado()
    print(f"anclas            : {e['anclas']}")
    print(f"gateway           : {e['gateway']['url'] or '(sin configurar)'}")
    print(f"token configurado : {e['gateway']['token_ok']}")

    print("\nancla en Puerta de Alcala (Madrid):")
    r = st.crear_ancla({"lat": 40.4199, "lon": -3.6889, "nombre": "Puerta de Alcala"})
    print(f"  -> {r.get('accion')}: {r.get('ancla', {}).get('nombre')}")

    print("\nsegunda visita al mismo sitio (a 20 m):")
    r2 = st.crear_ancla({"lat": 40.42008, "lon": -3.68885, "nombre": "Puerta de Alcala"})
    print(f"  -> {r2.get('accion')} | visitas={r2.get('ancla', {}).get('visitas')}")
    print(f"  -> {r2.get('nota', '')}")

    # Punto de vista 300 m al SUR del ancla: mirar al norte (yaw 0) debe verla
    # y mirar al sur (yaw 180) no. Con el observador encima del ancla el rumbo
    # no significaria nada.
    print("\nmirada desde 300 m al sur (el ancla queda al norte, yaw 0):")
    obs_lat, obs_lon = 40.41720, -3.6889
    st.registrar_pose({"yaw": 0, "pitch": 0, "origen": "demo", "lat": obs_lat, "lon": obs_lon})
    for yaw in (0, 90, 180):
        m = st.mirada(obs_lat, obs_lon, yaw, 0)
        print(f"  yaw {yaw:3d} -> en_cono={m['en_cono']} | {m['frase']}")
    m = st.mirada(obs_lat, obs_lon, 0, 80)
    print(f"  yaw   0, pitch 80 -> {m['frase']}")

    html = st.escena()
    print(f"\nescena generada  : {len(html)} bytes -> {SCENE_FILE}")
    print(f"lleva WebXR      : {'immersive-ar' in html}")
    print(f"contexto seguro  : avisado en la pagina: {'isSecureContext' in html}")

    p = st.plan(5000)
    print("\nplan para el movil:")
    for paso in p["pasos"]:
        print("  " + paso)
    print(f"  url: {p['url_movil']}")


class ARStage:
    pass