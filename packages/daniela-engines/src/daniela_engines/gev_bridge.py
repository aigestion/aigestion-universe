#!/usr/bin/env python3
"""
GEV Bridge — Daniela <-> God's Eye View
========================================
God's Eye View (localhost:4173) es un globo 3D con 15+ feeds publicos en vivo.
Este modulo es la **frontera** entre Daniela y esa app: no importa nada de GEV,
solo habla con su URL. Si GEV cambia por dentro, esto sigue funcionando.

Dos capacidades:

  1. ENLACES PROFUNDOS — construye URLs que abren el globo ya enfocado en un
     punto, con el estilo visual adecuado. Daniela "muestra" en vez de describir.
     Formato real (src/sharelink.js de GEV):
       #lat=..&lon=..&alt=..&heading=..&pitch=..&style=..&map=photoreal
     Estilos validos: normal | crt | nvg | flir | anime | noir | snow

  2. CLIENTE HTTP — lee los feeds vivos del proxy de GEV (que ya trae gobernador
     de creditos, presupuesto de tiles, cache de TLEs y proteccion SSRF) para
     que intel_engine y el motor de geocercas razonen sobre telemetria real.

Rutas verificadas del proxy de GEV:
  /api/opensky        snapshot global de vuelos (formato OpenSky, 18 campos)
  /api/opensky-track  traza de una aeronave
  /api/adsblol/mil    vuelos militares
  /api/ais-live       barcos en vivo           (requiere clave AISStream)
  /api/firms          incendios activos        (requiere clave NASA FIRMS)
  /api/cctv           camaras publicas
  /api/celestrak      catalogo de satelites
  /api/launches       misiones espaciales
  /api/route          rutas (OSRM)
  /api/geocode        geocodificacion
  /api/status         salud del servidor

Los sismos NO pasan por el proxy: GEV los lee directos de USGS (sin clave).

Coste: $0. Ninguna de las capas usadas aqui necesita clave de pago.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import urllib.parse
import webbrowser
from collections.abc import Sequence
from typing import Any

import requests

# ── Config ───────────────────────────────────────────────────

GEV_BASE = os.getenv("GEV_BASE_URL", "http://localhost:4173").rstrip("/")
REQUEST_TIMEOUT = int(os.getenv("GEV_TIMEOUT", "20"))
USER_AGENT = "DanielaOS-GEV-Bridge/1.0"

USGS_ALL_DAY = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
)

# Estilos de GEV: token -> nombre legible
ESTILOS = {
    "normal": "Normal",
    "crt": "Retro CRT",
    "nvg": "Vision nocturna",
    "flir": "Termico FLIR",
    "anime": "Anime",
    "noir": "Noir",
    "snow": "Nieve",
}

# Contexto -> estilo. Daniela elige el look segun lo que va a mostrar.
ESTILO_POR_CONTEXTO = {
    "incendio": "flir",
    "fuego": "flir",
    "sismo": "flir",
    "terremoto": "flir",
    "calor": "flir",
    "noche": "nvg",
    "nocturno": "nvg",
    "vigilancia": "nvg",
    "militar": "nvg",
    "barco": "normal",
    "buque": "normal",
    "vuelo": "normal",
    "avion": "normal",
    "satelite": "normal",
    "camara": "normal",
    "ciudad": "normal",
    "retro": "crt",
    "antiguo": "crt",
    "archivo": "crt",
}


# ── Geometria ────────────────────────────────────────────────


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia haversine en kilometros entre dos puntos."""
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def bbox_alrededor(lat: float, lon: float, radio_km: float) -> tuple[float, float, float, float]:
    """Caja (smin, wmin, nmax, emax) que contiene un circulo de radio_km."""
    dlat = radio_km / 111.32
    coslat = max(math.cos(math.radians(lat)), 1e-6)
    dlon = radio_km / (111.32 * coslat)
    return (lat - dlat, lon - dlon, lat + dlat, lon + dlon)


# ── 1. Enlaces profundos ─────────────────────────────────────


def gev_link(
    lat: float,
    lon: float,
    alt: float = 1500,
    heading: float = 0,
    pitch: float = -35,
    style: str = "normal",
    map_stack: str = "photoreal",
) -> str:
    """Devuelve un enlace profundo al globo, enfocado y con estilo.

    >>> gev_link(41.39, 2.16, alt=900, style="flir")
    'http://localhost:4173/#lat=41.39000&lon=2.16000&alt=900&...&style=flir&map=photoreal'
    """
    if style not in ESTILOS:
        raise ValueError(f"estilo desconocido: {style!r}. Validos: {sorted(ESTILOS)}")
    params = {
        "lat": f"{float(lat):.5f}",
        "lon": f"{float(lon):.5f}",
        "alt": int(alt),
        "heading": int(heading),
        "pitch": int(pitch),
        "style": style,
        "map": map_stack,
    }
    return f"{GEV_BASE}/#{urllib.parse.urlencode(params)}"


