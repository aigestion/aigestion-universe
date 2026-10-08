#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
urban_nodes.py — E-12 · Daniela sabe donde estas y que hay alrededor
===================================================================

El problema
-----------
Daniela puede leer la bateria del movil, los SMS, la camara... pero no tiene
ni idea de donde estas. Si le preguntas "que tiempo hace" o "donde estoy",
no puede responder: nadie le ha dado nunca contexto del mundo real.

Y resulta que ese contexto es **gratis y sin clave**. Tres APIs publicas,
sin registro, sin tarjeta:

  - **Open-Meteo**  → tiempo actual y prevision (sin clave, sin limite duro).
  - **Nominatim**   → direccion a partir de coordenadas (OpenStreetMap).
  - **Overpass**    → que hay alrededor: bares, farmacias, paradas, cajeros...
  - **Wikipedia**   → que se sabe de este sitio (geosearch + extracto).

Que es un "nodo urbano"
-----------------------
Un sitio que Daniela ha aprendido. Si vuelves, lo reconoce: "llevas 14 visitas
aqui". Los nodos se guardan en disco y se emparejan por distancia: si caes a
menos de `RADIO_NODO` metros de uno conocido, es una visita; si no, es un nodo
nuevo. Asi Daniela construye un mapa de tu vida sin que nadie lo rellene a mano.

Reglas de seguridad
-------------------
1. **Los hosts estan escritos aqui, en una lista cerrada.** Nunca se acepta una
   URL que venga de la peticion HTTP: si se pudiera inyectar `url_base`,
   tendriamos un servidor haciendo peticiones a donde le diera la gana (SSRF).
   Lo unico que llega de fuera son numeros (lat, lon, radio) y se validan.
2. **Nominatim exige User-Agent propio** o te bloquea, y su politica es de
   **1 peticion por segundo**. Hay un limitador por host: si se salta, la
   IP acaba baneada y se corta el servicio para todos.
3. **Todo se cachea**. Geocodificar lo mismo cada vez que Daniela habla es
   malgastar el servicio y arriesgar el baneo.
4. Cero `os.system()`, cero `shell=True`: aqui todo es HTTP con `requests`.

Uso
---
    GET  /api/urban/status      resumen: nodos, cache, limite de peticiones
    GET  /api/urban/where       direccion a partir de lat/lon
    GET  /api/urban/weather     tiempo actual + prevision de hoy y manana
    GET  /api/urban/around      que hay alrededor (Overpass)
    GET  /api/urban/wikipedia   articulos del sitio
    GET  /api/urban/nodes       nodos conocidos
    POST /api/urban/nodes       visitar / crear / etiquetar / borrar
    GET  /api/urban/briefing    el resumen que diria Daniela
