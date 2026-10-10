"""Daniela OS — Docker Marketplace API.

Permite a cada universe desplegar sus propios containers desde un catalogo
de imagenes pre-aprobadas. Incluye deploy, monitor, logs y gestion.
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent
_CATALOG_FILE = _REPO_ROOT / "marketplace_catalog.json"
_CONTAINERS_FILE = _REPO_ROOT / "data" / "docker" / "containers.json"
_LOGS_DIR = _REPO_ROOT / "data" / "docker" / "logs"

# ── Helpers ──────────────────────────────────────────────────────────────────

def _ensure_dirs():
    _CONTAINERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _load_catalog() -> dict[str, Any]:
    if _CATALOG_FILE.exists():
        return json.loads(_CATALOG_FILE.read_text(encoding="utf-8"))
    return {"catalog": [], "categories": []}


def _load_containers() -> dict[str, Any]:
    _ensure_dirs()
    if _CONTAINERS_FILE.exists():
        return json.loads(_CONTAINERS_FILE.read_text(encoding="utf-8"))
    return {"containers": {}}


def _save_containers(data: dict[str, Any]) -> None:
    _ensure_dirs()
    _CONTAINERS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _run_docker(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    """Ejecuta un comando docker con timeout."""
    cmd = ["docker"] + args
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="timeout")
    except FileNotFoundError:
        return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="docker not found")


def _get_container_stats(container_id: str) -> dict[str, Any]:
    """Obtiene stats en vivo de un container."""
    r = _run_docker(["stats", container_id, "--no-stream", "--format",
                      "{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}|{{.BlockIO}}"],
                     timeout=10)
    if r.returncode != 0 or not r.stdout.strip():
        return {"cpu": "?", "mem": "?", "net": "?", "block": "?"}
    parts = r.stdout.strip().split("|")
    return {
        "cpu": parts[0] if len(parts) > 0 else "?",
        "mem": parts[1] if len(parts) > 1 else "?",
        "net": parts[2] if len(parts) > 2 else "?",
        "block": parts[3] if len(parts) > 3 else "?",
    }


def _sync_docker_ps() -> dict[str, Any]:
    """Sincroniza el estado de containers desde docker ps."""
    store = _load_containers()
    r = _run_docker(["ps", "-a", "--format",
                      "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}|{{.CreatedAt}}"],
                     timeout=15)
    running_ids = set()
    if r.returncode == 0 and r.stdout.strip():
        for line in r.stdout.strip().split("\n"):
            parts = line.split("|")
            if len(parts) >= 5:
                cid, name, image, status, ports = parts[0], parts[1], parts[2], parts[3], parts[4]
                running_ids.add(cid)
                if name not in store["containers"]:
                    store["containers"][name] = {}
                store["containers"][name].update({
                    "container_id": cid,
                    "image": image,
                    "status": status,
                    "ports": ports,
                    "last_seen": datetime.now().isoformat(),
                })
    # Marcar containers que ya no existen
    for _name, info in list(store["containers"].items()):
        cid = info.get("container_id", "")
        if cid and cid not in running_ids:
            info["status"] = "removed"
            info["last_seen"] = datetime.now().isoformat()
    _save_containers(store)
    return store


# ── API Routes ───────────────────────────────────────────────────────────────

def register_docker_routes(app) -> None:
    """Registra todas las rutas del Docker Marketplace."""

    # ── Marketplace Catalog ──────────────────────────────────────────────

    @app.route("/api/docker/marketplace")
    def docker_marketplace_list():
        """Lista el catalogo de imagenes disponibles."""
        catalog = _load_catalog()
        return {"ok": True, "catalog": catalog["catalog"], "categories": catalog["categories"]}

    @app.route("/api/docker/marketplace/<app_id>")
    def docker_marketplace_detail(app_id: str):
        """Detalle de una imagen del marketplace."""
        catalog = _load_catalog()
        for item in catalog["catalog"]:
            if item["id"] == app_id:
                return {"ok": True, "app": item}
        return {"ok": False, "error": f"App '{app_id}' no encontrada"}, 404

    # ── Deploy ───────────────────────────────────────────────────────────

    @app.route("/api/docker/deploy", methods=["POST"])
    def docker_deploy():
        """Despliega un container desde el marketplace."""
        from flask import request
        data = request.get_json(silent=True) or {}
        app_id = data.get("app_id", "")
        universe = data.get("universe", "default")
        custom_name = data.get("name", "")
        env_vars = data.get("env", {})
        ports_override = data.get("ports", {})

        catalog = _load_catalog()
        image_info = None
        for item in catalog["catalog"]:
            if item["id"] == app_id:
                image_info = item
                break

        if not image_info:
            return {"ok": False, "error": f"App '{app_id}' no encontrada en el marketplace"}, 404

        container_name = custom_name or f"uni-{universe}-{app_id}"
        _ensure_dirs()

        # Verificar que no exista ya
        r = _run_docker(["inspect", container_name], timeout=10)
        if r.returncode == 0:
            return {"ok": False, "error": f"Container '{container_name}' ya existe"}, 409

        # Pull image
        _run_docker(["pull", image_info["image"]], timeout=120)

        # Construir comando docker run
        cmd = ["run", "-d", "--name", container_name, "--restart", "unless-stopped"]

        # Network
        cmd += ["--network", "aig-net"]

        # Memory limit
        if image_info.get("memory"):
            cmd += ["-m", image_info["memory"]]

        # CPU limit
        if image_info.get("cpu"):
            cmd += ["--cpus", image_info["cpu"]]

        # Port mapping
        base_port = image_info.get("port", 5000)
        host_port = ports_override.get("host", base_port)
        cmd += ["-p", f"{host_port}:{base_port}"]

        # Extra ports
        for ep in image_info.get("ports_extra", []):
            cmd += ["-p", f"{ep}:{ep}"]

        # Volumes
        for vol in image_info.get("volumes", []):
            if vol.startswith("/"):  # bind mount
                cmd += ["-v", f"{vol}"]
            else:  # named volume
                vol_name = f"uni-{universe}-{vol.split(':')[0]}"
                mount = vol.split(":")
                cmd += ["-v", f"{vol_name}:{mount[1] if len(mount) > 1 else vol}"]

        # Environment variables
        for k, v in image_info.get("env", {}).items():
            cmd += ["-e", f"{k}={v}"]
        for k, v in env_vars.items():
            cmd += ["-e", f"{k}={v}"]

        # Labels
        cmd += ["-l", f"universe={universe}", "-l", f"marketplace={app_id}",
                "-l", "managed-by=daniela-os"]

        # Custom command
        if image_info.get("command"):
            cmd += image_info["command"].split()

        cmd.append(image_info["image"])

        # Ejecutar
        r = _run_docker(cmd, timeout=120)
        if r.returncode != 0:
            return {"ok": False, "error": r.stderr or "docker run failed"}, 500

        container_id = r.stdout.strip()[:12]

        # Guardar en store
        store = _load_containers()
        store["containers"][container_name] = {
            "container_id": container_id,
            "image": image_info["image"],
            "app_id": app_id,
            "universe": universe,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "ports": f"{host_port}:{base_port}",
            "memory": image_info.get("memory", "?"),
            "cpu": image_info.get("cpu", "?"),
        }
        _save_containers(store)

        return {"ok": True, "container_id": container_id, "name": container_name,
                "port": host_port, "universe": universe}

    # ── Containers ───────────────────────────────────────────────────────

    @app.route("/api/docker/containers")
    def docker_containers_list():
        """Lista todos los containers gestionados."""
        store = _sync_docker_ps()
        # Filtrar solo los managed-by=daniela-os
        managed = {}
        for name, info in store.get("containers", {}).items():
            if info.get("universe") or info.get("marketplace"):
                managed[name] = info
        # Agregar stats para los que estan corriendo
        for _name, info in managed.items():
            cid = info.get("container_id", "")
            status = info.get("status", "")
            if cid and "Up" in status:
                info["stats"] = _get_container_stats(cid)
            else:
                info["stats"] = None
        return {"ok": True, "containers": managed, "total": len(managed)}

    @app.route("/api/docker/containers/<container_name>")
    def docker_container_detail(container_name: str):
        """Detalle de un container."""
        store = _sync_docker_ps()
        if container_name not in store.get("containers", {}):
            return {"ok": False, "error": "Container no encontrado"}, 404
        info = store["containers"][container_name]
        cid = info.get("container_id", "")
        if cid and "Up" in info.get("status", ""):
            info["stats"] = _get_container_stats(cid)
        return {"ok": True, "container": info}

    @app.route("/api/docker/containers/<container_name>/logs")
    def docker_container_logs(container_name: str):
        """Ultimas 100 lineas de logs de un container."""
        r = _run_docker(["logs", "--tail", "100", container_name], timeout=10)
        logs = r.stdout + r.stderr
        return {"ok": True, "logs": logs, "lines": len(logs.split("\n"))}

    @app.route("/api/docker/containers/<container_name>/stats")
    def docker_container_stats(container_name: str):
        """Stats en vivo de un container."""
        store = _load_containers()
        if container_name not in store.get("containers", {}):
            return {"ok": False, "error": "Container no encontrado"}, 404
        cid = store["containers"][container_name].get("container_id", "")
        if not cid:
            return {"ok": False, "error": "Container ID no disponible"}, 404
        stats = _get_container_stats(cid)
        return {"ok": True, "stats": stats}

    @app.route("/api/docker/containers/<container_name>/restart", methods=["POST"])
    def docker_container_restart(container_name: str):
        """Reinicia un container."""
        r = _run_docker(["restart", container_name], timeout=30)
        if r.returncode != 0:
            return {"ok": False, "error": r.stderr}, 500
        store = _sync_docker_ps()
        return {"ok": True, "status": store.get("containers", {}).get(container_name, {}).get("status")}

    @app.route("/api/docker/containers/<container_name>/stop", methods=["POST"])
    def docker_container_stop(container_name: str):
        """Detiene un container."""
        r = _run_docker(["stop", container_name], timeout=30)
        if r.returncode != 0:
            return {"ok": False, "error": r.stderr}, 500
        _sync_docker_ps()
        return {"ok": True, "status": "stopped"}

    @app.route("/api/docker/containers/<container_name>/start", methods=["POST"])
    def docker_container_start(container_name: str):
        """Inicia un container detenido."""
        r = _run_docker(["start", container_name], timeout=30)
        if r.returncode != 0:
            return {"ok": False, "error": r.stderr}, 500
        _sync_docker_ps()
        return {"ok": True, "status": "running"}

    @app.route("/api/docker/containers/<container_name>", methods=["DELETE"])
    def docker_container_remove(container_name: str):
        """Detiene y elimina un container."""
        _run_docker(["stop", container_name], timeout=15)
        r = _run_docker(["rm", container_name], timeout=15)
        if r.returncode != 0:
            return {"ok": False, "error": r.stderr}, 500
        store = _load_containers()
        store["containers"].pop(container_name, None)
        _save_containers(store)
        return {"ok": True}

    # ── Universes ────────────────────────────────────────────────────────

    @app.route("/api/docker/universes")
    def docker_universes_list():
        """Lista todos los universes con sus containers."""
        store = _sync_docker_ps()
        universes: dict[str, list] = {}
        for name, info in store.get("containers", {}).items():
            uni = info.get("universe", "default")
            if uni not in universes:
                universes[uni] = []
            universes[uni].append({"name": name, **info})
        return {"ok": True, "universes": universes, "total": len(universes)}

    @app.route("/api/docker/universes/<universe>/install", methods=["POST"])
    def docker_universe_install(universe: str):
        """Instala una app del marketplace en un universe."""
        from flask import request
        data = request.get_json(silent=True) or {}
        data["universe"] = universe
        # Reusar la ruta de deploy
        with request.application_context():
            # Simular deploy
            app_id = data.get("app_id", "")
            catalog = _load_catalog()
            for item in catalog["catalog"]:
                if item["id"] == app_id:
                    data.setdefault("name", f"uni-{universe}-{app_id}")
                    break

        # Deploy directo
        from flask import request as req
        req._cached_json = (data, data)
        return docker_deploy()

    # ── Docker System ────────────────────────────────────────────────────

    @app.route("/api/docker/system")
    def docker_system_info():
        """Info del sistema Docker."""
        r = _run_docker(["info", "--format",
                          "{{.ServerVersion}}|{{.Containers}}|{{.ContainersRunning}}|{{.MemTotal}}"],
                         timeout=10)
        info = {"version": "?", "containers_total": 0, "containers_running": 0, "memory": "?"}
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().split("|")
            if len(parts) >= 4:
                info = {
                    "version": parts[0],
                    "containers_total": int(parts[1]) if parts[1].isdigit() else 0,
                    "containers_running": int(parts[2]) if parts[2].isdigit() else 0,
                    "memory": parts[3],
                }

        # Images list
        r2 = _run_docker(["images", "--format", "{{.Repository}}:{{.Tag}}|{{.Size}}"], timeout=10)
        images = []
        if r2.returncode == 0 and r2.stdout.strip():
            for line in r2.stdout.strip().split("\n"):
                parts = line.split("|")
                if len(parts) >= 2:
                    images.append({"image": parts[0], "size": parts[1]})

        return {"ok": True, "system": info, "images": images}

    @app.route("/api/docker/images/pull", methods=["POST"])
    def docker_image_pull():
        """Pull de una imagen Docker."""
        from flask import request
        data = request.get_json(silent=True) or {}
        image = data.get("image", "")
        if not image:
            return {"ok": False, "error": "image requerida"}, 400
        r = _run_docker(["pull", image], timeout=300)
        if r.returncode != 0:
            return {"ok": False, "error": r.stderr}, 500
        return {"ok": True, "output": r.stdout}

    print("[Docker Marketplace] Routes registered: /api/docker/*")
