"""
E-42: Agent Scheduler — revives the 6 dead agents with real schedules.

Agents:
  - agent_calendario: daily briefing (8:00), reminders (every 30min), conflict detection (hourly)
  - agent_correo: inbox check (every 15min)
  - agent_documentos: weekly summary (Monday 9:00), meeting minutes (on demand)
  - agent_redes: analytics (daily 18:00)
  - agent_vigia: system health (every 5min), git backup check (hourly)
  - agent_epic_ideas: audit (daily 23:00)

All executions are logged to scheduler_locks.db.
"""

import os
import sqlite3
import sys
import threading
import time
import traceback

from flask import Blueprint, jsonify, request

scheduler_bp = Blueprint("scheduler", __name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Find repo root: check if server.py exists (in container, agents are at /app/agents/)
# ⚠️ 2026-09-20: el refactor movio `server.py` a `core/server.py`, asi que el
# marcador anterior ya no existia en la raiz y REPO_ROOT caia a "/app" incluso
# en local. Eso dejaba AGENT_PATHS apuntando a rutas inexistentes y todos los
# agentes del scheduler devolvian None. Se aceptan los dos marcadores.
#
# 🔴 2026-09-22: la reestructura movio este fichero a
# `gev/daniela-os/shared/scheduler.py`, UN NIVEL MAS ABAJO, y el marcador
# suelto `server.py` se convirtio en un DECOY: a 3 niveles hay
# `<repo>/gev/`, que tiene su propio `server.py` (el del visor). El bucle
# aceptaba esa carpeta como raiz y los 5 agentes volvian a dar None. Por eso el
# marcador ya no es "un server.py cualquiera": hacen falta los DOS, y `agents/`
# es el que `<repo>/gev/` no tiene.
#
# Comprobado en las dos ubicaciones:
#   host      : <repo>/gev/daniela-os/shared/scheduler.py -> <repo>
#   contenedor: /app/shared/scheduler.py                      -> /app (por defecto)
#
# 🧭 2026-09-30 (Fase 2 del triage): `core/server.py` desaparecio en 9194688e
# y con el los 10 tests de `tests/core/test_scheduler.py` (REPO_ROOT volvia a
# caer en "/app" y todos los agentes daban None). Restaurado en este mismo
# commit. Se valoro endurecer el marcador con `pyproject.toml`, que esta en la
# raiz y no se mueve con reestructuras... pero NO entra en la imagen:
# `grep -n COPY gev/daniela-os/Dockerfile` no copia `pyproject.toml` (ni
# `tests/` ni `config/`), asi que anadirlo a la tupla habria ROTO la deteccion
# en el contenedor (habria un `all(...)` que falla en /app). Marcador actual
# mantenido: los DOS son copiados por la imagen (`COPY ./core/` y `COPY ./agents/`).
_MARCADORES = (os.path.join("core", "server.py"), "agents")


def _es_raiz(c):
    """True si `c` es la raiz del repo (no una carpeta que se le parece)."""
    return all(os.path.exists(os.path.join(c, m)) for m in _MARCADORES)


# 2026-10-05: fusion `daniela-os/shared/` -> `shared/`. El fichero esta AHORA a
# 2 niveles de la raiz (antes 3 en `daniela-os/shared/`, 4 en
# `gev/daniela-os/shared/`). Se aceptan las tres profundidades.
_candidatos = (
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
REPO_ROOT = "/app"
for _c in _candidatos:
    if _es_raiz(_c):
        REPO_ROOT = _c
        break
DATA_DIR = os.getenv("DATA_DIR", os.path.join(REPO_ROOT, "data"))
DB_PATH = os.path.join(DATA_DIR, "scheduler_locks.db")

# Agent root paths (ADR-015: root wins, fallback to agents/ dir in container)
# ⚠️ 2026-09-20: los agentes canonicos viven ahora en `agents/` (antes
# en la raiz del repo). `scripts/agents/` es el paquete de despliegue y sirve de
# ultimo recurso. Se prueban por orden y se devuelve el primero que existe.
_AGENT_SUBDIRS = ("agents", "scripts/agents")


def _agent_path(filename):
    """Find agent file: repo root, agents/, agents/, scripts/agents/."""
    candidatos = [os.path.join(REPO_ROOT, filename)]
    candidatos += [os.path.join(REPO_ROOT, d, filename) for d in _AGENT_SUBDIRS]
    candidatos.append(os.path.join("/app", "agents", filename))
    for c in candidatos:
        if os.path.exists(c):
            return c
    return candidatos[0]  # default, will fail gracefully

AGENT_PATHS = {
    "calendario": _agent_path("agent_calendario.py"),
    "correo": _agent_path("agent_correo.py"),
    "documentos": _agent_path("agent_documentos.py"),
    "redes": _agent_path("agent_redes.py"),
    "vigia": _agent_path("agent_vigia.py"),
    "epic_ideas": _agent_path("agent_epic_ideas.py"),
}

# Schedule definitions: (agent_key, method_name, interval_seconds, description)
SCHEDULES = [
    ("calendario", "send_reminders", 1800, "Recordatorios cada 30min"),
    ("calendario", "detect_conflicts", 3600, "Detectar conflictos horarios"),
    ("calendario", "generate_briefing", 86400, "Briefing diario"),
    ("correo", "process_inbox", 900, "Revisar bandeja cada 15min"),
    ("documentos", "get_status", 86400, "Status de documentos"),
    ("vigia", "run_monitoring_cycle", 300, "Health check cada 5min"),
    ("vigia", "check_git_backup", 3600, "Verificar backup git cada hora"),
    ("redes", "get_analytics", 86400, "Analytics diario"),
    ("epic_ideas", "audit_summary", 86400, "Auditoria diaria de agentes"),
]

# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

def _get_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            method TEXT NOT NULL,
            started_at REAL,
            finished_at REAL,
            status TEXT,
            result TEXT,
            error TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_agent_runs_agent ON agent_runs(agent);
        CREATE INDEX IF NOT EXISTS idx_agent_runs_started ON agent_runs(started_at);

        CREATE TABLE IF NOT EXISTS agent_schedules (
            agent TEXT NOT NULL,
            method TEXT NOT NULL,
            interval_sec INTEGER,
            description TEXT,
            last_run REAL,
            next_run REAL,
            enabled INTEGER DEFAULT 1,
            PRIMARY KEY (agent, method)
        );
    """)
    # Upsert schedules
    for agent, method, interval, desc in SCHEDULES:
        conn.execute(
            "INSERT OR IGNORE INTO agent_schedules (agent, method, interval_sec, description, enabled) VALUES (?, ?, ?, ?, 1)",
            (agent, method, interval, desc),
        )
    conn.commit()
    conn.close()


def _log_run(agent, method, started, finished, status, result="", error=""):
    conn = _get_db()
    try:
        conn.execute(
            "INSERT INTO agent_runs (agent, method, started_at, finished_at, status, result, error) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (agent, method, started, finished, status, str(result)[:500], str(error)[:500]),
        )
        conn.execute(
            "UPDATE agent_schedules SET last_run = ?, next_run = ? WHERE agent = ? AND method = ?",
            (finished, finished + (_get_interval(agent, method) or 86400), agent, method),
        )
        conn.commit()
    finally:
        conn.close()


def _get_interval(agent, method):
    for a, m, interval, _ in SCHEDULES:
        if a == agent and m == method:
            return interval
    return 86400


# ---------------------------------------------------------------------------
# Agent Loader
# ---------------------------------------------------------------------------

_agent_instances = {}


def _get_agent(agent_key):
    """Lazy-load and cache agent instance."""
    if agent_key in _agent_instances:
        return _agent_instances[agent_key]

    path = AGENT_PATHS.get(agent_key)
    if not path or not os.path.exists(path):
        return None

    try:
        # Add repo root and agents dir to sys.path for imports
        if REPO_ROOT not in sys.path:
            sys.path.insert(0, REPO_ROOT)
        agents_dir = os.path.join(REPO_ROOT, "agents")
        if os.path.isdir(agents_dir) and agents_dir not in sys.path:
            sys.path.insert(0, agents_dir)

        import importlib.util
        spec = importlib.util.spec_from_file_location(agent_key, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Find the agent class
        class_map = {
            "calendario": "CalendarioAgent",
            "correo": "CorreoAgent",
            "documentos": "DocumentosAgent",
            "redes": "RedesAgent",
            "vigia": "VigiaAgent",
        }
        class_name = class_map.get(agent_key)
        if class_name and hasattr(mod, class_name):
            instance = getattr(mod, class_name)()
            _agent_instances[agent_key] = instance
            return instance

        # Special case: epic_ideas is a dataclass, not an agent
        if agent_key == "epic_ideas" and hasattr(mod, "AGENT_AUDITS"):
            class EpicIdeasWrapper:
                def audit_summary(self):
                    audits = mod.AGENT_AUDITS
                    result = {
                        "total_agents": len(audits),
                        "by_status": {},
                        "critical": [],
                    }
                    for a in audits:
                        result["by_status"][a.status] = result["by_status"].get(a.status, 0) + 1
                        if a.upgrade_priority == "critical":
                            result["critical"].append(a.name)
                    return result
            instance = EpicIdeasWrapper()
            _agent_instances[agent_key] = instance
            return instance
    except Exception as e:
        print(f"[Scheduler] Failed to load agent {agent_key}: {e}")
    return None


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------

def _execute_agent_method(agent_key, method_name):
    """Execute a single agent method, log the result."""
    started = time.time()
    status = "ok"
    result = ""
    error = ""

    try:
        agent = _get_agent(agent_key)
        if agent is None:
            status = "error"
            error = f"Agent {agent_key} not found or failed to load"
        elif not hasattr(agent, method_name):
            status = "error"
            error = f"Method {method_name} not found on {agent_key}"
        else:
            method = getattr(agent, method_name)
            result = method()
            if result is None:
                result = "ok"
    except Exception as e:
        status = "error"
        error = f"{type(e).__name__}: {str(e)[:300]}"
        traceback.print_exc()

    finished = time.time()
    _log_run(agent_key, method_name, started, finished, status, result, error)

    elapsed = round((finished - started) * 1000, 1)
    icon = "OK" if status == "ok" else "ERR"
    print(f"[Scheduler] {icon} {agent_key}.{method_name} ({elapsed}ms)")
    return {"agent": agent_key, "method": method_name, "status": status, "elapsed_ms": elapsed, "error": error}


# ---------------------------------------------------------------------------
# Background Loop
# ---------------------------------------------------------------------------

_stop_event = threading.Event()
_scheduler_thread = None


def _scheduler_loop():
    """Background loop that runs agents on their schedules."""
    while not _stop_event.is_set():
        now = time.time()
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT agent, method, interval_sec, next_run FROM agent_schedules WHERE enabled = 1"
            ).fetchall()
            for row in rows:
                if row["next_run"] and now >= row["next_run"]:
                    agent_key = row["agent"]
                    method_name = row["method"]
                    # Run in a separate thread to not block the loop
                    t = threading.Thread(
                        target=_execute_agent_method,
                        args=(agent_key, method_name),
                        daemon=True,
                        name=f"agent-{agent_key}-{method_name}",
                    )
                    t.start()
        finally:
            conn.close()
        _stop_event.wait(30)  # Check every 30 seconds


def start_scheduler():
    """Start the background agent scheduler."""
    global _scheduler_thread
    _init_db()
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True, name="agent-scheduler")
    _scheduler_thread.start()
    print(f"[Scheduler] Started with {len(SCHEDULES)} schedules")


def stop_scheduler():
    """Stop the scheduler."""
    _stop_event.set()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@scheduler_bp.route("/api/scheduler/status")
def scheduler_status():
    """Overview of all agent schedules."""
    conn = _get_db()
    try:
        schedules = []
        for row in conn.execute("SELECT * FROM agent_schedules ORDER BY agent, method"):
            schedules.append({
                "agent": row["agent"],
                "method": row["method"],
                "interval_sec": row["interval_sec"],
                "description": row["description"],
                "last_run": row["last_run"],
                "next_run": row["next_run"],
                "enabled": bool(row["enabled"]),
            })

        # Recent runs per agent
        agent_stats = {}
        for row in conn.execute("""
            SELECT agent, COUNT(*) as total,
                   SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END) as ok_count,
                   MAX(finished_at) as last_run
            FROM agent_runs
            GROUP BY agent
        """):
            agent_stats[row["agent"]] = {
                "total_runs": row["total"],
                "ok_count": row["ok_count"],
                "last_run": row["last_run"],
            }

        return jsonify({
            "schedules": schedules,
            "agent_stats": agent_stats,
            "total_schedules": len(schedules),
            "running": _scheduler_thread is not None and _scheduler_thread.is_alive(),
        })
    finally:
        conn.close()


@scheduler_bp.route("/api/scheduler/run", methods=["POST"])
def scheduler_run():
    """
    Manually trigger an agent method.

    Body: {"agent": "calendario", "method": "generate_briefing"}
    """
    data = request.json or {}
    agent_key = data.get("agent", "")
    method_name = data.get("method", "")

    if not agent_key or not method_name:
        return jsonify({"error": "agent and method required"}), 400

    valid = [(a, m) for a, m, _, _ in SCHEDULES]
    if (agent_key, method_name) not in valid:
        return jsonify({
            "error": f"Unknown agent/method: {agent_key}.{method_name}",
            "available": [{"agent": a, "method": m} for a, m, _, desc in SCHEDULES],
        }), 400

    result = _execute_agent_method(agent_key, method_name)
    return jsonify(result)


@scheduler_bp.route("/api/scheduler/run-all", methods=["POST"])
def scheduler_run_all():
    """Trigger all agents immediately (for testing)."""
    results = []
    for agent_key, method_name, _, _ in SCHEDULES:
        result = _execute_agent_method(agent_key, method_name)
        results.append(result)
    return jsonify({"results": results, "total": len(results)})


@scheduler_bp.route("/api/scheduler/agent/<agent_key>")
def scheduler_agent_detail(agent_key):
    """Detailed status for a specific agent."""
    conn = _get_db()
    try:
        # Recent runs
        runs = []
        for row in conn.execute(
            "SELECT * FROM agent_runs WHERE agent = ? ORDER BY started_at DESC LIMIT 20",
            (agent_key,),
        ):
            runs.append({
                "method": row["method"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "status": row["status"],
                "result": row["result"][:200] if row["result"] else "",
                "error": row["error"][:200] if row["error"] else "",
            })

        # Schedules
        schedules = []
        for row in conn.execute(
            "SELECT * FROM agent_schedules WHERE agent = ?", (agent_key,),
        ):
            schedules.append({
                "method": row["method"],
                "interval_sec": row["interval_sec"],
                "description": row["description"],
                "last_run": row["last_run"],
                "next_run": row["next_run"],
                "enabled": bool(row["enabled"]),
            })

        # Check if agent can be loaded
        agent = _get_agent(agent_key)
        loadable = agent is not None

        return jsonify({
            "agent": agent_key,
            "loadable": loadable,
            "schedules": schedules,
            "recent_runs": runs,
        })
    finally:
        conn.close()


_init_db()