"""

from __future__ import annotations

import json
import math
import os
import re
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, request

# --------------------------------------------------------------------------
#  Rutas y constantes
# --------------------------------------------------------------------------
# Fase 2: el codigo vive en pixel/, los datos siguen en la raiz.
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "urban_nodes"
NODES_FILE = DATA_DIR / "nodos.json"
VISITS_FILE = DATA_DIR / "visitas.jsonl"

# Hosts permitidos. Lista CERRADA: nunca se construye una URL desde la entrada.
HOST_CLIMA = "https://api.open-meteo.com"
HOST_GEO = "https://nominatim.openstreetmap.org"
HOST_OVERPASS = "https://overpass-api.de"
HOST_WIKI = "https://es.wikipedia.org"

# Segundos minimos entre peticiones al mismo host (politica de Nominatim: 1/s)
PAUSA = {
    HOST_GEO: 1.1,
    HOST_OVERPASS: 1.0,
    HOST_CLIMA: 0.4,
    HOST_WIKI: 0.4,
}

# Cuanto aguanta cada cache (segundos)
TTL = {
    "geo": 86400,  # una direccion no cambia
    "clima": 600,  # 10 min
    "alrededor": 300,  # 5 min
    "wiki": 86400,
}

TIMEOUT = 12
TIMEOUT_OVERPASS = 25
RADIO_NODO = 60.0  # metros para considerar que es el mismo sitio
RADIO_MAX = 5000.0  # tope de seguridad para el radio de busqueda
USER_AGENT = "DanielaOS/2.0 (aig; contacto: usuario-local)"

# Codigos WMO de Open-Meteo traducidos
WMO = {
    0: "despejado",
    1: "casi despejado",
    2: "parcialmente nublado",
    3: "nublado",
    45: "niebla",
    48: "niebla con escarcha",
    51: "llovizna debil",
    53: "llovizna",
    55: "llovizna fuerte",
    56: "llovizna helada",
    57: "llovizna helada fuerte",
    61: "lluvia debil",
    63: "lluvia",
    65: "lluvia fuerte",
    66: "lluvia helada",
    67: "lluvia helada fuerte",
    71: "nieve debil",
    73: "nieve",
    75: "nieve fuerte",
    77: "granos de nieve",
    80: "chubascos",
    81: "chubascos fuertes",
    82: "chubascos torrenciales",
    85: "chubascos de nieve",
    86: "chubascos de nieve fuertes",
    95: "tormenta",
    96: "tormenta con granizo",
    99: "tormenta con granizo fuerte",
}


def _ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _num(v: Any, minimo: float, maximo: float, defecto: float) -> float:
    """Convierte a float validando rango. Nunca confia en lo que llega."""
    try:
        n = float(v)
    except (TypeError, ValueError):
        return defecto
    if math.isnan(n) or math.isinf(n):
        return defecto
    return max(minimo, min(maximo, n))


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros entre dos puntos."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# --------------------------------------------------------------------------
#  HTTP con limite de peticiones y cache
# --------------------------------------------------------------------------
class Cliente:
    """requests con tres cosas que importan: limite, cache y degradacion."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._ultima: Dict[str, float] = {}
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.peticiones = 0
        self.errores = 0
        self._sin_requests = False
        try:
            import requests  # type: ignore

            self._req = requests
        except Exception:  # noqa: BLE001
            self._req = None
            self._sin_requests = True

    def _esperar(self, host: str) -> None:
        with self._lock:
            pausa = PAUSA.get(host, 0.5)
            ultima = self._ultima.get(host, 0.0)
            falta = pausa - (time.time() - ultima)
            if falta > 0:
                time.sleep(falta)
            self._ultima[host] = time.time()

    def get(
        self,
        host: str,
        ruta: str,
        params: Dict[str, Any],
        clave_cache: Optional[str] = None,
        ttl: int = 0,
        timeout: int = TIMEOUT,
    ) -> Dict[str, Any]:
        """GET con cache opcional. Devuelve {'ok', 'datos', 'nota'}."""
        if clave_cache:
            with self._lock:
                hit = self._cache.get(clave_cache)
                if hit and (time.time() - hit[0]) < ttl:
                    return {"ok": True, "datos": hit[1], "nota": "cache"}

        if self._sin_requests or self._req is None:
            return {"ok": False, "datos": None, "nota": "requests no disponible"}

        url = f"{host}{ruta}"
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        try:
            self._esperar(host)
            self.peticiones += 1
            r = self._req.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code != 200:
                self.errores += 1
                return {"ok": False, "datos": None, "nota": f"HTTP {r.status_code}"}
            datos = r.json()
        except Exception as e:  # noqa: BLE001
            self.errores += 1
            return {"ok": False, "datos": None, "nota": f"{type(e).__name__}: {str(e)[:80]}"}

        if clave_cache:
            with self._lock:
                self._cache[clave_cache] = (time.time(), datos)
        return {"ok": True, "datos": datos, "nota": ""}

    def post(
        self,
        host: str,
        ruta: str,
        data: Dict[str, Any],
        clave_cache: Optional[str] = None,
        ttl: int = 0,
        timeout: int = TIMEOUT_OVERPASS,
    ) -> Dict[str, Any]:
        """POST (lo usa Overpass, que recibe la consulta en el cuerpo)."""
        if clave_cache:
            with self._lock:
                hit = self._cache.get(clave_cache)
                if hit and (time.time() - hit[0]) < ttl:
                    return {"ok": True, "datos": hit[1], "nota": "cache"}
        if self._sin_requests or self._req is None:
            return {"ok": False, "datos": None, "nota": "requests no disponible"}
        url = f"{host}{ruta}"
        headers = {"User-Agent": USER_AGENT}
        try:
            self._esperar(host)
            self.peticiones += 1
            r = self._req.post(url, data=data, headers=headers, timeout=timeout)
            if r.status_code != 200:
                self.errores += 1
                return {"ok": False, "datos": None, "nota": f"HTTP {r.status_code}"}
            datos = r.json()
        except Exception as e:  # noqa: BLE001
            self.errores += 1
            return {"ok": False, "datos": None, "nota": f"{type(e).__name__}: {str(e)[:80]}"}
        if clave_cache:
            with self._lock:
                self._cache[clave_cache] = (time.time(), datos)
        return {"ok": True, "datos": datos, "nota": ""}

    def limpiar_cache(self) -> int:
        with self._lock:
            n = len(self._cache)
            self._cache.clear()
            return n


