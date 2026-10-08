#!/usr/bin/env python3
"""
DANIELA UNIFIED — Entry point único para Daniela OS
====================================================
Une todo en un solo proceso orquestado:
- Backend Flask (God's Eye + API aig)  : puerto 8082
- God's Eye 3D Visor                        : puerto 8090 (mismo proceso, blueprint)
- Web UI Three.js + Gemini                  : puerto 5050 (blueprint)
- HUD Desktop PyQt6 (voice always-on)       : proceso hijo
- Control REAL Windows (PowerShell, COM, pywinauto, psutil)
- Memoria persistente (ChromaDB + SQLite)
- LLM Local fallback (Ollama) + Gemini API
- Proactive loop (recordatorios, watchers, sugerencias)

Uso:
    python daniela_unified.py           # todo junto
    python daniela_unified.py --no-hud  # sin HUD desktop
    python daniela_unified.py --only-hud # solo HUD (para debug)
"""

from __future__ import annotations

import argparse
import atexit
import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

from flask import Flask

# ─── Paths & Env ──────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
CORE = ROOT / "core"
GODS_EYE = ROOT / "gev"
SYSTEM_DIR = Path.home() / ".daniela_system"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

for p in (ROOT, CORE, GODS_EYE, SYSTEM_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# ─── Imports core aig ───────────────────────────────────
try:
    from gev.gev_server import register_gev_routes
    CORE_OK = True
except Exception as e:
    print(f"[WARN] Core aig no disponible: {e}")
    CORE_OK = False

# ─── Flask App Factory ────────────────────────────────────────
def create_app() -> Flask:
    from flask import jsonify, request, send_from_directory
    from flask_cors import CORS

    app = Flask(__name__, static_folder=str(GODS_EYE / "static"), template_folder=str(GODS_EYE / "static"))
    CORS(app, origins=["http://localhost:5050", "http://localhost:8082", "http://localhost:8090", "http://127.0.0.1:5050"])

    # Health & info
    @app.route("/api/health")
    def health():
        return jsonify({"ok": True, "service": "daniela-unified", "ts": time.time()})

    @app.route("/api/version")
    def version():
        return jsonify({"version": "1.0.0-unified", "core": CORE_OK})

    # ─── God's Eye Blueprint (montado en /gods-eye) ───────────
    if CORE_OK:
        register_gev_routes(app)

    # ─── Avatar 3D de Daniela (módulo + three compartidos con la PWA) ───
    # web_ui.html monta /shared/daniela-avatar.js con el importmap de
    # /vendor/three/ y el GLB rigged de /assets/. Sin duplicar ficheros.
    _MOBILE = ROOT / "frontend" / "apps" / "android-app" / "mobile-app"

    @app.route("/shared/<path:rel>")
    def shared_avatar(rel):
        return send_from_directory(str(_MOBILE / "js"), rel)

    @app.route("/vendor/three/<path:rel>")
    def vendor_three(rel):
        return send_from_directory(str(_MOBILE / "vendor" / "three"), rel)

    @app.route("/assets/<path:rel>")
    def repo_assets(rel):
        return send_from_directory(str(ROOT / "assets"), rel)

    # ─── Voz neural para el avatar (mismo pipeline que la PWA) ───
    sys.path.insert(0, str(_MOBILE))
    try:
        from bridges.comms.voice_pipeline import register_voice_routes

        register_voice_routes(app)
    except Exception as e:  # noqa: BLE001 - el avatar cae a voz del navegador
        print(f"[Avatar] voz no disponible: {e}")

    # ─── Auditoría de seguridad: Daniela experta (/audita en el chat) ───
    @app.route("/api/secops/audit", methods=["POST"])
    def secops_audit():
        from secops.runner import ejecutar, guardar, resumen_para_daniela

        data = request.json or {}
        perfil = data.get("perfil", "rapido")
        if perfil not in ("rapido", "completo"):
            perfil = "rapido"
        try:
            informe = ejecutar(perfil=perfil, raiz=str(ROOT))
            ruta = guardar(informe)
        except Exception as e:  # noqa: BLE001 - la auditoría nunca tumba el chat
            return jsonify({"ok": False, "error": str(e)}), 500
        return jsonify(
            {
                "ok": True,
                "resumen": resumen_para_daniela(informe),
                "totales": informe["totales"],
                "informe": ruta,
            }
        )

    @app.route("/api/secops/latest", methods=["GET"])
    def secops_latest():
        import json as _json
        from pathlib import Path as _Path

        ultimo = _Path("data") / "secops" / "reports" / "latest.json"
        if not ultimo.exists():
            return jsonify({"ok": False, "error": "sin informes aún"}), 404
        return jsonify({"ok": True, "informe": _json.loads(ultimo.read_text(encoding="utf-8"))})

    # ─── Control REAL Windows API ─────────────────────────────
    @app.route("/api/windows/apps", methods=["GET"])
    def list_apps():
        """Lista apps instaladas (Start Menu + Program Files)."""
        try:
            import winreg
            apps = []
            for root_key in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                for subkey in (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"):
                    try:
                        with winreg.OpenKey(root_key, subkey) as key:
                            for i in range(winreg.QueryInfoKey(key)[0]):
                                try:
                                    sk = winreg.EnumKey(key, i)
                                    with winreg.OpenKey(key, sk) as sk_key:
                                        name = winreg.QueryValueEx(sk_key, "DisplayName")[0]
                                        exe = winreg.QueryValueEx(sk_key, "DisplayIcon")[0] if winreg.QueryValueEx(sk_key, "DisplayIcon") else ""
                                        if name and name not in [a["name"] for a in apps]:
                                            apps.append({"name": name, "icon": exe})
                                except OSError:
                                    pass
                    except OSError:
                        pass
            return jsonify({"ok": True, "apps": sorted(apps, key=lambda x: x["name"].lower())[:200]})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/windows/launch", methods=["POST"])
    def launch_app():
        """Lanza app por nombre o ruta exe."""
        data = request.get_json(silent=True) or {}
        target = data.get("target", "").strip()
        args = data.get("args", [])
        if not target:
            return jsonify({"ok": False, "error": "target requerido"}), 400
        try:
            # Si es ruta absoluta
            if os.path.isfile(target):
                proc = subprocess.Popen([target] + args, shell=False)
            else:
                # Buscar en PATH o Start Menu
                proc = subprocess.Popen(["cmd", "/c", "start", "", target] + args, shell=True)
            return jsonify({"ok": True, "pid": proc.pid, "target": target})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/windows/shell", methods=["POST"])
    def run_shell():
        """Ejecuta comando PowerShell / cmd (seguro: solo allowlist)."""
        try:
            data = request.get_json(silent=True) or {}
            cmd = data.get("cmd", "").strip()
            shell = data.get("shell", "powershell")
            # Allowlist básica
            allowed_prefixes = ("Get-", "Start-", "Stop-", "Restart-", "New-Item", "Copy-Item", "Move-Item", "Remove-Item", "Get-Process", "Get-Service", "ipconfig", "ping", "tracert", "nslookup", "netstat", "whoami", "systeminfo", "tasklist", "dir", "ls", "cd")
            if not any(cmd.strip().startswith(p) for p in allowed_prefixes):
                return jsonify({"ok": False, "error": "Comando no en allowlist", "allowed_prefixes": allowed_prefixes}), 403
            if shell == "powershell":
                # PowerShell en Windows puede emitir cp1252; capturar como bytes y decodificar con replace
                res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=30)
                stdout = res.stdout.decode("utf-8", errors="replace") if res.stdout else ""
                stderr = res.stderr.decode("utf-8", errors="replace") if res.stderr else ""
            else:
                res = subprocess.run(["cmd", "/c", cmd], capture_output=True, text=True, timeout=30, shell=True, encoding="utf-8", errors="replace")
                stdout = res.stdout or ""
                stderr = res.stderr or ""
            return jsonify({"ok": True, "stdout": stdout[-5000:], "stderr": stderr[-2000:], "code": res.returncode})
        except subprocess.TimeoutExpired:
            return jsonify({"ok": False, "error": "Timeout 30s"}), 500
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500

    @app.route("/api/windows/files", methods=["POST"])
    def file_ops():
        """Operaciones de archivos (leer, escribir, listar, buscar)."""
        data = request.get_json(silent=True) or {}
        op = data.get("op", "list")
        path = Path(data.get("path", str(Path.home())))
        try:
            if op == "list":
                p = Path(path)
                items = [{"name": f.name, "path": str(f), "is_dir": f.is_dir(), "size": f.stat().st_size if f.is_file() else None, "modified": f.stat().st_mtime} for f in p.iterdir()]
                return jsonify({"ok": True, "path": str(p), "items": items})
            elif op == "read":
                content = Path(path).read_text(encoding="utf-8", errors="ignore")[:10000]
                return jsonify({"ok": True, "path": str(path), "content": content})
            elif op == "write":
                Path(path).write_text(data.get("content", ""), encoding="utf-8")
                return jsonify({"ok": True, "path": str(path)})
            elif op == "search":
                pattern = data.get("pattern", "*")
                matches = [str(f) for f in Path(path).rglob(pattern)][:100]
                return jsonify({"ok": True, "matches": matches})
            else:
                return jsonify({"ok": False, "error": f"op desconocida: {op}"}), 400
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/windows/processes", methods=["GET"])
    def list_processes():
        """Lista procesos (psutil)."""
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "exe", "cmdline"]):
                try:
                    info = p.info
                    if info["name"]:
                        procs.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            procs.sort(key=lambda x: x.get("cpu_percent", 0) or 0, reverse=True)
            return jsonify({"ok": True, "processes": procs[:50]})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/windows/kill", methods=["POST"])
    def kill_process():
        data = request.get_json(silent=True) or {}
        pid = data.get("pid")
        if not pid:
            return jsonify({"ok": False, "error": "pid requerido"}), 400
        try:
            import psutil
            p = psutil.Process(pid)
            p.terminate()
            p.wait(timeout=5)
            return jsonify({"ok": True, "pid": pid})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    # ─── Memoria Persistente (Chroma + SQLite) ────────────────
    @app.route("/api/memory/add", methods=["POST"])
    def memory_add():
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()
        metadata = data.get("metadata", {})
        if not text:
            return jsonify({"ok": False, "error": "text requerido"}), 400
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(DATA_DIR / "chroma"))
            coll = client.get_or_create_collection("daniela_memory")
            idx = coll.count()
            coll.add(documents=[text], metadatas=[metadata], ids=[f"mem-{idx}-{int(time.time())}"])
            return jsonify({"ok": True, "id": f"mem-{idx}"})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/memory/search", methods=["POST"])
    def memory_search():
        data = request.get_json(silent=True) or {}
        query = data.get("query", "").strip()
        n = data.get("n", 5)
        if not query:
            return jsonify({"ok": False, "error": "query requerido"}), 400
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(DATA_DIR / "chroma"))
            coll = client.get_or_create_collection("daniela_memory")
            res = coll.query(query_texts=[query], n_results=n)
            return jsonify({"ok": True, "results": list(zip(res["documents"][0], res["metadatas"][0], res["distances"][0]))})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    # ─── LLM Local (Ollama) + Gemini Fallback ─────────────────
    @app.route("/api/llm/chat", methods=["POST"])
    def llm_chat():
        data = request.get_json(silent=True) or {}
        prompt = data.get("prompt", "").strip()
        model = data.get("model", "llama3.1:8b")
        system = data.get("system", "Eres Daniela, asistente personal. Responde en español, breve, cercano.")
        if not prompt:
            return jsonify({"ok": False, "error": "prompt requerido"}), 400

        # 1) Intentar Ollama local
        try:
            import httpx
            r = httpx.post("http://localhost:11434/api/generate", json={"model": model, "prompt": f"{system}\n\nUsuario: {prompt}\nDaniela:", "stream": False}, timeout=60)
            if r.status_code == 200:
                return jsonify({"ok": True, "reply": r.json().get("response", ""), "source": "ollama"})
        except Exception:
            pass

        # 2) Fallback Gemini
        try:
            import google.genai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                client = genai.Client(api_key=api_key)
                resp = client.models.generate_content(model="gemini-3.7-flash", contents=f"{system}\n\nUsuario: {prompt}\nDaniela:")
                return jsonify({"ok": True, "reply": resp.text.strip(), "source": "gemini"})
        except Exception as e:
            return jsonify({"ok": False, "error": f"LLM error: {e}"}), 500

        return jsonify({"ok": False, "error": "No LLM disponible (instala Ollama o configura GEMINI_API_KEY)"}), 503

    # ─── Proactive Engine (recordatorios, watchers) ───────────
    @app.route("/api/proactive/tasks", methods=["GET", "POST"])
    def proactive_tasks():
        if request.method == "GET":
            return jsonify({"ok": True, "tasks": PROACTIVE_TASKS})
        data = request.get_json(silent=True) or {}
        task = {"id": len(PROACTIVE_TASKS) + 1, "text": data.get("text", ""), "when": data.get("when"), "repeat": data.get("repeat"), "done": False, "created": time.time()}
        PROACTIVE_TASKS.append(task)
        return jsonify({"ok": True, "task": task})

    @app.route("/api/proactive/tasks/<int:tid>/done", methods=["POST"])
    def proactive_done(tid):
        for t in PROACTIVE_TASKS:
            if t["id"] == tid:
                t["done"] = True
                return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "no encontrado"}), 404

    # ─── Web UI Three.js (Gemini) — montado en /ui ────────────
    @app.route("/ui")
    @app.route("/ui/")
    def web_ui():
        return send_from_directory(str(GODS_EYE / "static"), "web_ui.html")

    return app


