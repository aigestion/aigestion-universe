#!/usr/bin/env python3
"""
GEV Integration — punto unico de entrada para Daniela
=====================================================
Capa fina sobre `gev_bridge` (enlaces + feeds), `gev_watch` (geocercas) y
`gev_archive` (historico). Expone:

  1. `register_gev_routes(app)` — rutas Flask, misma convencion que el resto
     de modulos de Daniela (`pixel_bridge_hub`, `sensor_stream_live`, ...).
  2. `enriquecer_respuesta(...)` — **Daniela muestra, no solo cuenta**: si una
     respuesta habla de un lugar, se le anade el enlace al globo ya enfocado.
  3. `estado()` — resumen de salud para el panel.

Autocontenido a proposito: inserta su propio directorio en sys.path, asi que
funciona aunque `daniela_os.py` no lo tenga en la lista de imports.

Rutas:
  GET  /api/gev/status                 salud de GEV + resumen del archivo
  GET  /api/gev/link?lat&lon&contexto  enlace profundo al globo
  GET  /api/gev/vuelos?lat&lon&radio   aeronaves cerca de un punto
  GET  /api/gev/sismos?min_mag         sismos recientes (USGS)
  GET  /api/gev/zonas                  geocercas configuradas
  POST /api/gev/zonas                  crear/actualizar geocerca
  GET  /api/gev/eventos                una pasada de vigilancia
  POST /api/gev/capturar               una foto del AOI al archivo
  GET  /api/gev/timeline?lat&lon&horas evolucion temporal
  GET  /api/gev/rebobinar?lat&lon&hace que habia alli hace N horas

Coste: $0. Todo lo expuesto funciona sin claves de pago.
"""

from __future__ import annotations

import os
import re
import sys
import time
from typing import Any

# Autocontenido: permitir `import gev_bridge` sin depender del sys.path ajeno
_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from gev_archive import capturar, rebobinar, stats, timeline  # noqa: E402
from gev_bridge import (  # noqa: E402
    ESTILOS,
    GevClient,
    estilo_para,
    gev_link,
)
from gev_watch import (  # noqa: E402
    CAPAS_VALIDAS,
    GevWatcher,
    Zona,
    cargar_zonas,
    guardar_zonas,
)

# ── 2. "Daniela muestra, no solo cuenta" ─────────────────────

# Coordenadas sueltas en un texto: "41.39, 2.15" o "41.39 2.15"
_RE_COORDS = re.compile(r"(-?\d{1,3}\.\d{3,})\s*[, ]\s*(-?\d{1,3}\.\d{3,})")


def extraer_coords(texto: str) -> tuple[float, float] | None:
    """Saca la primera pareja (lat, lon) que aparezca en un texto."""
    m = _RE_COORDS.search(texto or "")
    if not m:
        return None
    lat, lon = float(m.group(1)), float(m.group(2))
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return lat, lon


def enriquecer_respuesta(
    texto: str,
    lat: float | None = None,
    lon: float | None = None,
    contexto: str = "",
    alt: float = 1500,
) -> str:
    """Anade al final de la respuesta un enlace al globo, si hay un lugar.

    Si no se pasan coordenadas, intenta sacarlas del propio texto.
    Si no hay lugar, devuelve el texto intacto (no inventa nada).
    """
    if lat is None or lon is None:
        par = extraer_coords(texto)
        if not par:
            return texto
        lat, lon = par
    try:
        url = gev_link(lat, lon, alt=alt, style=estilo_para(contexto))
    except ValueError:
        return texto
    return f"{texto}\n\n🌍 Verlo en el globo: {url}"


# ── 3. Estado ────────────────────────────────────────────────


def estado() -> dict[str, Any]:
    """Resumen de salud: GEV vivo, geocercas y que hay archivado."""
    cli = GevClient()
    up = cli.is_up()
    zonas = cargar_zonas()
    s = stats()
    return {
        "gev": {"base": cli.base, "arriba": up},
        "geocercas": [
            {"key": z.key, "nombre": z.nombre, "lat": z.lat, "lon": z.lon,
             "radio_km": z.radio_km, "capas": z.capas}
            for z in zonas
        ],
        "archivo": s,
        "capas_validas": list(CAPAS_VALIDAS),
        "estilos": list(ESTILOS),
    }


# ── 1. Rutas Flask ───────────────────────────────────────────


