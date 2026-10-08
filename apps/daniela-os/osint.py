#!/usr/bin/env python3
"""
gev.osint — Capas OSINT dentro del visor de Daniela
==================================================================
Trae feeds publicos en vivo al globo 3D de Daniela usando `core/gev_bridge.py`
como frontera. Daniela NO depende de la interfaz de God's Eye View: solo de sus
datos. Si GEV no esta levantado, las capas que lo necesitan se declaran
`conectado: false` en vez de devolver puntos falsos.

Capas:
  sismos     USGS directo (sin clave, sin GEV)   -> siempre disponible
  vuelos     OpenSky via proxy de GEV
  militares  adsb.lol via proxy de GEV
  incendios  NASA FIRMS via GEV (requiere clave en GEV)
  barcos     AISStream via GEV (requiere clave en GEV)
  camaras    CCTV publicas via GEV

Todas las capas se normalizan a la misma forma de punto para que el visor las
pinte igual:
    {"lat", "lon", "etiqueta", "detalle", "color", "altura_m", "tipo"}
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

_DIR = os.path.dirname(os.path.abspath(__file__))


def _raiz_repo() -> str:
    """Raíz por marcador (ver el mismo criterio en `billing.py`).

    Este fichero vivía en `<repo>/aig/gev/`: al mudarse a
    `<repo>/gev/`, dos `..` dejaron de dar la raíz y apuntaban al padre
    del proyecto.
    """
    aqui = Path(_DIR)
    for c in (aqui, *aqui.parents):
        if (c / ".git").exists() or (c / "tests" / "conftest.py").exists():
            return str(c)
    return os.path.dirname(_DIR)


_RAIZ = _raiz_repo()
for _p in (_RAIZ, os.path.join(_RAIZ, "core")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Colores por capa (coherentes con el resto del visor)
COLORES = {
    "sismos": "#f97316",
    "vuelos": "#38bdf8",
    "militares": "#ef4444",
    "incendios": "#dc2626",
    "barcos": "#22d3ee",
    "camaras": "#a78bfa",
}

# TTL de cache por capa, en segundos. Los feeds externos (USGS, OpenSky via GEV)
# cambian despacio comparado con la frecuencia con la que el usuario marca y
# desmarca capas. Sin cache, cada clic repetia la descarga completa: medido,
# 316 ms en sismos y 142 ms en vuelos. Con cache, ~1 ms.
#
# Los sismos duran mas en cache porque USGS publica cada pocos minutos; los
# vuelos menos, porque son posiciones en movimiento.
TTL = {
    "sismos": 120,
    "vuelos": 20,
    "militares": 20,
    "incendios": 300,
    "barcos": 30,
    "camaras": 300,
}

# clave -> (expira_en, valor)
_CACHE: dict[str, tuple[float, Any]] = {}


def _cache_clave(nombre: str, lat, lon, radio_km, limite, min_mag) -> str:
    """Clave de cache. Incluye el AOI: dos zonas no comparten resultado."""
    aoi = (
        ""
        if lat is None or lon is None
        else f"{round(float(lat), 2)},{round(float(lon), 2)},{round(float(radio_km), 0)}"
    )
    return f"{nombre}|{aoi}|{int(limite)}|{round(float(min_mag), 1)}"


def _cache_leer(clave: str) -> dict[str, Any] | None:
    entrada = _CACHE.get(clave)
    if not entrada:
        return None
    expira, valor = entrada
    if time.time() > expira:
        _CACHE.pop(clave, None)
        return None
    return valor


def _cache_escribir(clave: str, nombre: str, valor: dict[str, Any]) -> None:
    _CACHE[clave] = (time.time() + TTL.get(nombre, 30), valor)
    # Poda simple para que no crezca sin limite con muchas zonas distintas.
    if len(_CACHE) > 64:
        ahora = time.time()
        for k in [k for k, (exp, _) in _CACHE.items() if exp < ahora]:
            _CACHE.pop(k, None)
        if len(_CACHE) > 64:
            _CACHE.pop(next(iter(_CACHE)))


def cache_estado() -> dict[str, Any]:
    """Estado del cache, para diagnostico."""
    ahora = time.time()
    return {
        "entradas": len(_CACHE),
        "ttl": dict(TTL),
        "vigentes": {k: round(v[0] - ahora, 1) for k, v in _CACHE.items()},
    }


# Capas que NO necesitan que GEV este levantado
DIRECTAS = {"sismos"}

# Capas que ademas necesitan una clave configurada en GEV
CON_CLAVE = {"incendios": "NASA FIRMS", "barcos": "AISStream"}


def _cliente():
    from gev_bridge import GevClient

    return GevClient()


def _punto(
    lat: Any, lon: Any, etiqueta: str, detalle: str, capa: str, altura_m: float = 0.0
) -> dict[str, Any] | None:
    """Normaliza un punto. Descarta lo que no tenga coordenadas validas."""
    try:
        la, lo = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    if not (-90 <= la <= 90) or not (-180 <= lo <= 180):
        return None
    return {
        "lat": round(la, 5),
        "lon": round(lo, 5),
        "etiqueta": (etiqueta or "")[:80],
        "detalle": (detalle or "")[:200],
        "color": COLORES.get(capa, "#94a3b8"),
        "altura_m": float(altura_m or 0),
        "tipo": capa,
    }


def _extraer_puntos(datos: Any, capa: str, limite: int) -> list[dict[str, Any]]:
    """Extractor tolerante: acepta varias formas de feed y saca puntos.

    Formatos contemplados:
      - OpenSky  : {"states": [[...18 campos...]]}
      - FIRMS    : {"fires": [{"latitude", "longitude", ...}]}
      - listas de dicts con lat/lon o latitude/longitude
    """
    crudos: list[Any] = []

    if isinstance(datos, dict):
        for clave in (
            "states",
            "fires",
            "data",
            "items",
            "results",
            "features",
            "aircraft",
            "vessels",
            "cameras",
            "satellites",
        ):
            if isinstance(datos.get(clave), list):
                crudos = datos[clave]
                break
    elif isinstance(datos, list):
        crudos = datos

    puntos: list[dict[str, Any]] = []
    for it in crudos:
        if len(puntos) >= limite:
            break

        # OpenSky: lista posicional
        if isinstance(it, (list, tuple)) and len(it) >= 11:
            p = _punto(
                it[6],
                it[5],
                str(it[1] or it[0] or ""),
                f"alt {it[7]} m · vel {it[9]} m/s",
                capa,
                it[7] or 0,
            )
            if p:
                puntos.append(p)
            continue

        if not isinstance(it, dict):
            continue

        # FIRMS / dicts con claves geograficas
        lat = it.get("latitude", it.get("lat"))
        lon = it.get("longitude", it.get("lon", it.get("lng")))
        if lat is None and isinstance(it.get("geometry"), dict):
            coords = it["geometry"].get("coordinates") or []
            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]

        etiqueta = str(
            it.get("callsign")
            or it.get("name")
            or it.get("title")
            or it.get("place")
            or it.get("id")
            or it.get("mmsi")
            or capa
        )
        detalle = str(
            it.get("country")
            or it.get("pais")
            or it.get("confidence")
            or it.get("description")
            or it.get("type")
            or ""
        )
        p = _punto(lat, lon, etiqueta, detalle, capa, it.get("altitude", it.get("alt", 0)) or 0)
        if p:
            puntos.append(p)

    return puntos


def capas() -> dict[str, Any]:
    """Catalogo de capas con su estado real de disponibilidad."""
    try:
        cli = _cliente()
        gev_vivo = bool(cli.is_up())
    except Exception:  # noqa: BLE001
        gev_vivo = False

    catalogo = []
    for nombre in ("sismos", "vuelos", "militares", "incendios", "barcos", "camaras"):
        necesita_gev = nombre not in DIRECTAS
        clave = CON_CLAVE.get(nombre)
        if not necesita_gev:
            estado, motivo = "ok", "USGS directo, sin clave"
        elif not gev_vivo:
            estado, motivo = "sin_gev", "GEV no responde: levantalo para esta capa"
        else:
            estado, motivo = "ok", "via proxy de GEV"
            if clave:
                motivo = f"via GEV, requiere clave {clave}"
        catalogo.append(
            {
                "capa": nombre,
                "color": COLORES[nombre],
                "necesita_gev": necesita_gev,
                "requiere_clave": clave,
                "estado": estado,
                "motivo": motivo,
            }
        )

    return {"ok": True, "gev_vivo": gev_vivo, "capas": catalogo, "ts": time.time()}


def capa(
    nombre: str,
    lat: float | None = None,
    lon: float | None = None,
    radio_km: float = 150.0,
    limite: int = 400,
    min_mag: float = 4.0,
    forzar: bool = False,
) -> dict[str, Any]:
    """Puntos de una capa, opcionalmente recortados a un area de interes.

    Si se pasan `lat`/`lon`, solo se devuelven los puntos dentro de `radio_km`.
    El resultado se cachea durante `TTL[capa]` segundos: los feeds externos
    cambian despacio y el usuario marca/desmarca capas a menudo. `forzar=True`
    salta el cache.
    """
    nombre = (nombre or "").strip().lower()
    if nombre not in COLORES:
        return {
            "ok": False,
            "error": f"capa desconocida: {nombre!r}",
            "capas_validas": sorted(COLORES),
        }

    limite = max(1, min(int(limite or 400), 2000))

    clave = _cache_clave(nombre, lat, lon, radio_km, limite, min_mag)
    if not forzar:
        guardado = _cache_leer(clave)
        if guardado is not None:
            return {**guardado, "cache": True}

    res = _capa_sin_cache(nombre, lat, lon, radio_km, limite, min_mag)
    # Solo se cachea lo que salio bien: un fallo de red no debe quedarse
    # pegado durante minutos.
    if res.get("ok"):
        _cache_escribir(clave, nombre, res)
    return {**res, "cache": False}


def _capa_sin_cache(
    nombre: str, lat: float | None, lon: float | None, radio_km: float, limite: int, min_mag: float
) -> dict[str, Any]:
    """Descarga real de una capa. Sin cache: llamar a `capa()` normalmente."""
    # ── Sismos: USGS directo ──
    if nombre == "sismos":
        try:
            from gev_bridge import GevClient

            if lat is not None and lon is not None:
                crudos = GevClient.sismos_cerca(
                    float(lat), float(lon), radio_km=radio_km, min_mag=min_mag
                )
            else:
                crudos = GevClient.sismos(min_mag=min_mag, limite=limite)
        except Exception as e:  # noqa: BLE001
            return {
                "ok": False,
                "capa": nombre,
                "conectado": False,
                "motivo": f"USGS inalcanzable: {e}",
                "puntos": [],
            }

        puntos = []
        for s in crudos[:limite]:
            p = _punto(
                s.get("lat"),
                s.get("lon"),
                f"M{s.get('mag')} · {s.get('lugar') or '?'}",
                f"prof {s.get('prof_km')} km",
                nombre,
                0,
            )
            if p:
                puntos.append(p)
        return {
            "ok": True,
            "capa": nombre,
            "conectado": True,
            "fuente": "USGS (directo)",
            "total": len(puntos),
            "puntos": puntos,
            "ts": time.time(),
        }

    # ── Resto: via proxy de GEV ──
    try:
        cli = _cliente()
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "capa": nombre,
            "conectado": False,
            "motivo": f"gev_bridge no importable: {e}",
            "puntos": [],
        }

    if not cli.is_up():
        return {
            "ok": False,
            "capa": nombre,
            "conectado": False,
            "motivo": (
                "GEV no responde. Levanta God's Eye View para esta "
                "capa, o usa la capa 'sismos' que es directa."
            ),
            "puntos": [],
        }

    try:
        if nombre == "vuelos" and lat is not None and lon is not None:
            crudos = cli.vuelos_cerca(float(lat), float(lon), radio_km=radio_km, limite=limite)
            # vuelos_cerca ya devuelve dicts normalizados
            puntos = []
            for v in crudos[:limite]:
                p = _punto(
                    v.get("lat"),
                    v.get("lon"),
                    str(v.get("callsign") or v.get("icao24") or "?"),
                    f"{v.get('pais', '?')} · {v.get('dist_km', '?')} km",
                    nombre,
                    v.get("alt_m") or 0,
                )
                if p:
                    puntos.append(p)
            return {
                "ok": True,
                "capa": nombre,
                "conectado": True,
                "fuente": "OpenSky via GEV",
                "total": len(puntos),
                "puntos": puntos,
                "ts": time.time(),
            }

        datos = {
            "vuelos": cli.vuelos,
            "militares": cli.militares,
            "incendios": cli.incendios,
            "barcos": cli.barcos,
            "camaras": cli.camaras,
        }[nombre]()
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "capa": nombre,
            "conectado": False,
            "motivo": f"feed fallo: {str(e)[:180]}",
            "puntos": [],
        }

    puntos = _extraer_puntos(datos, nombre, limite)

    # Recorte por area de interes
    if lat is not None and lon is not None and puntos:
        try:
            from gev_bridge import distancia_km

            puntos = [
                p
                for p in puntos
                if distancia_km(float(lat), float(lon), p["lat"], p["lon"]) <= radio_km
            ]
        except Exception:  # noqa: BLE001
            pass

    conectado = bool(puntos)
    res: dict[str, Any] = {
        "ok": True,
        "capa": nombre,
        "conectado": conectado,
        "fuente": f"{nombre} via GEV",
        "total": len(puntos),
        "puntos": puntos,
        "ts": time.time(),
    }
    if not conectado:
        clave = CON_CLAVE.get(nombre)
        res["motivo"] = f"El feed de {nombre} no devolvio puntos legibles." + (
            f" Puede faltar la clave {clave} en GEV." if clave else ""
        )
    return res
