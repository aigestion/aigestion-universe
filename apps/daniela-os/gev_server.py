#!/usr/bin/env python3
"""
gev_server.py (módulo `gev.gev_server`) - Backend del visor 3D unificado
==========================================================
2026-10-04: era `daniela-os/server.py` (nombre que ocupa la app principal
tras unificar el arbol anidado; ver P1 de reestructura).
Sirve el Visor (God's Eye Dashboard) y su API de datos. Es el **punto de
entrada unico** de Daniela OS.

Aplica el modelo de acceso de `core.access`:
  - ADMIN   -> ve la Sede + TODAS las empresas + agregados
  - CLIENTE -> ve SOLO su empresa; la Sede y las demas le quedan vetadas

Rutas:
  GET  /gods-eye                       -> el visor (HTML)
  GET  /gods-eye/static/<f>            -> assets del visor
  GET  /gods-eye/vendor/cesium/<f>     -> assets de Cesium
  GET  /api/globe/data                 -> nodos del globo (filtrado por rol)
  GET  /api/globe/cliente/<id>         -> detalle + estructura 3D
  POST /api/globe/cliente              -> alta de empresa (solo admin)
  POST /api/globe/cliente/<id>/estado  -> cambiar estado operativo
  GET  /api/globe/eventos              -> telemetria reciente
  GET  /api/globe/stream               -> SSE de telemetria (tiempo real)
  GET  /api/globe/osint                -> catalogo de capas OSINT
  GET  /api/globe/osint/<capa>         -> puntos de una capa (AOI opcional)
  GET  /api/globe/memoria[?q=]         -> recuerdos de Daniela (solo admin)
  POST /api/globe/memoria              -> guardar un recuerdo   (solo admin)
  DELETE /api/globe/memoria/<id>       -> olvidar un recuerdo   (solo admin)
  GET  /api/i18n[ /<lang>]             -> cadenas de idioma (es por defecto)
  GET  /api/cc/*                       -> 5 herramientas del Command Center

Registro en Daniela OS (convencion del repo):
    from gev.gev_server import register_gev_routes
    register_gev_routes(app)
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import time
from typing import Any

# Autocontenido: resolver imports propios y del core de aig
_DIR = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.abspath(os.path.join(_DIR, os.pardir))
_CORE = os.path.join(_RAIZ, "core")
# La raiz SIEMPRE (para el respaldo `import access`, `import business_store`...)
# y `core/` (compatibilidad). `gev/` NO: meterlo en `sys.path[0]` hacia
# que `gev/i18n.py` se colara delante de `ux_engine/i18n.py` y los tests
# de UX pasaban o fallaban segun el orden de coleccion. Se anade unicamente
# en modo script, donde no existe el paquete `gev`.
for _p in (_RAIZ, _CORE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
if not __package__ and _DIR not in sys.path:
    sys.path.insert(0, _DIR)


def _importar_core(nombre: str) -> Any:
    """Importa un modulo de `aig/core` como parte del paquete.

    Se prefiere `core.X` para que sea EL MISMO modulo que usa el resto
    de aig. Con `import X` a secas, Python lo cargaba dos veces (como `X` y
    como `core.X`): dos objetos distintos con estado propio. Hoy los
    tres son practicamente apatridas (su estado vive en disco, con rutas
    absolutas), asi que no divergian, pero era una trampa esperando a que alguien
    anadiese una cache en memoria.

    El respaldo a import directo mantiene el modo autonomo: el visor puede
    arrancar sin el paquete `aig` en sys.path.
    """
    try:
        return importlib.import_module(f"core.{nombre}")
    except ModuleNotFoundError as e:
        # Se respalda con el import directo SOLO si lo que falta es:
        #   - el paquete `aig` (modo autonomo del visor), o
        #   - el propio modulo dentro de `core/`, porque se aplano a la raiz
        #     (2026-09-29: `core/access.py` -> `access.py`,
        #      `core/business_store.py` -> `business_store.py`).
        # Si falta cualquier otra dependencia es un error real y debe
        # propagarse, no esconderse cargando una segunda copia.
        falta = (e.name or "").split(".")
        fuera_de_core = falta[0] == "core" and ".".join(falta) in (f"core.{nombre}", "core")
        if falta[0] != "aig" and not fuera_de_core:
            raise
        return importlib.import_module(nombre)


acc = _importar_core("access")
bs = _importar_core("business_store")
loc = _importar_core("location")

# Modulos hermanos del visor (se importan de forma perezosa y tolerante:
# si uno falla, el visor sigue sirviendo el globo).
_DIR_GE = os.path.dirname(os.path.abspath(__file__))
if not __package__:
    # Solo en modo script (`python gev/server.py`), donde no hay paquete
    # y hay que importar los hermanos por nombre. NO cuando se importa como
    # `gev.gev_server`: meter `gev/` en `sys.path[0]` hacia que
    # `gev/i18n.py` se colara delante de `ux_engine/i18n.py` y
    # `tests/security/test_ux.py` pasaba o fallaba segun el orden de coleccion.
    if _DIR_GE not in sys.path:
        sys.path.insert(0, _DIR_GE)


def _hermano(nombre: str) -> Any:
    """Importa un modulo hermano de `gev/`.

    Prefiere el import como paquete (`gev.i18n`), que no ensucia el
    `sys.path`; si no hay paquete (script suelto), cae al import normal.
    """
    paquete = __package__ or "gev"
    try:
        return importlib.import_module(f".{nombre}", paquete)
    except ImportError:
        return importlib.import_module(nombre)


STATIC_DIR = os.path.join(_DIR, "static")
VENDOR_DIR = os.path.join(_DIR, "vendor", "cesium")
# Assets de marca aig (paleta oficial, logos). Estan en la raiz del repo
# y NO se copian aqui: el visor los sirve desde /gods-eye/brand/ para tener la
# misma fuente de verdad que la PWA (`mobile-app/css/mobile.css`).
BRAND_DIR = os.path.abspath(os.path.join(_DIR, os.pardir, "static", "brand"))

TITULO = "Daniela OS — God's Eye Dashboard"

# Capas OSINT con interes local: si el cliente no da coordenadas, se recortan
# al area de la Sede. El resto (sismos) se sirven globales.
CAPAS_LOCALES = {"vuelos", "militares", "incendios", "barcos", "camaras"}


# ── Datos del globo ──────────────────────────────────────────


def datos_globo(s: acc.Sujeto) -> dict[str, Any]:
    """Nodos que el sujeto puede ver: sede (solo admin) + empresas."""
    clientes = acc.filtrar_clientes(s, bs.listar())
    nodos: list[dict[str, Any]] = []

    for c in clientes:
        d = c.to_dict()
        if not d.get("ubicado"):
            continue
        nodos.append(
            {
                "tipo": "empresa",
                "id": d["id"],
                "nombre": d["nombre"],
                "lat": d["lat"],
                "lon": d["lon"],
                "color": d["color"],
                "estado": d["estado"],
                "estado_etiqueta": d["estado_etiqueta"],
                "tier": d["tier"],
                "sector": d.get("sector", ""),
                "ciudad": d.get("ciudad", ""),
                "pais": d.get("pais", ""),
                "mrr": d.get("mrr", 0),
                "tenant_slug": d.get("tenant_slug", ""),
            }
        )

    sede = None
    if acc.puede_ver_hq(s):
        u = loc.actual()
        sede = {
            "tipo": "sede",
            "id": "sede-aig",
            "nombre": u.etiqueta,
            "lat": u.lat,
            "lon": u.lon,
            "color": "#38bdf8",
            "ciudad": u.ciudad,
            "pais": u.pais,
            "tz": u.tz,
            "fuente": u.fuente,
            "descripcion": u.descripcion(),
        }

    return {
        "sede": sede,
        "nodos": nodos,
        "rol": s.rol.value,
        "resumen": acc.filtrar_resumen(s, bs.resumen()),
        "ts": time.time(),
    }


def estructura_empresa(cid: str, s: acc.Sujeto) -> dict[str, Any]:
    """Detalle de una empresa para desplegar su estructura 3D."""
    c = bs.obtener(cid)
    if c is None:
        raise LookupError(f"no existe la empresa {cid!r}")
    acc.exigir_cliente(s, c.id, c.tenant_slug)

    evs = bs.eventos(cid, limite=20)
    return {
        "empresa": c.to_dict(),
        "modulos": _modulos_de(c),
        "eventos": evs,
        "metricas": {
            "mrr": c.mrr,
            "eventos_24h": len([e for e in evs if time.time() - e["ts"] < 86400]),
        },
    }


def _modulos_de(c: bs.Cliente) -> list[dict[str, Any]]:
    """Modulos 3D de la empresa: departamentos y su estado.

    Se derivan del tier y del estado operativo: no hay datos inventados.
    """
    base = [
        ("Direccion", "direction", "#38bdf8"),
        ("Operaciones", "operations", "#a78bfa"),
        ("Datos / RAG", "rag", "#34d399"),
        ("Automatizaciones", "automation", "#fbbf24"),
    ]
    if c.tier in ("pro", "enterprise"):
        base.append(("Integraciones", "integrations", "#f472b6"))
    if c.tier == "enterprise":
        base.append(("Marca Blanca", "whitelabel", "#facc15"))

    estado_mod = {
        "activo": "ok",
        "alerta": "warn",
        "incidencia": "error",
        "inactivo": "off",
    }.get(c.estado, "off")

    return [
        {
            "nombre": n,
            "clave": k,
            "color": col,
            "estado": estado_mod if k in ("operations", "rag") else "ok",
            "altura": 40 + i * 12,
        }
        for i, (n, k, col) in enumerate(base)
    ]


# ── Rutas Flask ──────────────────────────────────────────────


def register_gev_routes(app) -> None:
    from flask import Response, jsonify, request, send_from_directory

    @app.route("/gods-eye")
    def gever():
        return send_from_directory(STATIC_DIR, "index.html")

    @app.route("/gods-eye/static/<path:nombre>")
    def gev_static(nombre: str):
        return send_from_directory(STATIC_DIR, nombre)

    @app.route("/gods-eye/brand/<path:nombre>")
    def gev_brand(nombre: str):
        """Assets de marca aig: `tokens.css`, logos SVG, etc.

        Se sirven desde `<repo>/static/brand/` para que el visor y la PWA
        compartan UNA sola fuente de verdad de la paleta oficial.
        """
        return send_from_directory(BRAND_DIR, nombre)

    @app.route("/gods-eye/vendor/cesium/<path:nombre>")
    def gev_cesium(nombre: str):
        return send_from_directory(VENDOR_DIR, nombre)

    # -- datos --

    @app.route("/api/globe/data")
    def globe_data():
        s = acc.sujeto_desde_request(request)
        return jsonify({"ok": True, **datos_globo(s)})

    @app.route("/api/globe/cliente/<cid>")
    def globe_cliente(cid: str):
        s = acc.sujeto_desde_request(request)
        try:
            return jsonify({"ok": True, **estructura_empresa(cid, s)})
        except acc.AccesoDenegado as e:
            return jsonify(e.to_dict()), 403
        except LookupError as e:
            return jsonify({"ok": False, "error": str(e)}), 404

    @app.route("/api/globe/cliente", methods=["POST"])
    def globe_alta():
        """Alta de una empresa nueva. Solo el admin puede dar de alta."""
        s = acc.sujeto_desde_request(request)
        if not s.es_admin:
            return jsonify(
                acc.AccesoDenegado(
                    "solo el administrador puede dar de alta empresas", f"rol={s.rol.value}"
                ).to_dict()
            ), 403

        cuerpo = request.get_json(silent=True) or {}
        nombre = (cuerpo.get("nombre") or "").strip()
        if not nombre:
            return jsonify({"ok": False, "error": "falta el nombre"}), 400

        try:
            c = bs.alta(
                nombre=nombre,
                direccion=(cuerpo.get("direccion") or "").strip(),
                tier=(cuerpo.get("tier") or "free").strip(),
                sector=(cuerpo.get("sector") or "").strip(),
                email=(cuerpo.get("email") or "").strip(),
                telefono=(cuerpo.get("telefono") or "").strip(),
                web=(cuerpo.get("web") or "").strip(),
                notas=(cuerpo.get("notas") or "").strip(),
                mrr=(float(cuerpo["mrr"]) if cuerpo.get("mrr") not in (None, "") else None),
                geocodificar_direccion=bool(cuerpo.get("geocodificar", True)),
            )
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(e)[:200]}), 500

        bs.registrar_evento(c.id, "alta", f"empresa dada de alta por {s.nombre}")
        return jsonify({"ok": True, "empresa": c.to_dict()}), 201

    @app.route("/api/globe/cliente/<cid>/estado", methods=["POST"])
    def globe_estado(cid: str):
        s = acc.sujeto_desde_request(request)
        c = bs.obtener(cid)
        if c is None:
            return jsonify({"ok": False, "error": "no existe"}), 404
        try:
            acc.exigir_operar(s, c.id, c.tenant_slug)
        except acc.AccesoDenegado as e:
            return jsonify(e.to_dict()), 403
        cuerpo = request.get_json(silent=True) or {}
        nuevo = (cuerpo.get("estado") or "").strip()
        try:
            actualizado = bs.cambiar_estado(cid, nuevo, cuerpo.get("mensaje", ""))
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400
        return jsonify({"ok": True, "empresa": actualizado.to_dict()})

    @app.route("/api/globe/eventos")
    def globe_eventos():
        s = acc.sujeto_desde_request(request)
        cid = request.args.get("cliente") or None
        if cid:
            c = bs.obtener(cid)
            if c is None:
                return jsonify({"ok": False, "error": "no existe"}), 404
            try:
                acc.exigir_cliente(s, c.id, c.tenant_slug)
            except acc.AccesoDenegado as e:
                return jsonify(e.to_dict()), 403
        return jsonify({"ok": True, "eventos": bs.eventos(cid, limite=40)})

    # -- capas OSINT (GEV como sensorio) --

    @app.route("/api/globe/osint")
    def globe_osint_capas():
        """Catalogo de capas y su estado real de disponibilidad."""
        try:
            _osint = _hermano("osint")
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": f"osint no importable: {e}"}), 500
        d = _osint.capas()
        d["cache"] = {k: v for k, v in _osint.cache_estado().items() if k in ("entradas", "ttl")}
        return jsonify(d)

    @app.route("/api/globe/osint/<capa>")
    def globe_osint_capa(capa: str):
        """Puntos de una capa. Por defecto, recortados al AOI de la Sede."""
        try:
            _osint = _hermano("osint")
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": f"osint no importable: {e}"}), 500

        def _f(nombre: str, defecto: float) -> float:
            try:
                return float(request.args.get(nombre, defecto))
            except (TypeError, ValueError):
                return defecto

        def _flag(nombre: str) -> bool:
            """Bandera booleana de la query string.

            `bool(request.args.get(x))` seria erroneo: "0" y "false" son cadenas
            no vacias y por tanto verdaderas. Solo se acepta lo que el usuario
            quiere decir de verdad.
            """
            return (request.args.get(nombre) or "").strip().lower() in (
                "1",
                "true",
                "si",
                "sí",
                "yes",
                "on",
            )

        lat = request.args.get("lat")
        lon = request.args.get("lon")

        # Sin AOI explicito se usa la Sede, pero SOLO para capas de interes
        # local. Los sismos son un peligro global: recortarlos a 150 km de la
        # sede devolveria casi siempre 0 y ocultaria lo que importa.
        if lat is None and lon is None and capa in CAPAS_LOCALES:
            s = acc.sujeto_desde_request(request)
            if acc.puede_ver_hq(s):
                try:
                    u = loc.actual()
                    lat, lon = str(u.lat), str(u.lon)
                except Exception:  # noqa: BLE001
                    pass

        try:
            res = _osint.capa(
                capa,
                lat=float(lat) if lat is not None else None,
                lon=float(lon) if lon is not None else None,
                radio_km=_f("radio_km", 150.0),
                limite=int(_f("limite", 400)),
                min_mag=_f("min_mag", 4.0),
                forzar=_flag("forzar"),
            )
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "capa": capa, "error": str(e)[:200]}), 500
        return jsonify(res), (200 if res.get("ok") else 400)

    # -- SSE: telemetria en tiempo real --

    @app.route("/api/globe/stream")
    def globe_stream():
        s = acc.sujeto_desde_request(request)

        def generar():
            visto: dict[str, float] = {}
            # Cache cliente_id -> tenant_slug: el bucle corre cada 5 s y no
            # tiene sentido golpear la base de datos por cada evento.
            tenants: dict[str, str | None] = {}

            def _tenant_de(cid: str) -> str | None:
                if cid not in tenants:
                    c = bs.obtener(cid)
                    tenants[cid] = c.tenant_slug if c is not None else None
                return tenants[cid]

            while True:
                try:
                    for ev in bs.eventos(limite=20):
                        clave = f"{ev['cliente_id']}:{ev['id']}"
                        if clave in visto:
                            continue
                        visto[clave] = ev["ts"]
                        payload = dict(ev)
                        if not s.es_admin:
                            # Un cliente solo recibe SUS eventos. Se pasa el
                            # tenant_slug REAL del cliente: antes se pasaba el
                            # cliente_id, asi que la comparacion usaba el valor
                            # equivocado y un cliente cuyo slug de tenant difiere
                            # de su id nunca coincidia (se quedaba sin eventos).
                            #
                            # Se pasa el valor tal cual (aunque este vacio) y se
                            # deja que `puede_ver_cliente` aplique su propio
                            # respaldo a cliente_id: cortar aqui con `if not ts`
                            # dejaria sin eventos a los clientes sin tenant
                            # enlazado, que antes si los recibian.
                            ts = _tenant_de(ev["cliente_id"])
                            if not acc.puede_ver_cliente(s, ev["cliente_id"], ts):
                                continue
                        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                    if len(visto) > 500:
                        visto.clear()
                    if len(tenants) > 200:
                        tenants.clear()
                except Exception as e:  # noqa: BLE001
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                time.sleep(5)

        return Response(
            generar(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # -- idioma (espanol por defecto, ingles opcional) --

    try:
        _i18n = _hermano("i18n")
        _i18n.registrar_i18n(app)
    except Exception as e:  # noqa: BLE001
        print(f"[God's Eye] i18n NO registrado: {e}")

    # -- Command Center: 5 herramientas conectadas a backends reales --

    try:
        _cc = _hermano("command_center")
        _cc.registrar_command_center(app)
    except Exception as e:  # noqa: BLE001
        print(f"[God's Eye] Command Center NO registrado: {e}")

    # -- facturacion (Stripe con firma obligatoria) --

    try:
        _billing = _hermano("billing")
        _billing.registrar_billing(app)
    except Exception as e:  # noqa: BLE001
        print(f"[God's Eye] Billing NO registrado: {e}")

    # -- memoria bidireccional de Daniela (MemoryVault, lo mismo que el chat) --

    try:
        _mem = _hermano("memoria")
        _mem.registrar_memoria(app)
    except Exception as e:  # noqa: BLE001
        print(f"[God's Eye] Memoria NO registrada: {e}")

    # -- capas personalizadas por usuario + búsqueda dirigida por Daniela --

    try:
        _capas = _hermano("capas_usuario")

        @app.route("/api/globe/capas")
        def globe_capas_get():
            s = acc.sujeto_desde_request(request)
            slug = s.tenant_slug or (s.id if s.es_admin else "anon")
            return jsonify(_capas.catalogo_personalizado(slug))

        @app.route("/api/globe/capas", methods=["POST"])
        def globe_capas_post():
            s = acc.sujeto_desde_request(request)
            cuerpo = request.get_json(silent=True) or {}
            slug = s.tenant_slug or (s.id if s.es_admin else "anon")
            config = _capas.obtener(slug)
            if "capas_activas" in cuerpo:
                config["capas_activas"] = cuerpo["capas_activas"]
            if "aoi" in cuerpo:
                config["aoi"] = cuerpo["aoi"]
            if "estilo" in cuerpo:
                config["estilo"] = cuerpo["estilo"]
            if "mapa" in cuerpo:
                config["mapa"] = cuerpo["mapa"]
            _capas.guardar(slug, config)
            return jsonify({"ok": True, **_capas.catalogo_personalizado(slug)})

        @app.route("/api/globe/busqueda")
        def globe_busqueda():
            s = acc.sujeto_desde_request(request)
            q = (request.args.get("q") or "").strip()
            if not q:
                return jsonify({"ok": False, "error": "falta el parámetro q"}), 400
            slug = s.tenant_slug or (s.id if s.es_admin else "anon")
            return jsonify(_capas.buscar(q, slug))

    except Exception as e:  # noqa: BLE001
        print(f"[God's Eye] Capas personalizadas NO registradas: {e}")

    print(
        "[God's Eye] visor registrado en /gods-eye "
        "(API en /api/globe/*, OSINT en /api/globe/osint/*, "
        "memoria en /api/globe/memoria)"
    )


# ── Servidor de pruebas ──────────────────────────────────────


def _main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="Visor 3D de Daniela OS")
    p.add_argument("--puerto", type=int, default=8090)
    p.add_argument(
        "--host", default="127.0.0.1", help="por defecto solo localhost (no exponer a la LAN)"
    )
    args = p.parse_args()

    try:
        from flask import Flask
    except ImportError:
        print("Flask no instalado: pip install flask", file=sys.stderr)
        return 1

    if not os.path.isdir(os.path.join(VENDOR_DIR, "Widgets")):
        print("AVISO: falta el vendor de Cesium. Ejecuta:", file=sys.stderr)
        print("  python scripts/setup_gev_vendor.py", file=sys.stderr)

    app = Flask(__name__)
    register_gev_routes(app)
    print(f"abre http://{args.host}:{args.puerto}/gods-eye")
    app.run(host=args.host, port=args.puerto, debug=False)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