def register_gev_routes(app) -> None:
    """Registra las rutas de GEV en una app Flask de Daniela."""
    from flask import jsonify, request

    def _f(name: str, default: float) -> float:
        try:
            return float(request.args.get(name, default))
        except (TypeError, ValueError):
            return default

    @app.route("/api/gev/status")
    def gev_status():
        try:
            return jsonify({"ok": True, **estado()})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/gev/link")
    def gev_link_route():
        lat, lon = _f("lat", 0.0), _f("lon", 0.0)
        contexto = request.args.get("contexto", "")
        try:
            url = gev_link(lat, lon, alt=_f("alt", 1500),
                           pitch=_f("pitch", -35),
                           style=request.args.get("style") or estilo_para(contexto))
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400
        return jsonify({"ok": True, "url": url})

    @app.route("/api/gev/vuelos")
    def gev_vuelos():
        try:
            cli = GevClient()
            filas = cli.vuelos_cerca(_f("lat", 0.0), _f("lon", 0.0),
                                     _f("radio", 50), int(_f("limite", 25)))
            return jsonify({"ok": True, "n": len(filas), "vuelos": filas})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 502

    @app.route("/api/gev/sismos")
    def gev_sismos():
        try:
            filas = GevClient.sismos(min_mag=_f("min_mag", 4.0),
                                     limite=int(_f("limite", 25)))
            return jsonify({"ok": True, "n": len(filas), "sismos": filas})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 502

    @app.route("/api/gev/zonas", methods=["GET"])
    def gev_zonas_get():
        return jsonify({"ok": True, "zonas": [z.__dict__ for z in cargar_zonas()]})

    @app.route("/api/gev/zonas", methods=["POST"])
    def gev_zonas_post():
        d = request.get_json(silent=True) or {}
        if not d.get("key") or d.get("lat") is None or d.get("lon") is None:
            return jsonify({"ok": False, "error": "faltan key/lat/lon"}), 400
        capas = [c for c in d.get("capas", ["vuelos", "sismos"]) if c in CAPAS_VALIDAS]
        zonas = [z for z in cargar_zonas() if z.key != d["key"]]
        zonas.append(Zona(
            key=d["key"], nombre=d.get("nombre", d["key"]),
            lat=float(d["lat"]), lon=float(d["lon"]),
            radio_km=float(d.get("radio_km", 25.0)),
            capas=capas or ["vuelos", "sismos"],
            min_mag=float(d.get("min_mag", 4.0)),
        ))
        guardar_zonas(zonas)
        return jsonify({"ok": True, "n": len(zonas)})

    @app.route("/api/gev/eventos")
    def gev_eventos():
        try:
            evs = GevWatcher().revisar()
            return jsonify({"ok": True, "n": len(evs),
                            "eventos": [e.to_dict() for e in evs]})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/gev/capturar", methods=["POST", "GET"])
    def gev_capturar():
        try:
            r = capturar()
            return jsonify({"ok": True, "filas": r.filas,
                            "por_capa": r.por_capa, "errores": r.errores})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/gev/timeline")
    def gev_timeline():
        try:
            filas = timeline(_f("lat", 0.0), _f("lon", 0.0), _f("radio", 50),
                             int(_f("horas", 24)), int(_f("bucket_min", 60)))
            return jsonify({"ok": True, "n": len(filas), "franjas": filas})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/gev/rebobinar")
    def gev_rebobinar():
        try:
            ts = time.time() - _f("hace", 1.0) * 3600
            filas = rebobinar(ts, _f("lat", 0.0), _f("lon", 0.0),
                              _f("radio", 50), request.args.get("capa"))
            return jsonify({"ok": True, "n": len(filas), "objetos": filas})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    print("[GEV] rutas registradas: /api/gev/*")


# ── Auto-test ────────────────────────────────────────────────


def _selftest() -> int:
    print("== estado ==")
    e = estado()
    print(f"  GEV {e['gev']['base']}: {'ARRIBA' if e['gev']['arriba'] else 'CAIDO'}")
    print(f"  geocercas: {len(e['geocercas'])}  archivo: {e['archivo']['total']} obs")
    print("== extraer_coords ==")
    for t in ("Esta en 41.3902, 2.1540 cerca del puerto", "sin coordenadas aqui"):
        print(f"  {t[:38]!r} -> {extraer_coords(t)}")
    print("== enriquecer_respuesta ==")
    print(enriquecer_respuesta("Hay un incendio activo.", 41.39, 2.15, "incendio"))
    return 0


if __name__ == "__main__":
    sys.exit(_selftest())
