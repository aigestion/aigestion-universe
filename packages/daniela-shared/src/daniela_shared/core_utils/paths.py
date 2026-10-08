"""Centralized repository paths for aig.

Single source of truth for repo root and standard directories.
All modules should import from here instead of computing paths manually.
"""

import os
from pathlib import Path


def _repo_root() -> Path:
    """Raiz real del repo.

    Este fichero se aplano de `core/` a la raiz (2026-09-29), asi que un
    `parents[N]` con indice fijo dejó de valer: `parents[1]` daba
    `files/home/apps`, FUERA del proyecto (mismo bug documentado en
    `health_checks._raiz_repo`). Buscar un marcador es inmune a la
    profundidad: funciona igual desde la raiz, desde `core/` o desde un
    contenedor sin `.git`.
    """
    aqui = Path(__file__).resolve()
    for cand in (aqui.parent, *aqui.parents):
        if (cand / ".git").exists() or (cand / "tests" / "conftest.py").exists():
            return cand
    return aqui.parent


REPO_ROOT = _repo_root()

# Standard directories
DATA_DIR = REPO_ROOT / "data"
STATIC_DIR = REPO_ROOT / "static"
CONFIG_DIR = REPO_ROOT / "config"
SCRIPTS_DIR = REPO_ROOT / "scripts"
TESTS_DIR = REPO_ROOT / "tests"
DOCS_DIR = REPO_ROOT / "docs"

# Domain-specific data directories
AGENTS_DATA_DIR = DATA_DIR / "agents"
CORE_DATA_DIR = DATA_DIR / "core"
MEMORY_DATA_DIR = DATA_DIR / "memory"
SIL_DATA_DIR = DATA_DIR / "sil"
INVOICE_DATA_DIR = DATA_DIR / "invoice"
DOCUMENTS_DATA_DIR = DATA_DIR / "documents"
RESEARCH_DATA_DIR = DATA_DIR / "research"

# Static subdirectories
BRAND_DIR = STATIC_DIR / "brand"
CAPTURES_DIR = STATIC_DIR / "captures"

# Config subdirectories
DOCKER_CONFIG_DIR = CONFIG_DIR / "docker"
NGINX_CONFIG_DIR = CONFIG_DIR / "nginx"
TERMUX_CONFIG_DIR = CONFIG_DIR / "termux"


def ensure_dirs() -> None:
    """Create all standard directories if they don't exist."""
    for d in [
        DATA_DIR, STATIC_DIR, CONFIG_DIR,
        AGENTS_DATA_DIR, CORE_DATA_DIR, MEMORY_DATA_DIR,
        SIL_DATA_DIR, INVOICE_DATA_DIR, DOCUMENTS_DATA_DIR,
        RESEARCH_DATA_DIR, BRAND_DIR, CAPTURES_DIR,
        DOCKER_CONFIG_DIR, NGINX_CONFIG_DIR, TERMUX_CONFIG_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


# Convenience: commonly used file paths
CALENDAR_FILE = DATA_DIR / "calendar_events.json"
BROKER_DB = CORE_DATA_DIR / "agent_messages.db"
LOG_DIR = CORE_DATA_DIR / "agent_activity"
MEMORY_RAG_DB = MEMORY_DATA_DIR / "memory_rag.db"
INVOICE_LEDGER = INVOICE_DATA_DIR / "ledger.jsonl"
SIL_STATE_FILE = SIL_DATA_DIR / "sil_state.json"
SIL_LESSONS_FILE = SIL_DATA_DIR / "knowledge_base.json"
SIL_TREND_FILE = SIL_DATA_DIR / "health_trend.json"
SIL_DISPATCH_LOG = SIL_DATA_DIR / "dispatch_log.json"


# ── Bases de datos "sueltas" ─────────────────────────────────────────────────
#
# POR QUE ESTE BLOQUE
# -------------------
# Estas bases se abrian con el NOMBRE RELATIVO ("aig_auth.db"), asi que
# SQLite creaba el fichero en el DIRECTORIO DE TRABAJO del proceso. Como casi
# todo se lanzaba desde la raiz del repo, aparecieron 8 `.db` SUELTOS EN LA RAIZ
# mientras la copia buena vivia en `data/`.
#
# Medido el 2026-09-21:
#
#     fichero                     raiz                 data/
#     memory_rag.db               16 KB,   0 filas     1,4 MB, 89 filas
#     scheduler_locks.db          12 KB,   0 filas     36 KB,  9 filas
#     daniela_multiuser.db        49 KB,  33 filas     49 KB, 53 filas
#     aig.db / auth / billing /
#     whitelabel / trigger         16-45 KB, 0 filas    identicos
#
# El caso mas caro es `memory_rag.db`: quien abria la de la raiz no veia NADA de
# la memoria, porque estaba vacia. Por eso estas constantes son ABSOLUTAS.
#
# Todas viven en `data/` (plano), que es donde ya estaba el dato bueno y donde
# las busca `daniela-os/shared/*` (`DATA_DIR/memory_rag.db`). Se pueden
# sobreescribir por entorno para despliegues con volumen propio.
DB_DIR = DATA_DIR


def _db(nombre: str, variable: str) -> Path:
    """Ruta ABSOLUTA de una base de datos, sobreescribible por variable de entorno.

    Nunca relativa: una ruta relativa se resuelve contra el cwd y acaba creando
    un fichero vacio en la raiz del repo (ver el bloque de arriba).
    """
    entorno = (os.getenv(variable) or "").strip()
    return Path(entorno).expanduser().resolve() if entorno else DB_DIR / nombre


DANIELA_DB = _db("daniela.db", "DANIELA_DB")
AUTH_DB = _db("auth.db", "DANIELA_AUTH_DB")
BILLING_DB = _db("billing.db", "DANIELA_BILLING_DB")
WHITELABEL_DB = _db("whitelabel.db", "DANIELA_WHITELABEL_DB")
DANIELA_MULTIUSER_DB = _db("daniela_multiuser.db", "DANIELA_MULTIUSER_DB")
SCHEDULER_LOCKS_DB = _db("scheduler_locks.db", "SCHEDULER_LOCKS_DB")
TRIGGER_WATCHES_DB = _db("trigger_watches.db", "TRIGGER_WATCHES_DB")

# OJO: apuntaba a `data/memory/memory_rag.db`, que NO existe. El fichero real (y
# el unico con datos) es `data/memory_rag.db`, que es el que usa daniela-os.
MEMORY_RAG_DB = _db("memory_rag.db", "MEMORY_RAG_DB")

# Bases de datos que deben existir como .db sueltos en `data/`. Lo usa el test
# de integridad para detectar si algun modulo vuelve a crearlas en la raiz.
BASES_CANONICAS = (
    DANIELA_DB,
    AUTH_DB,
    BILLING_DB,
    WHITELABEL_DB,
    DANIELA_MULTIUSER_DB,
    SCHEDULER_LOCKS_DB,
    TRIGGER_WATCHES_DB,
    MEMORY_RAG_DB,
)