# ─── Proactive Task Store ─────────────────────────────────────
PROACTIVE_TASKS: list[dict] = []


# ─── HUD Desktop Launcher ─────────────────────────────────────
HUD_PROC: subprocess.Popen | None = None


def launch_hud():
    global HUD_PROC
    hud_script = SYSTEM_DIR / "living_daniela_pc.py"
    if not hud_script.exists():
        print(f"[HUD] No encontrado: {hud_script}")
        return
    print("[HUD] Lanzando living_daniela_pc.py …")
    HUD_PROC = subprocess.Popen([sys.executable, str(hud_script)], cwd=str(SYSTEM_DIR))
    atexit.register(lambda: HUD_PROC and HUD_PROC.terminate())


# ─── Main ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Daniela Unified Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8082)
    parser.add_argument("--no-hud", action="store_true")
    parser.add_argument("--only-hud", action="store_true")
    parser.add_argument("--open-browser", action="store_true")
    args = parser.parse_args()

    if args.only_hud:
        launch_hud()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return

    app = create_app()

    if not args.no_hud:
        threading.Thread(target=launch_hud, daemon=True).start()
        time.sleep(1.5)  # dar tiempo al HUD

    if args.open_browser:
        webbrowser.open(f"http://{args.host}:{args.port}/gods-eye")
        webbrowser.open(f"http://{args.host}:{args.port}/ui")

    print(f"\n🚀 DANIELA UNIFIED corriendo en http://{args.host}:{args.port}")
    print("   ├─ God's Eye 3D   → /gods-eye")
    print("   ├─ API aig  → /api/globe/*, /api/cc/*, /api/economy/*, /api/gamification/*, /api/dna/*")
    print("   ├─ Windows Control → /api/windows/*")
    print("   ├─ Memoria        → /api/memory/*")
    print("   ├─ LLM (Ollama/Gemini) → /api/llm/chat")
    print("   ├─ Proactive      → /api/proactive/tasks")
    print("   └─ Web UI (Three.js)  → /ui")
    if not args.no_hud:
        print("   🖥  HUD Desktop PyQt6 → lanzado en background")
    print()

    try:
        app.run(host=args.host, port=args.port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n👋 Daniela apagada.")


if __name__ == "__main__":
    main()
