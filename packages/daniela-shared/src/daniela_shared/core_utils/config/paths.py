"""Canonical repository and SQLite data paths."""

from __future__ import annotations

import os
from pathlib import Path


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in (current.parent, *current.parents):
        if (candidate / ".git").exists() or (candidate / "tests" / "conftest.py").exists():
            return candidate
    return current.parents[2]


REPO_ROOT = _repo_root()
DATA_DIR = REPO_ROOT / "data"
DB_DIR = DATA_DIR


def _db(filename: str, env_var: str) -> Path:
    value = (os.getenv(env_var) or "").strip()
    return Path(value).expanduser().resolve() if value else DB_DIR / filename


DANIELA_DB = _db("daniela.db", "DANIELA_DB")
AUTH_DB = _db("auth.db", "DANIELA_AUTH_DB")
BILLING_DB = _db("billing.db", "DANIELA_BILLING_DB")
WHITELABEL_DB = _db("whitelabel.db", "DANIELA_WHITELABEL_DB")
DANIELA_MULTIUSER_DB = _db("daniela_multiuser.db", "DANIELA_MULTIUSER_DB")
SCHEDULER_LOCKS_DB = _db("scheduler_locks.db", "SCHEDULER_LOCKS_DB")
TRIGGER_WATCHES_DB = _db("trigger_watches.db", "TRIGGER_WATCHES_DB")
MEMORY_RAG_DB = _db("memory_rag.db", "MEMORY_RAG_DB")

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

__all__ = [
    "DANIELA_DB",
    "AUTH_DB",
    "BASES_CANONICAS",
    "BILLING_DB",
    "DATA_DIR",
    "DANIELA_MULTIUSER_DB",
    "DB_DIR",
    "MEMORY_RAG_DB",
    "REPO_ROOT",
    "SCHEDULER_LOCKS_DB",
    "TRIGGER_WATCHES_DB",
    "WHITELABEL_DB",
]
