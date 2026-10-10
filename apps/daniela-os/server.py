import os
import sys
from pathlib import Path


def _base_proyecto() -> str:
    """Raiz del proyecto, inmune a la profundidad de este fichero.

    En el host `server.py` vive en `daniela-os/`, asi que subir niveles
    da la raiz del repo y todo resuelve. En el contenedor NO: el Dockerfile hace
    `COPY ./daniela-os/server.py ./server.py`, de modo que el fichero acaba en
    `/app/server.py` y contar niveles da `/`, no `/app`.

    Medido el 2026-09-21 dentro de `aig-daniela`: `BASE` valia `/` y los siete
    `sys.path` de abajo apuntaban a `/aig-optimization/...`, que no existe. Cinco
    fases morian en silencio -- `frontend`, `sse`, `health`, `obs`, `conn` -- y
    `/api/status` seguia anunciando "SSE, Health Checks, Observability,
    Connection Pooling" que nunca llegaban a registrarse.

    Se busca un marcador en vez de contar niveles: el mismo fichero vale para el
    host y para la imagen.

    ⚠️ El marcador NO puede ser `optimization/`. El 2026-09-22 esa carpeta se
    llamaba `aig-optimization/`, y una imagen construida antes del renombrado
    (comprobado en `aig-daniela`: tiene `/app/aig-optimization` y NO tiene
    `/app/optimization`) no lo encontraria, volveria al ultimo recurso y
    devolveria `/`.

    ⚠️ Tampoco vale `(core, daniela-os)`: `daniela-os/` TENIA esos dos
    directorios (falso positivo el 2026-10-03: BASE salia `aig/daniela-os` y
    `aig_shared` no se encontraba). El par actual — `tests/` + `pyproject.toml`
    — solo existe en la raiz del repo.
    """
    aqui = os.path.dirname(os.path.abspath(__file__))
    candidatos = [aqui]
    p = aqui
    while True:
        padre = os.path.dirname(p)
        if padre == p:
            break
        candidatos.append(padre)
        p = padre
    for c in candidatos:
        if os.path.isdir(os.path.join(c, "tests")) and os.path.isfile(
            os.path.join(c, "pyproject.toml")
        ):
            return c
    # Ultimo recurso: el comportamiento historico (dos niveles arriba).
    return os.path.dirname(aqui)


BASE = _base_proyecto()
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "daniela-os"))  # gev_proxy, phone/...
sys.path.insert(0, os.path.join(BASE, "shared"))  # paquete aig_shared (aig-shared/ de la raiz)
sys.path.insert(0, os.path.join(BASE, "optimization"))
# Host: el codigo de optimizacion sigue en `aig-optimization/` (la imagen lo
# renombra a `optimization/`; por eso se insertan las dos variantes).
for _opt_dir in ("cache", "sse", "health", "observe", "conn"):
    sys.path.insert(0, os.path.join(BASE, "aig-optimization", _opt_dir))
sys.path.insert(0, os.path.join(BASE, "optimization", "cache"))
sys.path.insert(0, os.path.join(BASE, "optimization", "sse"))
sys.path.insert(0, os.path.join(BASE, "optimization", "health"))
sys.path.insert(0, os.path.join(BASE, "optimization", "observe"))
sys.path.insert(0, os.path.join(BASE, "optimization", "conn"))


# NOTE: sys.path bootstrap above must precede these imports (E402 intencional).
from flask import Flask, jsonify, request, send_from_directory  # noqa: E402
from flask_cors import CORS  # noqa: E402
from flask_socketio import SocketIO  # noqa: E402

from core.auth.casbin_auth import create_auth_middleware  # noqa: E402
from core.config.paths import WEB_PORT, load_env, validate_env  # noqa: E402
from core.message_broker import Event, get_in_memory_bus  # noqa: E402
from core.service_registry import register_service, update_heartbeat  # noqa: E402

# E-47: Load .env (single source of truth) + validate critical keys
load_env()
validate_env()

# Initialize new integrations (optional - fail open if deps missing in container)
try:
    from core.observability.pyroscope_integration import init_daniela_profiler

    init_daniela_profiler()
except Exception as e:
    print(f"[Daniela] Pyroscope init skipped: {e}")

try:
    from core.observability.langfuse_integration import setup_langfuse

    langfuse = setup_langfuse()
except Exception as e:
    print(f"[Daniela] Langfuse init skipped: {e}")
    langfuse = None

try:
    from core.memory.mem0_integration import get_memory_manager

    memory_manager = get_memory_manager()
except Exception as e:
    print(f"[Daniela] mem0 init skipped: {e}")
    memory_manager = None

try:
    from core.knowledge.llamaindex_rag import get_rag

    rag = get_rag()