def estilo_para(contexto: str) -> str:
    """Traduce un contexto humano ('incendio', 'noche') a un token de estilo."""
    return ESTILO_POR_CONTEXTO.get((contexto or "").strip().lower(), "normal")


def mostrar(lat: float, lon: float, contexto: str = "", **kw: Any) -> str:
    """Abre el globo en el navegador. Devuelve el enlace por si hay que citarlo."""
    if contexto and "style" not in kw:
        kw["style"] = estilo_para(contexto)
    url = gev_link(lat, lon, **kw)
    try:
        webbrowser.open(url)
    except Exception:
        pass  # sin navegador (Termux, headless): el enlace se devuelve igual
    return url


# ── 2. Cliente HTTP ──────────────────────────────────────────


class GevClient:
    """Cliente del proxy local de GEV. Solo stdlib + requests."""

    def __init__(self, base: str = GEV_BASE, timeout: int = REQUEST_TIMEOUT):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self._s = requests.Session()
        self._s.headers.update({"User-Agent": USER_AGENT})

    # -- infraestructura --

    def get_json(self, path: str, **params: Any) -> Any:
        """GET a una ruta del proxy. Lanza requests.HTTPError si falla."""
        url = f"{self.base}{path}"
        r = self._s.get(url, params=params or None, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def is_up(self) -> bool:
        """True si GEV responde. Nunca lanza: es un chequeo de salud."""
        for path in ("/api/status", "/"):
            try:
                r = self._s.get(f"{self.base}{path}", timeout=5)
                if r.status_code < 500:
                    return True
            except Exception:
                continue
        return False

    # -- feeds --

    def vuelos(self) -> list[dict[str, Any]]:
        """Snapshot global de aeronaves, normalizado a dicts legibles.

        OpenSky devuelve listas de 18 campos:
          [icao24, callsign, country, t_pos, t_contact, lon, lat, alt,
           on_ground, velocity, true_track, vertical_rate, sensors,
           geo_alt, squawk, spi, position_source, ...]
        """
        raw = self.get_json("/api/opensky")
        estados = raw.get("states") if isinstance(raw, dict) else raw
        out: list[dict[str, Any]] = []
        for s in estados or []:
            if not isinstance(s, (list, tuple)) or len(s) < 11:
                continue
            lon, lat = s[5], s[6]
            if lat is None or lon is None:
                continue
            out.append(
                {
                    "icao24": s[0],
                    "callsign": (s[1] or "").strip() or None,
                    "pais": s[2],
                    "lon": float(lon),
                    "lat": float(lat),
                    "alt_m": s[7],
                    "en_tierra": bool(s[8]),
                    "vel_ms": s[9],
                    "rumbo": s[10],
                }
            )
        return out

    def vuelos_cerca(
        self, lat: float, lon: float, radio_km: float = 50, limite: int = 25
    ) -> list[dict[str, Any]]:
        """Aeronaves dentro de radio_km, ordenadas por cercania."""
        cerca: list[dict[str, Any]] = []
        for v in self.vuelos():
            d = distancia_km(lat, lon, v["lat"], v["lon"])
            if d <= radio_km:
                v["dist_km"] = round(d, 2)
                cerca.append(v)
        cerca.sort(key=lambda x: x["dist_km"])
        return cerca[:limite]

    def militares(self) -> Any:
        """Trafico militar (adsb.lol)."""
        return self.get_json("/api/adsblol/mil")

    def barcos(self) -> Any:
        """Barcos en vivo. Requiere clave AISStream en GEV."""
        return self.get_json("/api/ais-live")

    def incendios(self) -> Any:
        """Incendios activos. Requiere clave NASA FIRMS en GEV."""
        return self.get_json("/api/firms")

    def camaras(self) -> Any:
        """Camaras CCTV publicas."""
        return self.get_json("/api/cctv")

    def satelites(self) -> Any:
        """Catalogo de satelites (CelesTrak)."""
        return self.get_json("/api/celestrak")

    def lanzamientos(self) -> Any:
        """Misiones espaciales de los ultimos/Proximos 30 dias."""
        return self.get_json("/api/launches")

    def ruta(self, origen: str, destino: str, modo: str = "driving") -> Any:
        """Ruta entre dos puntos (OSRM). modo: driving|walking|cycling."""
        return self.get_json("/api/route", from_=origen, to=destino, mode=modo)

    def geocodificar(self, texto: str) -> Any:
        """Toponimo -> coordenadas."""
        return self.get_json("/api/geocode", q=texto)

    # -- sismos (directo a USGS, sin proxy ni clave) --

    @staticmethod
    def sismos(min_mag: float = 0.0, limite: int = 50) -> list[dict[str, Any]]:
        """Sismos de las ultimas 24 h desde USGS, filtrados por magnitud."""
        r = requests.get(USGS_ALL_DAY, timeout=REQUEST_TIMEOUT,
                         headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        out: list[dict[str, Any]] = []
        for f in r.json().get("features", []):
            p = f.get("properties", {})
            g = f.get("geometry", {}).get("coordinates") or []
            mag = p.get("mag")
            if mag is None or mag < min_mag or len(g) < 2:
                continue
            out.append(
                {
                    "mag": mag,
                    "lugar": p.get("place"),
                    "hora_ms": p.get("time"),
                    "lon": g[0],
                    "lat": g[1],
                    "prof_km": g[2] if len(g) > 2 else None,
                    "url": p.get("url"),
                }
            )
        out.sort(key=lambda x: x["mag"], reverse=True)
        return out[:limite]

    @staticmethod
    def sismos_cerca(lat: float, lon: float, radio_km: float = 500,
                     min_mag: float = 4.0) -> list[dict[str, Any]]:
        """Sismos recientes dentro de radio_km."""
        out = []
        for s in GevClient.sismos(min_mag=min_mag, limite=500):
            d = distancia_km(lat, lon, s["lat"], s["lon"])
            if d <= radio_km:
                s["dist_km"] = round(d, 1)
                out.append(s)
        out.sort(key=lambda x: x["dist_km"])
        return out


# ── Helpers de presentacion ──────────────────────────────────


def resumen_vuelo(v: dict[str, Any]) -> str:
    """Linea legible de una aeronave."""
    quien = v.get("callsign") or v.get("icao24") or "?"
    alt = v.get("alt_m")
    alt_txt = f"{alt:.0f} m" if isinstance(alt, (int, float)) else "alt ?"
    return f"{quien} ({v.get('pais','?')}) a {v.get('dist_km','?')} km, {alt_txt}"


def resumen_sismo(s: dict[str, Any]) -> str:
    """Linea legible de un sismo."""
    return f"M{s['mag']} — {s.get('lugar')} ({s.get('dist_km','?')} km)"


# ── CLI ──────────────────────────────────────────────────────


def _main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Puente Daniela <-> God's Eye View")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("estado", help="comprobar si GEV responde")

    a = sub.add_parser("link", help="generar enlace profundo")
    a.add_argument("lat", type=float)
    a.add_argument("lon", type=float)
    a.add_argument("--alt", type=float, default=1500)
    a.add_argument("--pitch", type=float, default=-35)
    a.add_argument("--contexto", default="")
    a.add_argument("--abrir", action="store_true")

    b = sub.add_parser("vuelos", help="aeronaves cerca de un punto")
    b.add_argument("lat", type=float)
    b.add_argument("lon", type=float)
    b.add_argument("--radio", type=float, default=50)
    b.add_argument("--limite", type=int, default=15)

    c = sub.add_parser("sismos", help="sismos recientes (USGS)")
    c.add_argument("--min-mag", type=float, default=4.0)
    c.add_argument("--lat", type=float)
    c.add_argument("--lon", type=float)
    c.add_argument("--radio", type=float, default=500)

    args = p.parse_args(argv)

    if args.cmd == "estado":
        cli = GevClient()
        up = cli.is_up()
        print(f"GEV en {cli.base}: {'ARRIBA' if up else 'CAIDO'}")
        return 0 if up else 1

    if args.cmd == "link":
        url = gev_link(args.lat, args.lon, alt=args.alt, pitch=args.pitch,
                       style=estilo_para(args.contexto))
        print(url)
        if args.abrir:
            webbrowser.open(url)
        return 0

    if args.cmd == "vuelos":
        cli = GevClient()
        for v in cli.vuelos_cerca(args.lat, args.lon, args.radio, args.limite):
            print(resumen_vuelo(v))
        return 0

    if args.cmd == "sismos":
        if args.lat is not None and args.lon is not None:
            filas = GevClient.sismos_cerca(args.lat, args.lon, args.radio, args.min_mag)
        else:
            filas = GevClient.sismos(min_mag=args.min_mag, limite=20)
        for s in filas:
            print(resumen_sismo(s))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(_main())
