"""state.db - base RAG operativa de Daniela OS (SQLite + WAL).

Cumple indicaciones.txt §2: sincronizar cada cambio o log importante en la
base de datos `C:\\Users\\Alejandro\\aig\\state.db`.

- Tabla `events`: log de cambios (kind, source, payload JSON).
- Tabla `kv`: estado corto (modelo :free activo, versiones, flags).

Alimenta el dashboard `web/` via `scripts/serve_control.py` (GET /api/status)
y el HUD de escritorio (YASB/Rainmeter).

CLI:
    python scripts/state_db.py status
    python scripts/state_db.py log <kind> <source> [--payload JSON]
    python scripts/state_db.py kv <key> [value]
    python scripts/state_db.py recent [limit]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[1] / "state.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    source TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS kv (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated TEXT NOT NULL
);
"""


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Abre (crea si no existe) el estado en modo WAL con el schema listo."""
    path = Path(db_path) if db_path is not None else Path(DEFAULT_DB)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def log_event(
    conn: sqlite3.Connection,
    kind: str,
    source: str,
    payload: dict | str | None = None,
) -> int:
    """Registra un evento y devuelve su id."""
    if payload is None:
        stored = "{}"
    elif isinstance(payload, str):
        stored = json.dumps({"text": payload}, ensure_ascii=False)
    else:
        stored = json.dumps(payload, ensure_ascii=False)
    ts = datetime.now(UTC).isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO events (ts, kind, source, payload) VALUES (?, ?, ?, ?)",
        (ts, kind, source, stored),
    )
    conn.commit()
    return int(cur.lastrowid)


def set_kv(conn: sqlite3.Connection, key: str, value: str) -> None:
    """Escribe/actualiza una entrada clave-valor con timestamp."""
    ts = datetime.now(UTC).isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO kv (key, value, updated) VALUES (?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
        "updated = excluded.updated",
        (key, value, ts),
    )
    conn.commit()


def get_kv(conn: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    """Lee una entrada clave-valor (o `default` si no existe)."""
    row = conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def recent_events(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    """Ultimos eventos, mas recientes primero."""
    rows = conn.execute(
        "SELECT id, ts, kind, source, payload FROM events "
        "ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        try:
            item["payload"] = json.loads(item["payload"])
        except json.JSONDecodeError:  # pragma: no cover - payload corrupto
            pass
        out.append(item)
    return out


def status(db_path: Path | str | None = None) -> dict:
    """Estado para el dashboard/HUD: modo WAL, contadores y tamano."""
    path = Path(db_path) if db_path is not None else Path(DEFAULT_DB)
    conn = connect(path)
    try:
        journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
        events = conn.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"]
        kv = conn.execute("SELECT COUNT(*) AS n FROM kv").fetchone()["n"]
    finally:
        conn.close()
    size = path.stat().st_size if path.exists() else 0
    return {
        "path": str(path),
        "journal_mode": str(journal).lower(),
        "wal": str(journal).lower() == "wal",
        "events": int(events),
        "kv": int(kv),
        "size_bytes": size,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI minima para scripts y el HUD."""
    parser = argparse.ArgumentParser(description="state.db de Daniela OS")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="modo WAL, contadores y tamano")

    p_log = sub.add_parser("log", help="registra un evento")
    p_log.add_argument("kind")
    p_log.add_argument("source")
    p_log.add_argument("--payload", help="JSON o texto plano")

    p_kv = sub.add_parser("kv", help="lee o escribe clave-valor")
    p_kv.add_argument("key")
    p_kv.add_argument("value", nargs="?")

    p_recent = sub.add_parser("recent", help="ultimos eventos")
    p_recent.add_argument("limit", nargs="?", type=int, default=20)

    args = parser.parse_args(argv)
    conn = connect()
    try:
        if args.cmd == "status":
            print(json.dumps(status(), ensure_ascii=False, indent=2))
        elif args.cmd == "log":
            payload = args.payload
            if payload and payload.lstrip().startswith(("{", "[")):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    # PowerShell puede llegar a manipular las comillas al
                    # pasar argumentos: el texto se guarda tal cual.
                    pass
            event_id = log_event(conn, args.kind, args.source, payload)
            print(f"event_id={event_id}")
        elif args.cmd == "kv":
            if args.value is None:
                print(get_kv(conn, args.key) or "")
            else:
                set_kv(conn, args.key, args.value)
                print(f"{args.key}={args.value}")
        elif args.cmd == "recent":
            print(json.dumps(recent_events(conn, args.limit), ensure_ascii=False, indent=2))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
