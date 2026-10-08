"""Shared SQLite connection pool via SQLAlchemy.

Usage:
    from shared.db import get_sqlite_engine
    engine = get_sqlite_engine("my.db")
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
"""

from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool

_engines = {}


def get_sqlite_engine(db_path: str):
    """Get a SQLAlchemy engine for a SQLite database.

    Uses StaticPool (single-writer) with WAL mode enabled.
    The engine is cached per db_path.
    """
    if db_path not in _engines:
        engine = create_engine(
            f"sqlite:///{db_path}",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        _engines[db_path] = engine
    return _engines[db_path]