# --------------------------------------------------------------------------
#  Nodo urbano
# --------------------------------------------------------------------------
@dataclass
class Nodo:
    id: str
    nombre: str
    tipo: str = "sitio"
    lat: float = 0.0
    lon: float = 0.0
    visitas: int = 1
    primera_vez: str = ""
    ultima_vez: str = ""
    notas: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UrbanNodes:
    """Registro de sitios conocidos + acceso a las APIs del mundo real."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.cliente = Cliente()
        self.nodos: Dict[str, Nodo] = {}
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._cargar()

    # ── persistencia ──────────────────────────────────────────
    def _cargar(self) -> None:
        if not NODES_FILE.exists():
            return
        try:
            raw = json.loads(NODES_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return
        for d in raw:
            try:
                self.nodos[d["id"]] = Nodo(**d)
            except Exception:  # noqa: BLE001
                continue

    def guardar(self) -> None:
        with self._lock:
            try:
                NODES_FILE.write_text(
                    json.dumps(
                        [n.to_dict() for n in self.nodos.values()], ensure_ascii=False, indent=2
                    ),
                    encoding="utf-8",
                )
            except Exception:  # noqa: BLE001
                pass

    def _registrar_visita(self, nodo: Nodo, nueva: bool) -> None:
        try:
            with VISITS_FILE.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "ts": _ahora(),
                            "id": nodo.id,
                            "nombre": nodo.nombre,
                            "lat": nodo.lat,
                            "lon": nodo.lon,
                            "nuevo": nueva,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except Exception:  # noqa: BLE001
            pass

    # ── nodos ─────────────────────────────────────────────────
    def _id_para(self, lat: float, lon: float) -> str:
        return f"n{abs(round(lat * 1e4)):07d}{abs(round(lon * 1e4)):07d}"

    def cercano(self, lat: float, lon: float) -> Optional[Nodo]:
        mejor, dist = None, RADIO_NODO
        with self._lock:
            for n in self.nodos.values():
                d = _haversine(lat, lon, n.lat, n.lon)
                if d <= dist:
                    mejor, dist = n, d
        return mejor

    def visitar(
        self,
        lat: float,
        lon: float,
        nombre: str = "",
        tipo: str = "sitio",
        nota: str = "",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Si el sitio ya existe, cuenta una visita. Si no, lo crea."""
        with self._lock:
            existente = self.cercano(lat, lon)
            if existente is not None:
                existente.visitas += 1
                existente.ultima_vez = _ahora()
                if nota:
                    existente.notas.append(f"{_ahora()}: {nota}")
                for t in tags or []:
                    if t and t not in existente.tags:
                        existente.tags.append(t)
                if nombre and not existente.nombre:
                    existente.nombre = nombre
                self.guardar()
                self._registrar_visita(existente, False)
                return {"nuevo": False, "nodo": existente.to_dict()}

            nid = self._id_para(lat, lon)
            nodo = Nodo(
                id=nid,
                nombre=nombre or f"Sitio {lat:.4f},{lon:.4f}",
                tipo=tipo,
                lat=lat,
                lon=lon,
                visitas=1,
                primera_vez=_ahora(),
                ultima_vez=_ahora(),
                notas=[f"{_ahora()}: {nota}"] if nota else [],
                tags=list(tags or []),
            )
            self.nodos[nid] = nodo
            self.guardar()
            self._registrar_visita(nodo, True)
            return {"nuevo": True, "nodo": nodo.to_dict()}

    def listar(self, limite: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            nodos = sorted(self.nodos.values(), key=lambda n: (-n.visitas, n.ultima_vez))
        return [n.to_dict() for n in nodos[:limite]]

    def etiquetar(
        self,
        nid: str,
        nombre: Optional[str] = None,
        nota: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Nodo]:
        with self._lock:
            n = self.nodos.get(nid)
            if n is None:
                return None
            if nombre:
                n.nombre = nombre
            if nota:
                n.notas.append(f"{_ahora()}: {nota}")
            for t in tags or []:
                if t and t not in n.tags:
                    n.tags.append(t)
            self.guardar()
            return n

    def borrar(self, nid: str) -> bool:
        with self._lock:
            if nid not in self.nodos:
                return False
            del self.nodos[nid]
            self.guardar()
            return True

    # ── APIs del mundo real ───────────────────────────────────
    def donde_estoy(self, lat: float, lon: float) -> Dict[str, Any]:
        r = self.cliente.get(
            HOST_GEO,
            "/reverse",
            {
                "format": "jsonv2",
                "lat": f"{lat:.6f}",
                "lon": f"{lon:.6f}",
                "zoom": 18,
                "addressdetails": 1,
            },
            clave_cache=f"geo:{lat:.4f},{lon:.4f}",
            ttl=TTL["geo"],
        )
        if not r["ok"]:
            return {"ok": False, "nota": r["nota"], "lat": lat, "lon": lon}
        d = r["datos"]
        dirs = d.get("address") or {}
        return {
            "ok": True,
            "nota": r["nota"],
            "lat": lat,
            "lon": lon,
            "nombre": d.get("name") or d.get("display_name", "").split(",")[0],
            "direccion": d.get("display_name", ""),
            "categoria": d.get("category", ""),
            "tipo": d.get("type", ""),
            "calle": dirs.get("road", "") or dirs.get("pedestrian", ""),
            "numero": dirs.get("house_number", ""),
            "barrio": (
                dirs.get("suburb") or dirs.get("neighbourhood") or dirs.get("quarter") or ""
            ),
            "ciudad": (dirs.get("city") or dirs.get("town") or dirs.get("village") or ""),
            "provincia": dirs.get("state", ""),
            "pais": dirs.get("country", ""),
            "cp": dirs.get("postcode", ""),
        }

    def clima(self, lat: float, lon: float) -> Dict[str, Any]:
        r = self.cliente.get(
            HOST_CLIMA,
            "/v1/forecast",
            {
                "latitude": f"{lat:.4f}",
                "longitude": f"{lon:.4f}",
                "current": (
                    "temperature_2m,relative_humidity_2m,"
                    "apparent_temperature,is_day,precipitation,"
                    "weather_code,wind_speed_10m"
                ),
                "daily": (
                    "weather_code,temperature_2m_max,"
                    "temperature_2m_min,precipitation_probability_max"
                ),
                "timezone": "auto",
                "forecast_days": 2,
            },
            clave_cache=f"clima:{lat:.2f},{lon:.2f}",
            ttl=TTL["clima"],
        )
        if not r["ok"]:
            return {"ok": False, "nota": r["nota"]}
        d = r["datos"]
        cur = d.get("current") or {}
        dia = d.get("daily") or {}
        codigo = cur.get("weather_code")
        out: Dict[str, Any] = {
            "ok": True,
            "nota": r["nota"],
            "temperatura": cur.get("temperature_2m"),
            "sensacion": cur.get("apparent_temperature"),
            "humedad": cur.get("relative_humidity_2m"),
            "viento": cur.get("wind_speed_10m"),
            "precipitacion": cur.get("precipitation"),
            "es_de_dia": bool(cur.get("is_day")),
            "codigo": codigo,
            "descripcion": WMO.get(codigo, "sin datos") if isinstance(codigo, int) else "",
            "unidades": (d.get("current_units") or {}),
        }
        fechas = dia.get("time") or []
        if len(fechas) >= 2:
            out["manana"] = {
                "fecha": fechas[1],
                "max": (dia.get("temperature_2m_max") or [None, None])[1],
                "min": (dia.get("temperature_2m_min") or [None, None])[1],
                "lluvia": (dia.get("precipitation_probability_max") or [None, None])[1],
                "descripcion": WMO.get((dia.get("weather_code") or [None, None])[1], ""),
            }
        return out

    def alrededor(
        self, lat: float, lon: float, radio: float = 400.0, limite: int = 12
    ) -> Dict[str, Any]:
        """Que hay cerca. Overpass entiende la consulta en el cuerpo."""
        radio = _num(radio, 50, RADIO_MAX, 400)
        consulta = (
            f"[out:json][timeout:20];"
            f"node(around:{int(radio)},{lat:.6f},{lon:.6f})[amenity];"
            f"out body {int(limite) * 3};"
        )
        r = self.cliente.post(
            HOST_OVERPASS,
            "/api/interpreter",
            {"data": consulta},
            clave_cache=f"alr:{lat:.3f},{lon:.3f},{int(radio)}",
            ttl=TTL["alrededor"],
        )
        if not r["ok"]:
            return {"ok": False, "nota": r["nota"], "lugares": []}
        elementos = (r["datos"] or {}).get("elements") or []
        sitios: List[Dict[str, Any]] = []
        for e in elementos:
            tags = e.get("tags") or {}
            nombre = tags.get("name")
            if not nombre:
                continue
            elat, elon = e.get("lat"), e.get("lon")
            dist = None
            if elat is not None and elon is not None:
                dist = round(_haversine(lat, lon, float(elat), float(elon)))
            sitios.append(
                {
                    "nombre": nombre,
                    "tipo": tags.get("amenity", ""),
                    "distancia_m": dist,
                    "abierto": tags.get("opening_hours", ""),
                }
            )
        sitios.sort(key=lambda s: (s["distancia_m"] is None, s["distancia_m"] or 0))
        return {"ok": True, "nota": r["nota"], "radio_m": radio, "lugares": sitios[:limite]}

    def wikipedia(self, lat: float, lon: float, limite: int = 5) -> Dict[str, Any]:
        r = self.cliente.get(
            HOST_WIKI,
            "/w/api.php",
            {
                "action": "query",
                "format": "json",
                "list": "geosearch",
                "gscoord": f"{lat:.5f}|{lon:.5f}",
                "gsradius": 3000,
                "gslimit": limite,
            },
            clave_cache=f"wiki:{lat:.3f},{lon:.3f}",
            ttl=TTL["wiki"],
        )
        if not r["ok"]:
            return {"ok": False, "nota": r["nota"], "articulos": []}
        geo = ((r["datos"] or {}).get("query") or {}).get("geosearch") or []
        arts = [
            {
                "titulo": g.get("title", ""),
                "distancia_m": g.get("dist"),
                "resumen": re.sub(r"<[^>]+>", "", g.get("snippet", "") or "")[:220],
            }
            for g in geo
        ]
        return {"ok": True, "nota": r["nota"], "articulos": arts}

    def briefing(self, lat: float, lon: float, radio: float = 400.0) -> Dict[str, Any]:
        """Lo que Daniela diria: donde estas, que tiempo hace, que hay cerca."""
        donde = self.donde_estoy(lat, lon)
        clima = self.clima(lat, lon)
        conocido = self.cercano(lat, lon)

        texto: List[str] = []
        if donde.get("ok"):
            sitio = donde.get("nombre") or donde.get("calle") or "aqui"
            texto.append(f"Estas en {sitio}")
            if donde.get("barrio"):
                texto.append(f", en {donde['barrio']}")
            if donde.get("ciudad"):
                texto.append(f" ({donde['ciudad']})")
        else:
            texto.append(f"Estas en {lat:.4f}, {lon:.4f}")
        if clima.get("ok") and clima.get("temperatura") is not None:
            texto.append(
                f". Hace {clima['temperatura']} grados"
                f"{', ' + clima['descripcion'] if clima.get('descripcion') else ''}"
            )
        if conocido is not None:
            texto.append(f". Conozco este sitio: {conocido.visitas} visitas")
            if conocido.notas:
                texto.append(f". Ultima nota: {conocido.notas[-1]}")
        texto.append(".")

        return {
            "ok": True,
            "lat": lat,
            "lon": lon,
            "donde": donde,
            "clima": clima,
            "nodo_conocido": conocido.to_dict() if conocido else None,
            "frase": "".join(texto),
            "radio_m": radio,
        }

    def estado(self) -> Dict[str, Any]:
        return {
            "nodos": len(self.nodos),
            "visitas_totales": sum(n.visitas for n in self.nodos.values()),
            "peticiones": self.cliente.peticiones,
            "errores": self.cliente.errores,
            "cache": len(self.cliente._cache),
            "requests": not self.cliente._sin_requests,
            "hosts": list(PAUSA),
            "cuando": _ahora(),
        }


_instancia: Optional[UrbanNodes] = None
_lock = threading.RLock()


def get_instance() -> UrbanNodes:
    global _instancia
    with _lock:
        if _instancia is None:
            _instancia = UrbanNodes()
        return _instancia


# --------------------------------------------------------------------------
#  Rutas
# --------------------------------------------------------------------------
urban_bp = Blueprint("urban_nodes", __name__)


def _coords() -> Tuple[float, float]:
    """Lee lat/lon de la query, del .env, o del ultimo sitio conocido."""
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if lat is not None and lon is not None:
        return (_num(lat, -90, 90, 0.0), _num(lon, -180, 180, 0.0))
    dlat = os.getenv("HOME_LAT")
    dlon = os.getenv("HOME_LON")
    if dlat and dlon:
        return (_num(dlat, -90, 90, 0.0), _num(dlon, -180, 180, 0.0))
    return (0.0, 0.0)


@urban_bp.route("/api/urban/status", methods=["GET"])
def urban_status():
    return jsonify(
        {
            "ok": True,
            **get_instance().estado(),
            "rutas": [
                "/api/urban/where",
                "/api/urban/weather",
                "/api/urban/around",
                "/api/urban/wikipedia",
                "/api/urban/nodes",
                "/api/urban/briefing",
            ],
        }
    )


@urban_bp.route("/api/urban/where", methods=["GET"])
def urban_where():
    lat, lon = _coords()
    if not lat and not lon:
        return (
            jsonify({"ok": False, "error": "falta lat/lon (o HOME_LAT/HOME_LON en el .env)"}),
            400,
        )
    return jsonify(get_instance().donde_estoy(lat, lon))


@urban_bp.route("/api/urban/weather", methods=["GET"])
def urban_weather():
    lat, lon = _coords()
    if not lat and not lon:
        return jsonify({"ok": False, "error": "falta lat/lon"}), 400
    return jsonify(get_instance().clima(lat, lon))


@urban_bp.route("/api/urban/around", methods=["GET"])
def urban_around():
    lat, lon = _coords()
    if not lat and not lon:
        return jsonify({"ok": False, "error": "falta lat/lon"}), 400
    radio = _num(request.args.get("radius", 400), 50, RADIO_MAX, 400)
    limite = int(_num(request.args.get("limit", 12), 1, 50, 12))
    return jsonify(get_instance().alrededor(lat, lon, radio, limite))


@urban_bp.route("/api/urban/wikipedia", methods=["GET"])
def urban_wikipedia():
    lat, lon = _coords()
    if not lat and not lon:
        return jsonify({"ok": False, "error": "falta lat/lon"}), 400
    limite = int(_num(request.args.get("limit", 5), 1, 20, 5))
    return jsonify(get_instance().wikipedia(lat, lon, limite))


@urban_bp.route("/api/urban/nodes", methods=["GET"])
def urban_nodes_get():
    limite = int(_num(request.args.get("limit", 100), 1, 1000, 100))
    return jsonify(
        {"ok": True, "total": len(get_instance().nodos), "nodos": get_instance().listar(limite)}
    )


@urban_bp.route("/api/urban/nodes", methods=["POST"])
def urban_nodes_post():
    """Crear/visitar (accion=visitar), etiquetar, o borrar."""
    cuerpo = request.get_json(silent=True) or {}
    accion = (cuerpo.get("accion") or "visitar").lower()

    if accion == "borrar":
        nid = str(cuerpo.get("id", ""))
        return jsonify({"ok": get_instance().borrar(nid)})

    if accion == "etiquetar":
        nid = str(cuerpo.get("id", ""))
        n = get_instance().etiquetar(
            nid, cuerpo.get("nombre"), cuerpo.get("nota"), cuerpo.get("tags")
        )
        if n is None:
            return jsonify({"ok": False, "error": "nodo no encontrado"}), 404
        return jsonify({"ok": True, "nodo": n.to_dict()})

    lat = _num(cuerpo.get("lat", 0), -90, 90, 0.0)
    lon = _num(cuerpo.get("lon", 0), -180, 180, 0.0)
    if not lat and not lon:
        return jsonify({"ok": False, "error": "falta lat/lon"}), 400
    r = get_instance().visitar(
        lat,
        lon,
        nombre=cuerpo.get("nombre", ""),
        tipo=cuerpo.get("tipo", "sitio"),
        nota=cuerpo.get("nota", ""),
        tags=cuerpo.get("tags"),
    )
    return jsonify({"ok": True, **r})


@urban_bp.route("/api/urban/briefing", methods=["GET"])
def urban_briefing():
    lat, lon = _coords()
    if not lat and not lon:
        return jsonify({"ok": False, "error": "falta lat/lon"}), 400
    radio = _num(request.args.get("radius", 400), 50, RADIO_MAX, 400)
    return jsonify(get_instance().briefing(lat, lon, radio))


def register_urban_routes(app) -> int:
    app.register_blueprint(urban_bp)
    print(
        "[Urban Nodes] Routes registered: /api/urban/* "
        "(status, where, weather, around, wikipedia, nodes, briefing)"
    )
    return 8


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo() -> None:
    print("=" * 66)
    print("E-12 · urban_nodes — demo")
    print("=" * 66)
    u = get_instance()
    # Puerta de Alcala, Madrid: un sitio con de todo alrededor
    lat, lon = 40.4206, -3.6889

    print("\n-- Donde estoy (Nominatim) --")
    d = u.donde_estoy(lat, lon)
    if d.get("ok"):
        print(f"  {d.get('nombre')} | {d.get('calle')} {d.get('numero')}")
        print(
            f"  barrio={d.get('barrio')} ciudad={d.get('ciudad')} "
            f"cp={d.get('cp')} ({d.get('nota') or 'red'})"
        )
    else:
        print(f"  fallo: {d.get('nota')}")

    print("\n-- Tiempo (Open-Meteo) --")
    c = u.clima(lat, lon)
    if c.get("ok"):
        print(
            f"  {c.get('temperatura')} C (sensacion {c.get('sensacion')}), "
            f"{c.get('descripcion')}, humedad {c.get('humedad')}%"
        )
        if c.get("manana"):
            m = c["manana"]
            print(f"  manana: {m.get('min')}-{m.get('max')} C, " f"lluvia {m.get('lluvia')}%")
    else:
        print(f"  fallo: {c.get('nota')}")

    print("\n-- Alrededor (Overpass) --")
    a = u.alrededor(lat, lon, 350, 8)
    for s in a.get("lugares", [])[:8]:
        print(f"  {s['distancia_m']:>5} m  {s['tipo']:<14} {s['nombre']}")
    if not a.get("lugares"):
        print(f"  (ninguno: {a.get('nota')})")

    print("\n-- Wikipedia --")
    w = u.wikipedia(lat, lon, 4)
    for x in w.get("articulos", [])[:4]:
        print(f"  {x['distancia_m']:>5} m  {x['titulo']}")

    print("\n-- Nodos (memoria de sitios) --")
    r1 = u.visitar(lat, lon, nombre="Puerta de Alcala", tipo="monumento", nota="primera vez")
    r2 = u.visitar(lat + 0.0002, lon + 0.0002)
    print(f"  1a vez: nuevo={r1['nuevo']} visitas={r1['nodo']['visitas']}")
    print(
        f"  2a vez: nuevo={r2['nuevo']} visitas={r2['nodo']['visitas']} "
        f"(reconocio el sitio a pocos metros)"
    )
    lejos = u.visitar(40.4168, -3.7038, nombre="Puerta del Sol")
    print(f"  otro sitio: nuevo={lejos['nuevo']} -> {lejos['nodo']['nombre']}")

    print("\n-- Briefing (lo que diria Daniela) --")
    print("  " + u.briefing(lat, lon)["frase"])

    print("\n-- Estado --")
    e = u.estado()
    print(
        f"  nodos={e['nodos']} peticiones={e['peticiones']} "
        f"errores={e['errores']} cache={e['cache']}"
    )
    print("\n" + "=" * 66)


if __name__ == "__main__":
    _demo()