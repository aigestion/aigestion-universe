"""Database optimization utilities for Daniela OS.

The project has multiple SQLite files and a recurring issue: many modules open
relative database paths from the current working directory. This utility keeps a
canonical optimization pass under the repo data directory and makes it easy to
repair/optimize every SQLite database in one place.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from core.config.paths import BASES_CANONICAS, DATA_DIR


class DatabaseManager:
    """Central manager for the SQLite data layer in Daniela OS."""

    def __init__(self, base_dir: Path | str | None = None):
        self.base_dir = Path(base_dir) if base_dir is not None else DATA_DIR

    def list_database_files(self) -> list[Path]:
        """Return the canonical database files under the repo data tree."""
        directory = self.base_dir
        if not directory.exists():
            return []

        db_files = sorted({p for p in directory.rglob("*.db") if p.is_file()})
        if directory.resolve() == DATA_DIR.resolve():
            for canonical in BASES_CANONICAS:
                if canonical.exists() and canonical not in db_files:
                    db_files.append(canonical)
        return db_files

    def optimize_database(self, path: str | Path, *, vacuum: bool = True) -> dict[str, Any]:
        """Apply a safe SQLite optimization pass to a single database file."""
        db_path = Path(path).expanduser()
        if not db_path.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
            sqlite3.connect(str(db_path)).close()

        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA cache_size=-20000")
            conn.execute("PRAGMA wal_autocheckpoint=1000")
            conn.execute("PRAGMA optimize")
            if vacuum and db_path.stat().st_size > 1024 * 1024:
                conn.execute("VACUUM")
            conn.commit()
            journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            return {"ok": True, "path": str(db_path), "journal_mode": str(journal_mode)}
        finally:
            conn.close()

    def run_maintenance(self, *, vacuum: bool = True) -> dict[str, Any]:
        """Optimize every SQLite database in the canonical data tree."""
        results: list[dict[str, Any]] = []
        for db_path in self.list_database_files():
            try:
                results.append(self.optimize_database(db_path, vacuum=vacuum))
            except Exception as exc:  # pragma: no cover - defensive logging
                results.append({"ok": False, "path": str(db_path), "error": str(exc)})
        return {
            "ok": all(result["ok"] for result in results),
            "count": len(results),
            "databases": results,
        }


def _iter_database_files(base_dir: Path | None = None) -> list[Path]:
    """Backward-compatible helper for callers that still use the old function."""
    return DatabaseManager(base_dir).list_database_files()


def optimize_sqlite_database(path: str | Path, *, vacuum: bool = True) -> dict[str, Any]:
    """Compatibility wrapper for the old helper API."""
    return DatabaseManager().optimize_database(path, vacuum=vacuum)


def optimize_all_databases(base_dir: Path | None = None, *, vacuum: bool = True) -> dict[str, Any]:
    """Optimize all SQLite files in the canonical data tree."""
    return DatabaseManager(base_dir).run_maintenance(vacuum=vacuum)


if __name__ == "__main__":
    print(optimize_all_databases())