except Exception as e:
    print(f"[Daniela] RAG init skipped: {e}")
    rag = None

# Los prefijos de `/api/*` del visor COMPLETO (el God's Eye View original) tienen
# que quedar fuera del muro JWT.
#
# Por que: el original es codigo de terceros y hace `fetch('/api/opensky')` sin
# ninguna cabecera. No vamos a parchearlo para que mande un `Authorization`, asi
# que si el middleware los intercepta, el visor CARGA (las rutas HTML no pasan
# por el muro, porque no empiezan por /api/) pero se queda **sin datos en vivo**.
#
# La lista sale del propio `gev_proxy` para que no haya dos fuentes de verdad: es
# exactamente la superficie que Daniela ya proxea. Nuestras rutas (`/api/globe`,
# `/api/cc`, `/api/billing`, `/api/i18n`, `/api/gev`...) NO coinciden con ninguno
# de esos prefijos, asi que siguen protegidas.
try:
    import gev_proxy as _gev_proxy  # antes `from gev import gev_proxy` (paquete

    # gev/ fusionado en daniela-os/ en la reestructura 2026-10-03)
    _prefijos_publicos = tuple(f"/api/{p}" for p in _gev_proxy.PREFIJOS_API)
except Exception:  # noqa: BLE001
    # Sin aig (modo autonomo) no hay visor completo que eximir.
    _prefijos_publicos = ()

app = Flask(__name__, static_folder="web")
CORS(app, origins=["http://localhost:9200", "http://localhost:9300"])
socketio = SocketIO(
    app,
    cors_allowed_origins=["http://localhost:9200", "http://localhost:9300"],
    async_mode="threading",
)
create_auth_middleware(
    app,
    public_paths={"/api/dashboard/services", "/api/dashboard/events"},
    public_prefixes=_prefijos_publicos,
)

# Casbin authorization middleware (optional)
try:
    from core.auth.casbin_auth import get_enforcer

    enforcer = get_enforcer()
except Exception as e:
    print(f"[Daniela] Casbin init skipped: {e}")
    enforcer = None


# 2026-10-04 (S14): conectar el enforcer casbin al flujo de auth. Corre
# DESPUES del middleware JWT (que define request.user). Fail-open para sujetos
# sin politicas gestionadas (no rompe consumidores existentes); el wildcard
# admin ya se elimino, asi que un subject con politicas solo accede a lo que
# estas le conceden.
@app.before_request
def _casbin_enforce():
    if enforcer is None or not hasattr(request, "user"):
        return None
    sub = request.user.get("sub", "")
    if not sub or not enforcer.get_filtered_policy(0, sub):
        return None
    if not enforcer.enforce(sub, request.path, request.method):
        return jsonify({"error": "permiso denegado (casbin)"}), 403
    return None


# Event bus
event_bus = get_in_memory_bus("daniela")

# Initialize LangGraph orchestrator (optional)
try:
    from core.orchestration.langgraph_orchestrator import LangGraphOrchestrator, create_aig_agents

    aig_agents = create_aig_agents()
    langgraph_orchestrator = LangGraphOrchestrator(aig_agents)
except Exception as e:
    print(f"[Daniela] LangGraph init skipped: {e}")
    aig_agents = None
    langgraph_orchestrator = None

failed_phases = []


def _safe_register(name, fn):
    try:
        fn()
    except Exception as e:
        failed_phases.append({"phase": name, "error": str(e)[:200]})
        print(f"[Daniela] Phase '{name}' FAILED: {e}")


