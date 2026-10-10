#!/usr/bin/env python3
"""
Git Brain Sync — Cerebro versionado PC <-> Pixel (E-03 / Fase 5)
=================================================================
La memoria de Daniela (episodios, aprendizajes SIL, preferencias) vive en un
solo sitio. Si cambias de dispositivo, Daniela "olvida".

Solucion: git funciona en Termux. Este modulo mantiene data/brain/ como un
repo git propio que se sincroniza entre el PC y el Pixel:

  - Commits automaticos del estado cuando cambia algo
  - Pull --rebase + push cuando hay red
  - Resolucion de conflictos por timestamp + device-id (el mas reciente gana)
  - Rollback de la personalidad a cualquier punto del historial
  - Daniela tiene "git log" de sus propios recuerdos

Seguridad: comandos git con lista de argumentos via safe_exec. Nunca shell.

Rutas:
  GET  /api/brain/status          — estado del cerebro y del repo
  POST /api/brain/commit          — commitea el estado actual
  POST /api/brain/sync            — pull + push (si hay remoto)
  GET  /api/brain/history         — historial de versiones
  POST /api/brain/rollback        — vuelve a una version anterior
  POST /api/brain/write           — escribe un recuerdo/episodio
  GET  /api/brain/read            — lee el estado actual
  POST /api/brain/autosync        — activa/desactiva el autosync

Coste: $0/mes — git + repo privado (free)
"""

from __future__ import annotations

import json
import socket
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from safe_exec import run_cmd, run_out

PROJECT_ROOT = Path(__file__).resolve().parent
BRAIN_DIR = PROJECT_ROOT / "data" / "brain"
STATE_FILE = BRAIN_DIR / "brain_state.json"
EPISODES_DIR = BRAIN_DIR / "episodes"
CONFLICTS_FILE = BRAIN_DIR / "conflicts.json"

AUTOSYNC_INTERVAL = 120  # segundos entre intentos de sincronizacion
MAX_HISTORY = 100

_instance: BrainSync | None = None
_instance_lock = threading.Lock()


def _device_id() -> str:
    """Identificador estable del dispositivo (PC o Pixel)."""
    host = socket.gethostname().replace(" ", "_")[:24]
    try:
        import platform as _p

        tag = _p.system().lower()[:3]
    except Exception:
        tag = "unk"
    return f"{host}-{tag}"


