"""Daniela OS — Universe Deploy Manager.

Cada universe puede desplegar sus propios containers Docker con aislamiento
por nombre de red, volumes y labels.
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent
_UNIVERSES_FILE = _REPO_ROOT / "data" / "docker" / "universes.json"
_NETWORK = "aig-net"


def _ensure_dirs():
    _UNIVERSES_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_universes() -> dict[str, Any]:
    _ensure_dirs()
    if _UNIVERSES_FILE.exists():
        return json.loads(_UNIVERSES_FILE.read_text(encoding="utf-8"))
    return {"universes": {}}


def _save_universes(data: dict[str, Any]) -> None:
    _ensure_dirs()
    _UNIVERSES_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _run(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    cmd = ["docker"] + args
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="timeout")
    except FileNotFoundError:
        return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="docker not found")


# ── Universe CRUD ────────────────────────────────────────────────────────────

def create_universe(slug: str, name: str, description: str = "",
                    admin_email: str = "") -> dict[str, Any]:
    """Crea un universe con su propio namespace de containers."""
    store = _load_universes()
    if slug in store["universes"]:
        return {"ok": False, "error": f"Universe '{slug}' ya existe"}

    # Crear red dedicada si no existe
    _run(["network", "create", f"uni-{slug}-net"], timeout=15)

    # Crear directorio de datos
    uni_dir = _REPO_ROOT / "data" / "universes" / slug
    uni_dir.mkdir(parents=True, exist_ok=True)
    (uni_dir / "containers").mkdir(exist_ok=True)
    (uni_dir / "data").mkdir(exist_ok=True)

    universe = {
        "slug": slug,
        "name": name,
        "description": description,
        "admin_email": admin_email,
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "containers": {},
        "network": f"uni-{slug}-net",
        "data_dir": str(uni_dir),
    }
    store["universes"][slug] = universe
    _save_universes(store)
    return {"ok": True, "universe": universe}


def list_universes() -> dict[str, Any]:
    """Lista todos los universes."""
    store = _load_universes()
    # Sincronizar estado de containers
    for _slug, uni in store["universes"].items():
        for _cname, cinfo in uni.get("containers", {}).items():
            cid = cinfo.get("container_id", "")
            if cid:
                r = _run(["inspect", "--format", "{{.State.Status}}", cid], timeout=10)
                if r.returncode == 0:
                    cinfo["status"] = r.stdout.strip()
                else:
                    cinfo["status"] = "removed"
    _save_universes(store)
    return {"ok": True, "universes": store["universes"], "total": len(store["universes"])}


def get_universe(slug: str) -> dict[str, Any] | None:
    """Obtiene un universe por slug."""
    store = _load_universes()
    return store["universes"].get(slug)


def delete_universe(slug: str) -> dict[str, Any]:
    """Elimina un universe y todos sus containers."""
    store = _load_universes()
    if slug not in store["universes"]:
        return {"ok": False, "error": f"Universe '{slug}' no encontrado"}

    uni = store["universes"][slug]

    # Parar y eliminar todos los containers del universe
    for cname in list(uni.get("containers", {}).keys()):
        _run(["stop", cname], timeout=15)
        _run(["rm", cname], timeout=15)

    # Eliminar red dedicada
    _run(["network", "rm", f"uni-{slug}-net"], timeout=15)

    store["universes"].pop(slug)
    _save_universes(store)
    return {"ok": True}


def deploy_in_universe(slug: str, app_id: str, image: str, port: int,
                       memory: str = "256m", cpu: str = "0.25",
                       env: dict | None = None) -> dict[str, Any]:
    """Despliega un container dentro de un universe."""
    store = _load_universes()
    if slug not in store["universes"]:
        return {"ok": False, "error": f"Universe '{slug}' no encontrado"}

    uni = store["universes"][slug]
    container_name = f"uni-{slug}-{app_id}"

    # Verificar que no exista
    r = _run(["inspect", container_name], timeout=10)
    if r.returncode == 0:
        return {"ok": False, "error": f"Container '{container_name}' ya existe"}

    # Pull
    _run(["pull", image], timeout=120)

    # Run
    cmd = ["run", "-d", "--name", container_name, "--restart", "unless-stopped"]
    cmd += ["--network", uni["network"]]
    cmd += ["-m", memory, "--cpus", cpu]
    cmd += ["-p", f"{port}:{port}"]
    cmd += ["-l", f"universe={slug}", "-l", f"marketplace={app_id}",
            "-l", "managed-by=daniela-os"]

    if env:
        for k, v in env.items():
            cmd += ["-e", f"{k}={v}"]

    # Volume del universe
    data_dir = uni.get("data_dir", "")
    if data_dir:
        cmd += ["-v", f"{data_dir}/data:/app/data"]

    cmd.append(image)

    r = _run(cmd, timeout=120)
    if r.returncode != 0:
        return {"ok": False, "error": r.stderr or "docker run failed"}, 500

    container_id = r.stdout.strip()[:12]
    uni["containers"][container_name] = {
        "container_id": container_id,
        "app_id": app_id,
        "image": image,
        "port": port,
        "status": "running",
        "created_at": datetime.now().isoformat(),
    }
    _save_universes(store)
    return {"ok": True, "container_id": container_id, "name": container_name}


def register_universe_routes(app) -> None:
    """Registra rutas de gestion de universes."""

    @app.route("/api/universes", methods=["GET"])
    def api_universes_list():
        return list_universes()

    @app.route("/api/universes", methods=["POST"])
    def api_universes_create():
        from flask import request
        data = request.get_json(silent=True) or {}
        slug = data.get("slug", "")
        if not slug:
            return {"ok": False, "error": "slug requerido"}, 400
        return create_universe(
            slug=slug,
            name=data.get("name", slug),
            description=data.get("description", ""),
            admin_email=data.get("admin_email", ""),
        )

    @app.route("/api/universes/<slug>")
    def api_universes_detail(slug: str):
        uni = get_universe(slug)
        if not uni:
            return {"ok": False, "error": "Universe no encontrado"}, 404
        return {"ok": True, "universe": uni}

    @app.route("/api/universes/<slug>", methods=["DELETE"])
    def api_universes_delete(slug: str):
        return delete_universe(slug)

    @app.route("/api/universes/<slug>/deploy", methods=["POST"])
    def api_universes_deploy(slug: str):
        from flask import request
        data = request.get_json(silent=True) or {}
        return deploy_in_universe(
            slug=slug,
            app_id=data.get("app_id", ""),
            image=data.get("image", ""),
            port=data.get("port", 5000),
            memory=data.get("memory", "256m"),
            cpu=data.get("cpu", "0.25"),
            env=data.get("env"),
        )

    print("[Universe Deploy] Routes registered: /api/universes/*")