def _cargar_integrador():
    """Carga el integrador `daniela.py` POR RUTA, no por nombre.

    ⚠️ `import daniela` NO sirve. Hay dos cosas llamadas `daniela`:
      * `/app/daniela.py`        -> el integrador, con `registrar()`
      * `/app/core/daniela/`     -> un PAQUETE, sin `registrar()`

    Y `core/` se inserta ANTES que la raiz en `sys.path`, asi que el nombre
    desnudo resuelve al paquete. Medido dentro del contenedor:

        sys.path[:2]     -> ['/app/core', '/app/gev', ...]
        daniela.__file__ -> /app/core/daniela/__init__.py
        hasattr(daniela, 'registrar') -> False

    Consecuencia: la fase `aig` moria con "module 'daniela' has no
    attribute 'registrar'" y con ella se quedaban fuera el visor 3D, las capas
    OSINT, el Command Center, el idioma y la facturacion (428 rutas en vez de
    ~506).

    Antes del aplanado el import era `aig.daniela`, que no colisionaba con
    nada; el aplanado lo dejo en `daniela` y aparecio el choque.

    Se prueban las profundidades porque `server.py` corre en dos sitios y
    la reestructura del 2026-09-22 anadio un nivel:
      * contenedor: `COPY ./daniela-os/server.py ./server.py` -> `/app/server.py`,
        y el integrador entra aparte (`COPY ./core/daniela.py ./daniela.py`)
        -> HERMANO (primer candidato).
      * host (2026-10-04, P1 reestructura): `<repo>/daniela-os/server.py` ->
        el integrador vive en `<repo>/core/daniela.py` (segundo candidato;
        anexo del aplanado: antes vivia un nivel mas abajo, en
        `daniela-os/daniela-os/server.py`, y el camino era a
        `parent.parent.parent/core/daniela.py`).
      * el resto de candidatos son historias (2026-09-22 y 2026-10-03).

    ⚠️ Si vuelves a mover `daniela-os/`, esta lista hay que ajustarla: el numero
    de `.parent` depende de la profundidad de `server.py`, no de donde este
    `daniela.py`.
    """
    import importlib.util

    for candidata in (
        Path(__file__).parent / "daniela.py",
        Path(__file__).parent.parent / "core" / "daniela.py",
        Path(__file__).parent.parent / "daniela.py",
        Path(__file__).parent.parent.parent / "daniela.py",
        Path(__file__).parent.parent.parent / "core" / "daniela.py",
    ):
        if candidata.is_file():
            spec = importlib.util.spec_from_file_location("daniela_integrador", candidata)
            if spec is None or spec.loader is None:  # pragma: no cover
                continue
            mod = importlib.util.module_from_spec(spec)
            # Hay que registrarlo ANTES de ejecutarlo: `dataclass` busca
            # `cls.__module__` en `sys.modules` y sin registro revienta.
            sys.modules["daniela_integrador"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("no se encontro daniela.py (integrador de aig)")


def register_all():
    """Registra lo que es PROPIO de Daniela OS + llama al integrador de aig.

    ADR-017#2: las 24 fases de Daniela que aqui se registraban ANTES
    (ambient, consciousness, proactive, emotional, embodiment, dreams,
    temporal, social, muse, guardian, sync, voice, unified, ai, health_sub,
    memory, scheduler, dashboard, epic_pc, sse, health, obs, conn y el
    catch-all pixel_guard) ahora las absorbe `daniela.py::registrar()`, que
    se invoca con la fase `aig`. Comprobado por NOMBRES uno a uno antes de
    borrar el bloque: los 24 blueprints siguen llegando a `app` y
    `pixel_guard` sigue siendo el ULTIMO (E-40, catch-all de /api/pixel/*).

    Se conservan como fases locales de ESTE servidor las 4 integraciones de
    aig que NO son de Daniela: mem0, rag, langgraph y langfuse.
    """
    import time

    t0 = time.monotonic()

    # New integrations (optional - use _safe_register to fail open)
    try:
        from core.knowledge.rag_bp import rag_bp
    except Exception as e:
        print(f"[Daniela] rag_bp import skipped: {e}")
        rag_bp = None
    try:
        from core.memory.mem0_bp import memory_bp as mem0_bp
    except Exception as e:
        print(f"[Daniela] mem0_bp import skipped: {e}")
        mem0_bp = None
    try:
        from core.orchestration.langgraph_bp import langgraph_bp
    except Exception as e:
        print(f"[Daniela] langgraph_bp import skipped: {e}")
        langgraph_bp = None
    try:
        from core.observability.langfuse_bp import langfuse_bp
    except Exception as e:
        print(f"[Daniela] langfuse_bp import skipped: {e}")
        langfuse_bp = None
    try:
        from iot_hub.api import iot_bp
    except Exception as e:
        print(f"[Daniela] iot_bp import skipped: {e}")
        iot_bp = None

    def _opt(modname):
        mod = __import__(modname)
        bp = getattr(mod, [n for n in dir(mod) if n.endswith("_bp")][0])
        app.register_blueprint(bp)

    for name, fn in [
        ("mem0", lambda: app.register_blueprint(mem0_bp)),
        ("rag", lambda: app.register_blueprint(rag_bp)),
        ("langgraph", lambda: app.register_blueprint(langgraph_bp)),
        ("langfuse", lambda: app.register_blueprint(langfuse_bp)),
        # IoT real (ADR-IOT-HUB): /api/iot/* = HA + MQTT + ESPHome + descubrimiento
        ("iot", lambda: app.register_blueprint(iot_bp)),
        # FASE `frontend` RETIRADA el 2026-09-22.
        # `frontend/` se archivo en `archives/frontend/` (isla antigua, sustituida
        # por Daniela OS + God's Eye). Se quita la fase en vez de dejarla: una
        # fase que SIEMPRE falla hace que `/api/status` reporte un fallo
        # permanente y enmascara los fallos de verdad.
        # Para recuperarla: mover `archives/frontend/` a la raiz, anadir su COPY
        # al Dockerfile y restaurar aqui
        #   ("frontend", lambda: __import__("frontend").register_frontend(app)),
        # Daniela es todo: una sola llamada integra el visor 3D, las capas
        # OSINT, el Command Center, el idioma, la facturacion de aig Y las
        # fases de Daniela (ADR-017#2). Se carga por RUTA a proposito:
        # `import daniela` resolveria al paquete `core/daniela/`, que no tiene
        # `registrar`. Ver `_cargar_integrador`.
        ("aig", lambda: _cargar_integrador().registrar(app, failed_phases, socketio=socketio)),
    ]:
        _safe_register(name, fn)

    dt = (time.monotonic() - t0) * 1000
    print(
        f"[Daniela] Registered {len(list(app.url_map.iter_rules()))} routes in {dt:.0f}ms, failed={len(failed_phases)}"
    )


# Absoluto al fichero: el servidor funciona aunque el CWD sea otro
# (tests lausan desde la raiz; gunicorn/systemd arrancan desde /).
_WEB_DIR = Path(__file__).resolve().parent / "web"


@app.route("/")
def index():
    return send_from_directory(_WEB_DIR, "index.html")


@app.route("/mobile")
def mobile():
    return send_from_directory(_WEB_DIR, "mobile.html")


@app.route("/api/status")
def status():
    return jsonify(
        {
            "name": "Daniela",
            "version": "1.0.0",
            "modules": 107,
            "total_systems": 114,
            "phases": [
                "Ambient",
                "Consciousness",
                "Proactive",
                "Emotional",
                "Embodiment",
                "Dreams",
                "Temporal",
                "Social",
                "Muse",
                "Guardian",
                "Sync",
                "Voice",
                "Unified",
                "AI",
                "Optimization",
            ],
            "optimizations": [
                "Redis Caching",
                "SSE",
                "Health Checks",
                "Observability",
                "Connection Pooling",
            ],
            "status": "alive",
            "registry": "active",
            "events": "active",
            "routes": len([r for r in app.url_map.iter_rules() if r.endpoint != "static"]),
            "failed_phases": failed_phases,
        }
    )


@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    update_heartbeat("daniela")
    return jsonify({"status": "ok"})


@app.route("/api/routes")
def routes():
    """Full route index grouped by prefix (fixes 404 discoverability)."""
    groups = {}
    for r in app.url_map.iter_rules():
        if r.endpoint == "static":
            continue
        prefix = "/" + "/".join(str(r).strip("/").split("/")[:2])
        groups.setdefault(prefix, []).append(
            {"path": str(r), "methods": sorted(r.methods - {"HEAD", "OPTIONS"})}
        )
    return jsonify({"total": sum(len(v) for v in groups.values()), "groups": groups})


@app.route("/api/phases")
def phases():
    """Phase list with route counts + failed phases."""
    counts = {}
    for r in app.url_map.iter_rules():
        parts = str(r).strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api":
            counts[parts[1]] = counts.get(parts[1], 0) + 1
    return jsonify({"phases": counts, "failed": failed_phases})


register_all()

# Start dashboard service poller (import tardio: evita circular con register_all).
from core.dashboard import start_poller  # noqa: E402

start_poller()


# WebSocket handlers for dashboard
@socketio.on("connect")
def handle_connect():
    print(f"[Dashboard] Client connected: {request.sid}")


@socketio.on("disconnect")
def handle_disconnect():
    print(f"[Dashboard] Client disconnected: {request.sid}")


@socketio.on("request_status")
def handle_request_status():
    from core.dashboard import get_all_status

    socketio.emit("status_update", get_all_status())


if __name__ == "__main__":
    # Register with service registry
    register_service(
        name="daniela",
        host="0.0.0.0",
        port=WEB_PORT,
        category="AI",
        version="1.0.0",
        endpoints=[
            "/api/status",
            "/api/ambient",
            "/api/consciousness",
            "/api/emotional",
            "/api/dashboard/services",
        ],
    )

    # Publish startup event
    event = Event(
        type="service.startup", payload={"service": "daniela", "port": WEB_PORT}, source="daniela"
    )
    event_bus.publish_sync("startup", event)

    # E-40: Start pixel health checker in background
    from core.pixel_guard import start_guard

    start_guard()

    # E-42: Start agent scheduler in background
    from core.scheduler import start_scheduler

    start_scheduler()

    print(f"[Daniela] Starting on port {WEB_PORT}...")
    socketio.run(app, host="0.0.0.0", port=WEB_PORT, debug=False, allow_unsafe_werkzeug=True)