class BrainSync:
    """Sincronizador git del cerebro de Daniela."""

    def __init__(self) -> None:
        self.device_id = _device_id()
        self.autosync = False
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.last_sync: str | None = None
        self.last_commit: str | None = None
        self.sync_count = 0
        self.conflicts: list[dict[str, Any]] = []

        BRAIN_DIR.mkdir(parents=True, exist_ok=True)
        EPISODES_DIR.mkdir(parents=True, exist_ok=True)
        if not STATE_FILE.exists():
            self._write_state(
                {
                    "created": datetime.now().isoformat(),
                    "device": self.device_id,
                    "episodes": 0,
                    "preferences": {},
                    "learnings": [],
                }
            )
        self._load_conflicts()

    # ── Estado del cerebro ───────────────────────────────────────────────────
    def _write_state(self, data: dict[str, Any]) -> None:
        data["_updated"] = datetime.now().isoformat(timespec="seconds")
        data["_device"] = self.device_id
        STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def read_state(self) -> dict[str, Any]:
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def write_episode(self, title: str, content: str, kind: str = "episodio") -> dict[str, Any]:
        """Escribe un recuerdo episodico. Se versiona automaticamente."""
        ts = datetime.now()
        fname = f"{ts.strftime('%Y%m%d_%H%M%S')}_{self.device_id}.json"
        path = EPISODES_DIR / fname
        path.write_text(
            json.dumps(
                {
                    "title": title,
                    "content": content,
                    "kind": kind,
                    "device": self.device_id,
                    "ts": ts.isoformat(timespec="seconds"),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        st = self.read_state()
        st["episodes"] = st.get("episodes", 0) + 1
        self._write_state(st)
        return {"ok": True, "file": str(path.relative_to(PROJECT_ROOT))}

    def write_learning(self, learning: str) -> dict[str, Any]:
        """Registra un aprendizaje del SIL."""
        st = self.read_state()
        learnings = st.get("learnings", [])
        learnings.append(
            {
                "text": learning,
                "device": self.device_id,
                "ts": datetime.now().isoformat(timespec="seconds"),
            }
        )
        st["learnings"] = learnings[-500:]
        self._write_state(st)
        return {"ok": True, "total": len(st["learnings"])}

    # ── Repo git ─────────────────────────────────────────────────────────────
    def _git(self, *args: str, timeout: int = 30):
        """Ejecuta git dentro del directorio del cerebro (lista de args)."""
        return run_cmd(["git", "-C", str(BRAIN_DIR)] + list(args), timeout=timeout)

    def init_repo(self) -> dict[str, Any]:
        """Crea el repo git del cerebro si no existe."""
        if (BRAIN_DIR / ".git").exists():
            return {"ok": True, "msg": "repo ya existe"}
        r = self._git("init")
        if r.returncode != 0:
            return {"ok": False, "msg": r.stderr.strip()[:100]}
        self._git("config", "user.name", "DanielaOS")
        self._git("config", "user.email", "daniela@aigestion.net")
        # El cerebro nunca debe llevar secretos
        (BRAIN_DIR / ".gitignore").write_text("*.key\n*.token\nsecrets/\n", encoding="utf-8")
        return {"ok": True, "msg": "repo creado en data/brain"}

    def has_remote(self) -> bool:
        return bool(run_out(["git", "-C", str(BRAIN_DIR), "remote", "get-url", "origin"]).strip())

    def commit(self, msg: str | None = None) -> dict[str, Any]:
        """Commitea el estado actual si hay cambios."""
        self.init_repo()
        self._git("add", "-A")
        status = run_out(["git", "-C", str(BRAIN_DIR), "status", "--porcelain"]).strip()
        if not status:
            return {"ok": True, "msg": "sin cambios", "committed": False}
        msg = msg or f"brain: {self.device_id} {datetime.now().isoformat(timespec='seconds')}"
        r = self._git("commit", "-m", msg)
        if r.returncode == 0:
            self.last_commit = datetime.now().isoformat(timespec="seconds")
            return {"ok": True, "msg": "commit creado", "committed": True, "message": msg}
        return {"ok": False, "msg": r.stderr.strip()[:100]}

    def sync(self) -> dict[str, Any]:
        """Pull --rebase + push. Resuelve conflictos por timestamp."""
        self.init_repo()
        result: dict[str, Any] = {"committed": False, "pulled": False, "pushed": False}

        c = self.commit()
        result["committed"] = c.get("committed", False)

        if not self.has_remote():
            result["msg"] = (
                "sin remoto configurado — anade uno con: git -C data/brain remote add origin <url>"
            )
            return result

        # Traer cambios del otro dispositivo
        p = self._git("pull", "--rebase", "--no-edit", timeout=60)
        if p.returncode == 0:
            result["pulled"] = True
        else:
            result["pull_error"] = p.stderr.strip()[:120]
            # Conflicto: el mas reciente gana
            conflict_files = [
                ln[3:].strip()
                for ln in run_out(
                    ["git", "-C", str(BRAIN_DIR), "diff", "--name-only", "--diff-filter=U"]
                ).splitlines()
                if ln.strip()
            ]
            for cf in conflict_files:
                self._resolve_conflict(cf)
            if conflict_files:
                self._git("add", "-A")
                self._git("rebase", "--continue")

        # Enviar nuestros cambios
        u = self._git("push", timeout=60)
        result["pushed"] = u.returncode == 0
        if not result["pushed"]:
            result["push_error"] = u.stderr.strip()[:120]

        self.last_sync = datetime.now().isoformat(timespec="seconds")
        self.sync_count += 1
        result["last_sync"] = self.last_sync
        return result

    def _resolve_conflict(self, rel_path: str) -> None:
        """Resuelve quedandose con la version mas reciente (por _updated)."""
        try:
            ours = run_out(["git", "-C", str(BRAIN_DIR), "show", f":2:{rel_path}"])
            theirs = run_out(["git", "-C", str(BRAIN_DIR), "show", f":3:{rel_path}"])
        except Exception:
            return

        def _ts(txt: str) -> float:
            try:
                d = json.loads(txt)
                return datetime.fromisoformat(d.get("_updated", "1970-01-01")).timestamp()
            except Exception:
                return 0.0

        winner = ours if _ts(ours) >= _ts(theirs) else theirs
        target = BRAIN_DIR / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(winner, encoding="utf-8")
        self.conflicts.append(
            {
                "file": rel_path,
                "resolved_at": datetime.now().isoformat(timespec="seconds"),
                "winner": "local" if _ts(ours) >= _ts(theirs) else "remoto",
            }
        )
        self._save_conflicts()

    def _load_conflicts(self) -> None:
        if CONFLICTS_FILE.exists():
            try:
                self.conflicts = json.loads(CONFLICTS_FILE.read_text(encoding="utf-8"))
            except Exception:
                self.conflicts = []

    def _save_conflicts(self) -> None:
        try:
            CONFLICTS_FILE.write_text(
                json.dumps(self.conflicts[-100:], indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass

    def history(self, limit: int = 20) -> list[dict[str, str]]:
        """Historial de versiones del cerebro."""
        if not (BRAIN_DIR / ".git").exists():
            return []
        out = run_out(
            [
                "git",
                "-C",
                str(BRAIN_DIR),
                "log",
                f"--max-count={limit}",
                "--pretty=format:%h|%ad|%s",
                "--date=iso",
            ]
        )
        rows = []
        for ln in out.splitlines():
            parts = ln.split("|", 2)
            if len(parts) == 3:
                rows.append({"sha": parts[0], "date": parts[1], "message": parts[2]})
        return rows

    def rollback(self, sha: str) -> dict[str, Any]:
        """Vuelve el cerebro a una version anterior."""
        if not (BRAIN_DIR / ".git").exists():
            return {"ok": False, "msg": "no hay repo"}
        r = self._git("checkout", sha, "--", ".")
        if r.returncode != 0:
            return {"ok": False, "msg": r.stderr.strip()[:100]}
        self.commit(f"rollback a {sha}")
        return {"ok": True, "msg": f"cerebro restaurado a {sha}"}

    # ── Autosync ─────────────────────────────────────────────────────────────
    def _autosync_loop(self) -> None:
        while not self._stop.wait(AUTOSYNC_INTERVAL):
            try:
                self.sync()
            except Exception:
                pass

    def set_autosync(self, enabled: bool) -> dict[str, Any]:
        self.autosync = enabled
        if enabled and not (self._thread and self._thread.is_alive()):
            self._stop.clear()
            self._thread = threading.Thread(target=self._autosync_loop, daemon=True)
            self._thread.start()
            return {"ok": True, "msg": "autosync activado"}
        if not enabled:
            self._stop.set()
            return {"ok": True, "msg": "autosync desactivado"}
        return {"ok": True, "msg": "autosync ya activo"}

    # ── Estado ───────────────────────────────────────────────────────────────
    def status(self) -> dict[str, Any]:
        st = self.read_state()
        pending = ""
        if (BRAIN_DIR / ".git").exists():
            pending = run_out(["git", "-C", str(BRAIN_DIR), "status", "--porcelain"]).strip()
        return {
            "device_id": self.device_id,
            "brain_dir": str(BRAIN_DIR.relative_to(PROJECT_ROOT)),
            "has_repo": (BRAIN_DIR / ".git").exists(),
            "has_remote": self.has_remote() if (BRAIN_DIR / ".git").exists() else False,
            "autosync": self.autosync,
            "pending_changes": len([row for row in pending.splitlines() if row.strip()]),
            "episodes": st.get("episodes", 0),
            "learnings": len(st.get("learnings", [])),
            "last_sync": self.last_sync,
            "last_commit": self.last_commit,
            "sync_count": self.sync_count,
            "conflicts": self.conflicts[-5:],
        }


def get_instance() -> BrainSync:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = BrainSync()
        return _instance


# =============================================================================
# RUTAS FLASK
# =============================================================================


def register_brain_routes(app) -> None:
    from flask import jsonify, request

    @app.route("/api/brain/status", methods=["GET"])
    def brain_status():
        return jsonify(get_instance().status())

    @app.route("/api/brain/commit", methods=["POST"])
    def brain_commit():
        msg = (request.get_json(silent=True) or {}).get("message")
        return jsonify(get_instance().commit(msg))

    @app.route("/api/brain/sync", methods=["POST"])
    def brain_sync():
        return jsonify(get_instance().sync())

    @app.route("/api/brain/history", methods=["GET"])
    def brain_history():
        limit = request.args.get("limit", 20, type=int)
        return jsonify({"history": get_instance().history(limit)})

    @app.route("/api/brain/rollback", methods=["POST"])
    def brain_rollback():
        sha = (request.get_json(silent=True) or {}).get("sha", "")
        if not sha:
            return jsonify({"ok": False, "msg": "falta 'sha'"}), 400
        return jsonify(get_instance().rollback(sha))

    @app.route("/api/brain/write", methods=["POST"])
    def brain_write():
        d = request.get_json(silent=True) or {}
        if d.get("kind") == "learning":
            return jsonify(get_instance().write_learning(d.get("text", "")))
        return jsonify(
            get_instance().write_episode(
                d.get("title", "sin titulo"), d.get("content", ""), d.get("kind", "episodio")
            )
        )

    @app.route("/api/brain/read", methods=["GET"])
    def brain_read():
        return jsonify(get_instance().read_state())

    @app.route("/api/brain/autosync", methods=["POST"])
    def brain_autosync():
        d = request.get_json(silent=True) or {}
        return jsonify(get_instance().set_autosync(bool(d.get("enabled", True))))

    print(
        "[Brain Sync] Routes registered: /api/brain/* "
        "(status, commit, sync, history, rollback, write, read, autosync)"
    )


def main() -> None:
    import sys

    b = get_instance()
    if "--status" in sys.argv:
        print(json.dumps(b.status(), indent=2))
    elif "--sync" in sys.argv:
        print(json.dumps(b.sync(), indent=2))
    elif "--history" in sys.argv:
        for h in b.history():
            print(f"  {h['sha']}  {h['date'][:19]}  {h['message']}")
    else:
        print("Git Brain Sync — Cerebro versionado de Daniela")
        print(f"  dispositivo : {b.device_id}")
        print(f"  directorio  : {b.brain_dir if hasattr(b, 'brain_dir') else BRAIN_DIR}")
        print("\nComandos: --status | --sync | --history")


if __name__ == "__main__":
    main()
