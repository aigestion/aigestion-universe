"""
gev.capas_usuario — Capas personalizadas por usuario en el visor GEV
=====================================================================
Cada usuario (tenant) puede tener su propia configuración de capas:
  - Qué capas están activas por defecto
  - AOI (Área de Interés) por defecto
  - Estilo visual y tipo de mapa
  - Última búsqueda realizada

Daniela, al procesar una solicitud del usuario, devuelve:
  - La capa a activar
  - El destino (lat/lon/radio) para volar el globo
  - Contexto para enriquecer la respuesta
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from osint import COLORES
from osint import capas as catalogar_capas

_DIR = os.path.dirname(os.path.abspath(__file__))
_DATOS = os.path.join(_DIR, "data")

_ESTILOS_VALIDOS = {"normal", "crt", "nvg", "flir", "anime", "noir", "snow"}
_MAPAS_VALIDOS = {"satellite", "dark", "light", "terrain"}


def _dir_datos() -> str:
    os.makedirs(_DATOS, exist_ok=True)
    return _DATOS


def _ruta_usuario(slug: str) -> str:
    """Ruta segura para el fichero de capas del usuario."""
    seguro = re.sub(r"[^a-z0-9_-]", "", (slug or "").lower())[:64] or "anon"
    return os.path.join(_dir_datos(), f"capas_{seguro}.json")


def config_por_defecto() -> dict[str, Any]:
    """Configuración inicial: todas las capas disponibles, AOI en la sede."""
    cat = catalogar_capas()
    capas_ok = [c["capa"] for c in cat.get("capas", []) if c.get("estado") == "ok"]
    return {
        "capas_activas": capas_ok,
        "aoi": {"lat": None, "lon": None, "radio_km": 150.0},
        "estilo": "normal",
        "mapa": "satellite",
        "ultima_busqueda": None,
        "ts": time.time(),
    }


def obtener(slug: str) -> dict[str, Any]:
    """Capas del usuario. Si no existe, devuelve la config por defecto."""
    ruta = _ruta_usuario(slug)
    if os.path.exists(ruta):
        try:
            with open(ruta, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return config_por_defecto()


def guardar(slug: str, config: dict[str, Any]) -> dict[str, Any]:
    """Guarda la configuración de capas del usuario."""
    capas_validas = set(COLORES.keys())
    config["capas_activas"] = [c for c in config.get("capas_activas", []) if c in capas_validas]
    config["estilo"] = config.get("estilo", "normal")
    if config["estilo"] not in _ESTILOS_VALIDOS:
        config["estilo"] = "normal"
    config["mapa"] = config.get("mapa", "satellite")
    if config["mapa"] not in _MAPAS_VALIDOS:
        config["mapa"] = "satellite"
    config["ts"] = time.time()

    aoi = config.get("aoi") or {}
    config["aoi"] = {
        "lat": aoi.get("lat"),
        "lon": aoi.get("lon"),
        "radio_km": float(aoi.get("radio_km") or 150.0),
    }

    ruta = _ruta_usuario(slug)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return config


_BUSQUEDA_PATRON = re.compile(
    r"""
    (?P<capa>sismos|terremotos|vuelos|aviones|aeronaves|militares|
            incendios|fuegos|barcos|navios|cámaras|camaras|cctv)
    \s*
    (?:(?:cerca\s+de|en|a)\s+)?
    (?P<lugar>[a-zA-ZáéíóúñüÑÁÉÍÓÚ\s]+)?
    """,
    re.VERBOSE | re.IGNORECASE,
)

_SINONIMOS_CAPA = {
    "sismos": "sismos",
    "terremotos": "sismos",
    "vuelos": "vuelos",
    "aviones": "vuelos",
    "aeronaves": "vuelos",
    "militares": "militares",
    "incendios": "incendios",
    "fuegos": "incendios",
    "barcos": "barcos",
    "navios": "barcos",
    "cámaras": "camaras",
    "camaras": "camaras",
    "cctv": "camaras",
}


def _geocodificar(lugar: str) -> tuple[float | None, float | None] | None:
    """Intenta geocodificar un nombre de lugar usando el bridge de GEV."""
    if not lugar or not lugar.strip():
        return None
    try:
        from engine.gev_bridge import GevClient

        cli = GevClient()
        if not cli.is_up():
            return None
        res = cli.geocode(lugar.strip())
        if isinstance(res, dict) and res.get("lat") is not None:
            return (float(res["lat"]), float(res["lon"]))
    except Exception:
        pass
    return None


def buscar(query: str, slug: str = "") -> dict[str, Any]:
    """Procesa una búsqueda del usuario y devuelve capa + destino.

    Ejemplos de query:
      "vuelos cerca de Madrid"
      "incendios en California"
      "sismos"
      "mostrame los barcos cerca de Puerto Rico"

    Devuelve:
      {
        "ok": True,
        "capa": "vuelos",
        "destino": {"lat": 40.4, "lon": -3.7, "radio_km": 150.0},
        "lugar": "Madrid",
        "contexto": "vuelos cerca de Madrid",
        "ts": 1234567890
      }
    """
    query = (query or "").strip().lower()
    if not query:
        return {"ok": False, "error": "query vacía"}

    m = _BUSQUEDA_PATRON.search(query)
    if not m:
        return {
            "ok": False,
            "error": f"no reconozco la capa en: {query!r}",
            "capas_validas": sorted(_SINONIMOS_CAPA.keys()),
        }

    capa_cruda = m.group("capa").lower().strip()
    capa = _SINONIMOS_CAPA.get(capa_cruda, capa_cruda)
    if capa not in COLORES:
        return {"ok": False, "error": f"capa inválida: {capa!r}"}

    lugar_crudo = (m.group("lugar") or "").strip()
    aoi = obtener(slug).get("aoi", {}) if slug else {}
    lat, lon = None, None

    if lugar_crudo:
        geo = _geocodificar(lugar_crudo)
        if geo:
            lat, lon = geo
        else:
            return {
                "ok": False,
                "error": f"no encuentro {lugar_crudo!r}",
                "capa": capa,
            }
    elif aoi.get("lat") is not None:
        lat, lon = aoi["lat"], aoi["lon"]

    radio_km = float(aoi.get("radio_km") or 150.0)

    destino = {"lat": lat, "lon": lon, "radio_km": radio_km}
    contexto = f"{capa}" + (f" cerca de {lugar_crudo}" if lugar_crudo else "")

    if slug:
        config = obtener(slug)
        config["ultima_busqueda"] = {
            "query": query,
            "capa": capa,
            "lugar": lugar_crudo,
            "lat": lat,
            "lon": lon,
            "ts": time.time(),
        }
        config["capas_activas"] = list(set(config.get("capas_activas", []) + [capa]))
        guardar(slug, config)

    return {
        "ok": True,
        "capa": capa,
        "capa_color": COLORES[capa],
        "destino": destino,
        "lugar": lugar_crudo,
        "contexto": contexto,
        "ts": time.time(),
    }


def catalogo_personalizado(slug: str) -> dict[str, Any]:
    """Catálogo de capas con el estado personalizado del usuario."""
    config = obtener(slug)
    cat = catalogar_capas()
    activas = set(config.get("capas_activas", []))

    capas = []
    for c in cat.get("capas", []):
        c = dict(c)
        c["activa"] = c["capa"] in activas
        capas.append(c)

    return {
        "ok": True,
        "slug": slug,
        "capas": capas,
        "aoi": config.get("aoi"),
        "estilo": config.get("estilo", "normal"),
        "mapa": config.get("mapa", "satellite"),
        "ultima_busqueda": config.get("ultima_busqueda"),
        "ts": time.time(),
    }
