#!/usr/bin/env python3
"""
daniela — Daniela es todo: punto de entrada unico
==========================================================
Daniela estaba repartida: `daniela-os/server.py` registraba sus
fases (ambient, consciousness, ...) y los modulos de `aig/` vivian
aparte, sin que nadie los conectara. Resultado: el visor 3D, las capas OSINT,
el Command Center y la facturacion no existian dentro del servidor real.

Este modulo es la respuesta a "Daniela Omnipresente es Daniela": una sola
llamada registra TODO aig en la app que ya existe, sin duplicar
servidores ni puertos.

    from daniela import registrar
    registrar(app)          # <- una linea y Daniela queda completa

Devuelve un informe honesto: que se registro y que fallo, con el motivo.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

_DIR = os.path.dirname(os.path.abspath(__file__))


def _raiz_repo() -> str:
    """Raiz real del proyecto.

    `daniela.py` se aplano de `aig/` a la raiz (2026-09-29), asi que
    `dirname(__file__)` dejo de ser el directorio que CONTIENE el proyecto y
    pasó a ser el propio proyecto; con el calculo viejo `_RAIZ` apuntaba al
    padre de la raiz y `core/` ni existia. Se busca un marcador, como en
    `health_checks._raiz_repo`: es inmune a la profundidad.
    """
    aqui = Path(_DIR)
    for c in (aqui, *aqui.parents):
        if (c / ".git").exists() or (c / "tests" / "conftest.py").exists():
            return str(c)
    return os.path.dirname(_DIR)


_RAIZ = _raiz_repo()
for _p in (_RAIZ, _DIR, os.path.join(_RAIZ, "core")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ADR-017#2: omnipresente es una propiedad de Daniela OS — sus fases se
# absorben en `registrar()`, no se lanzan como proceso paralelo. Rutas con
# `isdir` para que valgan en el host (raiz del repo) y en el contenedor
# (`daniela.py` vive en /app). `_DIR`, no `_RAIZ`: en la imagen no hay `.git`
# ni `tests/conftest.py` y `_raiz_repo()` degrada a `/`.
# (El antiguo `_OMNI` = `daniela-omnipresente/` se fusiono en `daniela-os/`
# el 2026-10-03: ya no hay directorio que insertar en sys.path.)
# Optimizacion: `aig-optimization/` es el canonico (ver `server.py` de
# daniela-omnipresente); `optimization/` es el renombrado que usa la imagen
# (`gev/daniela-os/Dockerfile` solo copia ese). Se prueban los dos, con
# el canonico primero para que gane en el host, donde existen ambos.
# Reestructura 2026-10-03: en el host `daniela.py` vive en `core/` (antes en
# la raiz), asi que se prueba `_DIR` (imagen: daniela.py en /app) y luego
# `_RAIZ` (host: repo root). Sin el segundo, las fases sse/health/obs/conn
# fallan con `No module named 'sse_server'` al correr `registrar()` en tests.
for _raiz_opt in (_DIR, _RAIZ):
    for _opt_base in ("optimization", "aig-optimization"):
        _o = os.path.join(_raiz_opt, _opt_base)
        if not os.path.isdir(_o):
            continue
        for _sub in ("", "cache", "sse", "health", "observe", "conn"):
            _s = os.path.join(_o, _sub) if _sub else _o
            if os.path.isdir(_s) and _s not in sys.path:
                sys.path.insert(0, _s)

VERSION = "2.0.0"

# Fases que componen Daniela. Cada una es (nombre, importador, funcion).
# El orden importa: el visor registra sus propias sub-rutas (idioma,
# Command Center, OSINT, facturacion) al vuelo.
FASES = (
    "visor",            # globo 3D + /api/globe/*  (+ i18n, Command Center, OSINT, billing)
    "visor_completo",   # el God's Eye View original bajo el mismo origen (/gods-eye/pro/)
    "gev_api",          # /api/gev/*: enlaces, capas, geocercas, timeline (visor <-> Daniela)
    "ubicacion",        # geolocalizacion de la Sede
    "negocio",          # clientes / empresas
    "acceso",           # control de acceso admin vs cliente
    # ADR-017#2: omnipresente absorbido — antes vivian en
    # `daniela-omnipresente/server.py::register_all()`, ahora se registran
    # aqui, en el servidor unico. `pixel_guard` va la ULTIMA: es el catch-all
    # de /api/pixel/* (E-40).
    "ambient",
    "consciousness",
    "proactive",
    "emotional",
    "embodiment",
    "dreams",
    "temporal",
    "social",
    "muse",
    "guardian",
    "sync",
    "voice",
    "unified",
    "ai",
    "health_sub",
    "memory",
    "scheduler",
    "dashboard",
    "epic_pc",
    "sse",
    "health",
    "obs",
    "conn",
    "pixel_guard",
)


def _informe() -> dict[str, Any]:
    return {"version": VERSION, "registradas": [], "fallidas": [],
            "ts": time.time()}


def _register_db_health_endpoint(app: Any) -> None:
    """Expose read-only health information for canonical SQLite databases."""
    from core.data.db_optimizer import DatabaseManager

    if "_db_health" in app.view_functions:
        return

    @app.get("/api/db/health")
    def _db_health() -> dict[str, Any]:
        databases: list[dict[str, Any]] = []
        for db_path in DatabaseManager().list_database_files():
            entry: dict[str, Any] = {
                "path": str(db_path),
                "exists": db_path.is_file(),
                "ok": False,
            }
            try:
                with sqlite3.connect(str(db_path), timeout=3) as connection:
                    entry["size_bytes"] = db_path.stat().st_size
                    entry["journal_mode"] = connection.execute(
                        "PRAGMA journal_mode"
                    ).fetchone()[0]
                    entry["page_size"] = connection.execute(
                        "PRAGMA page_size"
                    ).fetchone()[0]
                    integrity = connection.execute(
                        "PRAGMA integrity_check"
                    ).fetchone()[0]
                    entry["integrity"] = integrity
                    entry["ok"] = integrity == "ok"
            except (OSError, sqlite3.Error) as exc:
                entry["error"] = str(exc)[:200]
            databases.append(entry)
        return {
            "ok": all(database["ok"] for database in databases),
            "count": len(databases),
            "databases": databases,
        }


def _register_stack_status_endpoint(app: Any) -> None:
    """Report Compose service state without starting or mutating containers."""
    from core.orchestration.container_status import compose_stack_status

    if "_stack_status" in app.view_functions:
        return

    @app.get("/api/stack/status")
    def _stack_status() -> dict[str, Any]:
        return compose_stack_status(_DIR)


def _fase(informe: dict[str, Any], nombre: str, fn: Callable[[], Any]) -> Any:
    """Ejecuta una fase sin dejar que tumbe el arranque de Daniela."""
    try:
        res = fn()
        informe["registradas"].append(nombre)
        return res
    except Exception as e:  # noqa: BLE001
        informe["fallidas"].append({"fase": nombre, "error": str(e)[:200]})
        print(f"[Daniela] fase '{nombre}' FALLO: {e}")
        return None


def registrar(app, failed_phases: list[dict] | None = None,
              socketio: Any = None) -> dict[str, Any]:
    """Registra TODO aig en `app` (el servidor unico de Daniela).

    `failed_phases`, si se pasa, se rellena con las fases que fallaron para
    que el endpoint /api/health de Daniela pueda contarlo.

    `socketio`, si se pasa, es el SocketIO del servidor que nos llama
    (ADR-017#2): el dashboard se cablea al SUYO, que ya tiene montados sus
    handlers de `connect`/`disconnect`/`request_status`. Si no se pasa, la
    fase `dashboard` crea uno propio (defensivo, `async_mode` por defecto) y
    le cablea los handlers aqui, para que `registrar(app)` suelto funcione.
    """
    informe = _informe()
    _register_db_health_endpoint(app)
    _register_stack_status_endpoint(app)

    def _anotar(nombre: str, error: str) -> None:
        if failed_phases is not None:
            failed_phases.append({"phase": f"aig.{nombre}", "error": error})

    # ── Visor + su API completa ──
    def _visor() -> Any:
        # 2026-10-03: `gev/server.py` -> `daniela-os/server.py` (fusion de gev/
        # en daniela-os/). 2026-10-04 (P1): `daniela-os/server.py` es ahora la
        # APP PRINCIPAL (anidado fusionado); el modulo del visor es
        # `daniela-os/gev_server.py`. Se carga POR RUTA con nombre propio para
        # no pisar el module `server` de la app en los tests.
        import importlib.util
        ruta = Path(__file__).resolve().parent.parent / "daniela-os" / "gev_server.py"
        spec = importlib.util.spec_from_file_location("gev_server_mod", ruta)
        if spec is None or spec.loader is None:  # pragma: no cover
            raise ImportError(f"no se pudo cargar {ruta}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["gev_server_mod"] = mod
        spec.loader.exec_module(mod)
        mod.register_gev_routes(app)
        return True

    _fase(informe, "visor", _visor)

    # ── Visor completo: el God's Eye View ORIGINAL, con todas sus opciones ──
    # No se reimplementa ni se mete en un iframe (su servidor manda
    # X-Frame-Options: DENY y sus 22 proveedores de /api/* son middleware de
    # Vite, no sirven en un build estatico). Se lanza su servidor como servicio
    # y se expone bajo el mismo origen de Daniela con proxy inverso.
    def _visor_completo() -> Any:
        # 2026-10-03: `gev/gev_proxy.py` -> `daniela-os/gev_proxy.py` (autocon-
        # tenido: inserta su directorio como hace gev_integration).
        _d = str(Path(__file__).resolve().parent.parent / "daniela-os")
        if _d not in sys.path:
            sys.path.insert(0, _d)
        import gev_proxy
        gev_proxy.registrar_gev_proxy(app)
        e = gev_proxy.estado()
        # Arranque perezoso pero adelantado: si esta disponible, se levanta en
        # segundo plano para que la primera visita no espere el arranque en frio.
        gev_proxy.precalentar()
        if not e["disponible"]:
            # No es un fallo de Daniela: es una capacidad que este despliegue no
            # tiene. Se declara y se sigue.
            print(f"[Daniela] visor completo no disponible: {e.get('motivo')}")
        return e

    _fase(informe, "visor_completo", _visor_completo)

    # ── API puente visor <-> Daniela: /api/gev/* ──
    # Enlaces profundos al globo, capas, geocercas, eventos y timeline. Es lo
    # que permite que Daniela ENSENE en el globo de lo que habla, no solo que
    # lo cuente: `gev_integration.enriquecer_respuesta()` la invoca desde el
    # chat para anadir el enlace ya enfocado.
    def _gev_api() -> Any:
        # 2026-10-03: `gev_integration.py` de la raiz -> `engine/gev_integration.py`.
        _e = str(Path(__file__).resolve().parent.parent / "engine")
        if _e not in sys.path:
            sys.path.insert(0, _e)
        import gev_integration
        antes = len(list(app.url_map.iter_rules()))
        gev_integration.register_gev_routes(app)
        return len(list(app.url_map.iter_rules())) - antes

    _fase(informe, "gev_api", _gev_api)

    # ── Ubicacion de la Sede (no registra rutas, pero valida el subsistema) ──
    def _ubicacion() -> Any:
        import location as loc
        u = loc.actual()
        return {"etiqueta": u.etiqueta, "fuente": u.fuente}

    _fase(informe, "ubicacion", _ubicacion)

    # ── Negocio: clientes/empresas ──
    def _negocio() -> Any:
        import business_store as bs
        return bs.resumen().get("total", 0)

    _fase(informe, "negocio", _negocio)

    # ── Acceso: control admin vs cliente ──
    def _acceso() -> Any:
        import access as acc
        return sorted(r.value for r in acc.Rol)

    _fase(informe, "acceso", _acceso)

    # ── ADR-017#2: omnipresente absorbido ──
    # Las 20 fases + 4 _opt que antes registraba
    # `daniela-omnipresente/server.py::register_all()`. Imports perezosos en
    # closures (mismo patron que arriba): `daniela.py` no paga el coste ni
    # rompe si un modulo falta; `_fase` lo cuenta como fallo honesto.
    # NO se definen aqui `/`, `/mobile`, `/api/status`, `/api/heartbeat`,
    # `/api/routes` ni `/api/phases`: son del shim (`server.py`), no de Daniela.
    def _ambient() -> Any:
        from ambient import register_ambient
        register_ambient(app)
        return True

    def _consciousness() -> Any:
        from consciousness import register_consciousness
        register_consciousness(app)
        return True

    def _proactive() -> Any:
        from proactive import register_proactive
        register_proactive(app)
        return True

    def _emotional() -> Any:
        from emotional import register_emotional
        register_emotional(app)
        return True

    def _embodiment() -> Any:
        from embodiment import register_embodiment
        register_embodiment(app)
        return True

    def _dreams() -> Any:
        from dreams import register_dreams
        register_dreams(app)
        return True

    def _temporal() -> Any:
        from temporal import register_temporal
        register_temporal(app)
        return True

    def _social() -> Any:
        from social import register_social
        register_social(app)
        return True

    def _muse() -> Any:
        from muse import register_muse
        register_muse(app)
        return True

    def _guardian() -> Any:
        from guardian import register_guardian
        register_guardian(app)
        return True

    def _sync() -> Any:
        from core.cross_device_sync import sync_bp
        app.register_blueprint(sync_bp)
        return True

    def _voice() -> Any:
        from core.voice.voice_activation import voice_activation_bp
        app.register_blueprint(voice_activation_bp)
        return True

    def _unified() -> Any:
        from core.unified_bridge import unified_bp
        app.register_blueprint(unified_bp)
        return True

    def _ai() -> Any:
        from core.ai_bridge import ai_bp
        app.register_blueprint(ai_bp)
        return True

    def _health_sub() -> Any:
        from core.health_checks import health_bp
        app.register_blueprint(health_bp)
        return True

    def _memory() -> Any:
        from core.memory_rag_ollama import memory_bp
        app.register_blueprint(memory_bp)
        return True

    def _scheduler() -> Any:
        from core.scheduler import scheduler_bp
        app.register_blueprint(scheduler_bp)
        return True

    def _dashboard() -> Any:
        from core.unified_dashboard import create_dashboard_blueprint
        # ADR-017#2: si el servidor que nos llama pasa SU socketio, este ya
        # tiene montados `connect`/`disconnect`/`request_status` (son suyos,
        # estan en su `server.py`); volver a cablearlos aqui haria que
        # `request_status` emitiera `status_update` DOS veces. Solo se
        # cablean los handlers cuando el socketio es NUESTRO (creado aqui
        # para que `registrar(app)` suelto quede funcional).
        _sio_propio = socketio is None
        if _sio_propio:
            try:
                from flask_socketio import SocketIO
                _sio = SocketIO(app)
            except Exception:
                _sio = None
        else:
            _sio = socketio
        app.register_blueprint(create_dashboard_blueprint(_sio))
        if _sio_propio and _sio is not None:
            @_sio.on("connect")
            def _h_connect() -> None:
                from flask import request
                print(f"[Dashboard] Client connected: {request.sid}")

            @_sio.on("disconnect")
            def _h_disconnect() -> None:
                from flask import request
                print(f"[Dashboard] Client disconnected: {request.sid}")

            @_sio.on("request_status")
            def _h_request_status() -> None:
                from core.unified_dashboard import get_all_status
                _sio.emit("status_update", get_all_status())
        return True

    def _epic_pc() -> Any:
        from core.epic_pc_manager import create_epic_pc_blueprint
        app.register_blueprint(create_epic_pc_blueprint())
        return True

    def _opt(modname: str) -> Any:
        mod = __import__(modname)
        bp = getattr(mod, [n for n in dir(mod) if n.endswith("_bp")][0])
        app.register_blueprint(bp)
        return True

    def _sse() -> Any:
        return _opt("sse_server")

    def _health() -> Any:
        return _opt("health_checker")

    def _obs() -> Any:
        return _opt("observability")

    def _conn() -> Any:
        return _opt("connection_pool")

    def _pixel_guard() -> Any:
        from core.pixel_guard import pixel_guard_bp
        app.register_blueprint(pixel_guard_bp)
        return True

    # E-40: `pixel_guard` la ULTIMA — catch-all de /api/pixel/*.
    for _nombre, _fn in [
        ("ambient", _ambient),
        ("consciousness", _consciousness),
        ("proactive", _proactive),
        ("emotional", _emotional),
        ("embodiment", _embodiment),
        ("dreams", _dreams),
        ("temporal", _temporal),
        ("social", _social),
        ("muse", _muse),
        ("guardian", _guardian),
        ("sync", _sync),
        ("voice", _voice),
        ("unified", _unified),
        ("ai", _ai),
        ("health_sub", _health_sub),
        ("memory", _memory),
        ("scheduler", _scheduler),
        ("dashboard", _dashboard),
        ("epic_pc", _epic_pc),
        ("sse", _sse),
        ("health", _health),
        ("obs", _obs),
        ("conn", _conn),
        ("pixel_guard", _pixel_guard),
    ]:
        _fase(informe, _nombre, _fn)

    for f in informe["fallidas"]:
        _anotar(f["fase"], f["error"])

    print(f"[Daniela] aig {VERSION} integrado: "
          f"{len(informe['registradas'])}/{len(FASES)} fases OK"
          + (f", fallidas: {[f['fase'] for f in informe['fallidas']]}"
             if informe["fallidas"] else ""))
    return informe


def estado() -> dict[str, Any]:
    """Estado de los subsistemas de Daniela, sin tocar la app."""
    informe = _informe()
    _fase(informe, "ubicacion", lambda: __import__(
        "location", fromlist=["x"]).actual().etiqueta)
    _fase(informe, "negocio", lambda: __import__(
        "business_store", fromlist=["x"]).resumen().get("total", 0))
    _fase(informe, "visor", lambda: __import__(
        "gev.gev_server", fromlist=["x"]).TITULO)
    return informe
