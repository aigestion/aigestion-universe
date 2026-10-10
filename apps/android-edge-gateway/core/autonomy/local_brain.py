#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
local_brain.py — E-13 · Daniela sigue hablando cuando se corta la red
=====================================================================

El problema
-----------
Sin datos y sin WiFi, Daniela se queda muda: todo lo que dice pasa por la nube
de Google. Y no es una molestia teorica: es justo cuando mas la necesitas
(perdido en la calle, sin cobertura en el metro) cuando no esta.

Ademas hay un segundo problema, mas sutil: **todo lo que le dices se lo estás
mandando a un tercero**. Un modelo local no solo funciona sin red: tambien es
lo unico que no se va de tu telefono.

La decision que ya tomamos
--------------------------
**No descargar un modelo nuevo.** En el movil ya hay uno: el GGUF de
`com.llmproxy` (Qwen2.5-0.5B, 0,46 GB). El movil va justisimo de memoria
(swap al 98,5 %, 332 MB libres) y con cuatro stacks de LLM locales
compitiendo solo cabe UNO. Anadir otro seria empeorar el problema.

Dos backends, una sola interfaz
-------------------------------
- **ollama** — el PC. Ya funciona y tiene 4 modelos descargados
  (`daniela-local` 3,3 GB, `qwen3.5` 6,6 GB, `deepseek-coder` 776 MB,
  `nomic-embed-text` 274 MB). Es el backend que esta vivo HOY.
- **llamacpp** — el movil. `llama-server` compilado en Termux sirviendo el GGUF
  que ya existe. Es el objetivo de la epica, y es lo que hace que Daniela
  funcione de verdad sin red.

Seguridad
---------
- Hosts en lista cerrada. Nunca una URL que venga de la peticion (SSRF).
  Lo unico configurable es el modelo y el backend, y ambos se validan.
- **Los locales van sin proxy**: si el entorno tiene `HTTP_PROXY` puesto (y en
  esta maquina lo esta), una llamada a `localhost` rebota en el proxy y vuelve
  un 502. Por eso las peticiones locales llevan `proxies={"http": None, ...}`.
- Cero `os.system()`, cero `shell=True`. Este modulo **no arranca nada en el
  movil**: genera el script y te da el comando. El home de Termux es
  inaccesible por adb (no hay `run-as`, no hay `adb root`), asi que prometer
  un "arranque automatico" seria mentir.

Uso
---
    GET  /api/local/status       que backend esta vivo y cual se usaria
    GET  /api/local/models       modelos de cada backend, con tamano
    POST /api/local/ask          {"prompt": "...", "backend": "auto"}
    POST /api/local/test         sonda los dos y mide latencia
    GET  /api/local/config       configuracion
    POST /api/local/config       cambiar backend preferido / modelo / timeout
    GET  /api/local/plan         plan de instalacion en Termux (+ escribe el sh)
    GET  /api/local/benchmark    mediciones guardadas por modelo
    GET  /api/local/history      ultimas respuestas
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, request

# --------------------------------------------------------------------------
#  Rutas y constantes
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "local_brain"
STATE_FILE = DATA_DIR / "estado.json"
BENCH_FILE = DATA_DIR / "benchmark.json"
HISTORY_FILE = DATA_DIR / "historial.json"
PLAN_FILE = DATA_DIR / "instalar_llama_movil.sh"

BACKENDS = ("ollama", "llamacpp")

# Bases permitidas. Lista CERRADA: nunca se construyen desde la peticion.
OLLAMA_BASE = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLAMACPP_BASE = os.getenv("LLAMACPP_URL", "")  # lo rellena el .env o el config

PUERTO_LLAMACPP = 8083  # el 8080 choca con otras cosas y el 8082 es el gateway

# Localhost + proxy no se llevan bien: si HTTP_PROXY esta puesto, una llamada
# a 127.0.0.1 rebota en el proxy y vuelve 502.
SIN_PROXY = {"http": None, "https": None}

TIMEOUT_LOCAL = 150
MAX_HISTORIAL = 50


def _ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _base_ollama() -> str:
    """OLLAMA_HOST puede venir como host:port o con esquema."""
    b = (OLLAMA_BASE or "http://localhost:11434").strip()
    if not b.startswith("http"):
        b = f"http://{b}"
    # OLLAMA_HOST a veces trae ruta; la API vive en la raiz
    return b.rstrip("/")


def _base_llamacpp() -> str:
    cfg = get_instance().config
    b = (cfg.get("llamacpp_url") or LLAMACPP_BASE or "").strip()
    if not b:
        return ""
    if not b.startswith("http"):
        b = f"http://{b}"
    return b.rstrip("/")


# --------------------------------------------------------------------------
#  Backends
# --------------------------------------------------------------------------
def _http() -> Any:
    try:
        import requests  # type: ignore

        return requests
    except Exception:  # noqa: BLE001
        return None


def ollama_modelos(base: str) -> Tuple[bool, List[Dict[str, Any]], str]:
    req = _http()
    if req is None:
        return False, [], "requests no disponible"
    try:
        r = req.get(f"{base}/api/tags", timeout=8, proxies=SIN_PROXY)
        if r.status_code != 200:
            return False, [], f"HTTP {r.status_code}"
        datos = r.json() or {}
    except Exception as e:  # noqa: BLE001
        return False, [], f"{type(e).__name__}: {str(e)[:70]}"
    out = []
    for m in datos.get("models", []):
        d = m.get("details") or {}
        out.append(
            {
                "nombre": m.get("name", ""),
                "tamano_mb": round((m.get("size") or 0) / 1048576),
                "familia": d.get("family", ""),
                "parametros": d.get("parameter_size", ""),
                "cuantizacion": d.get("quantization_level", ""),
                "contexto": d.get("context_length", 0),
                "capacidades": m.get("capabilities") or [],
            }
        )
    return True, out, ""


def ollama_chat(base: str, modelo: str, prompt: str, timeout: int) -> Tuple[bool, str, int, str]:
    req = _http()
    if req is None:
        return False, "", 0, "requests no disponible"
    t0 = time.time()
    try:
        r = req.post(
            f"{base}/api/chat",
            json={
                "model": modelo,
                "stream": False,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=timeout,
            proxies=SIN_PROXY,
        )
        ms = int((time.time() - t0) * 1000)
        if r.status_code != 200:
            return False, "", ms, f"HTTP {r.status_code}: {r.text[:120]}"
        datos = r.json() or {}
        msg = (datos.get("message") or {}).get("content", "")
        if not msg:
            return False, "", ms, "respuesta vacia"
        return True, msg, ms, ""
    except Exception as e:  # noqa: BLE001
        return False, "", int((time.time() - t0) * 1000), f"{type(e).__name__}"


def llamacpp_modelos(base: str) -> Tuple[bool, List[Dict[str, Any]], str]:
    """llama-server expone /v1/models igual que OpenAI."""
    req = _http()
    if req is None:
        return False, [], "requests no disponible"
    try:
        r = req.get(f"{base}/v1/models", timeout=8, proxies=SIN_PROXY)
        if r.status_code != 200:
            return False, [], f"HTTP {r.status_code}"
        datos = r.json() or {}
    except Exception as e:  # noqa: BLE001
        return False, [], f"{type(e).__name__}: {str(e)[:70]}"
    out = [
        {
            "nombre": m.get("id", ""),
            "tamano_mb": 0,
            "familia": "gguf",
            "parametros": "",
            "cuantizacion": "",
            "contexto": 0,
            "capacidades": ["chat"],
        }
        for m in (datos.get("data") or [])
    ]
    return True, out, ""


def llamacpp_chat(base: str, modelo: str, prompt: str, timeout: int) -> Tuple[bool, str, int, str]:
    req = _http()
    if req is None:
        return False, "", 0, "requests no disponible"
    t0 = time.time()
    try:
        cuerpo: Dict[str, Any] = {
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        if modelo:
            cuerpo["model"] = modelo
        r = req.post(f"{base}/v1/chat/completions", json=cuerpo, timeout=timeout, proxies=SIN_PROXY)
        ms = int((time.time() - t0) * 1000)
        if r.status_code != 200:
            return False, "", ms, f"HTTP {r.status_code}: {r.text[:120]}"
        datos = r.json() or {}
        opciones = datos.get("choices") or []
        if not opciones:
            return False, "", ms, "respuesta vacia"
        msg = (opciones[0].get("message") or {}).get("content") or ""
        return (True, msg, ms, "") if msg else (False, "", ms, "respuesta vacia")
    except Exception as e:  # noqa: BLE001
        return False, "", int((time.time() - t0) * 1000), f"{type(e).__name__}"


# --------------------------------------------------------------------------
#  Estado
# --------------------------------------------------------------------------
@dataclass
class Medicion:
    backend: str
    modelo: str
    ms: int
    ok: bool
    cuando: str = ""
    nota: str = ""


class LocalBrain:
    """Elige el backend local que este vivo y mide cual responde antes."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.config: Dict[str, Any] = {
            "backend_preferido": "auto",  # auto | ollama | llamacpp
            "modelo_ollama": "daniela-local",
            "modelo_llamacpp": "",
            "llamacpp_url": "",
            "timeout_s": TIMEOUT_LOCAL,
        }
        self.benchmark: Dict[str, Any] = {}
        self.historial: List[Dict[str, Any]] = []
        self.ultimo: Dict[str, Any] = {}
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._cargar()

    # ── persistencia ──────────────────────────────────────────
    def _cargar(self) -> None:
        if STATE_FILE.exists():
            try:
                self.config.update(
                    json.loads(STATE_FILE.read_text(encoding="utf-8")).get("config", {})
                )
            except Exception:  # noqa: BLE001
                pass
        if BENCH_FILE.exists():
            try:
                self.benchmark = json.loads(BENCH_FILE.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                self.benchmark = {}
        if HISTORY_FILE.exists():
            try:
                self.historial = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                self.historial = []

    def guardar(self) -> None:
        with self._lock:
            try:
                STATE_FILE.write_text(
                    json.dumps(
                        {"config": self.config, "ultimo": self.ultimo, "cuando": _ahora()},
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                BENCH_FILE.write_text(
                    json.dumps(self.benchmark, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                HISTORY_FILE.write_text(
                    json.dumps(self.historial[-MAX_HISTORIAL:], ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:  # noqa: BLE001
                pass

    # ── descubrimiento ────────────────────────────────────────
    def modelos(self) -> Dict[str, Any]:
        ok_o, mods_o, nota_o = ollama_modelos(_base_ollama())
        base_l = _base_llamacpp()
        if base_l:
            ok_l, mods_l, nota_l = llamacpp_modelos(base_l)
        else:
            ok_l, mods_l, nota_l = False, [], "sin URL configurada"
        return {
            "ollama": {"vivo": ok_o, "modelos": mods_o, "nota": nota_o, "base": _base_ollama()},
            "llamacpp": {
                "vivo": ok_l,
                "modelos": mods_l,
                "nota": nota_l,
                "base": base_l or "(no configurado)",
            },
        }

    def elegir(self, preferido: str = "auto") -> str:
        """Devuelve el backend a usar. 'auto' = el que este vivo, ollama primero."""
        if preferido in BACKENDS:
            return preferido
        estado = self.modelos()
        for b in BACKENDS:
            if estado[b]["vivo"]:
                return b
        return ""

    # ── preguntar ─────────────────────────────────────────────
    def preguntar(
        self, prompt: str, backend: str = "auto", modelo: str = "", timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        if not prompt:
            return {"ok": False, "error": "prompt vacio"}
        if len(prompt) > 8000:
            prompt = prompt[:8000]

        elegido = self.elegir(backend)
        if not elegido:
            return {
                "ok": False,
                "error": "ningun backend local responde. Mira /api/local/plan para "
                "levantar llama.cpp en el movil, o arranca Ollama en el PC.",
            }

        timeout = int(timeout or self.config.get("timeout_s", TIMEOUT_LOCAL))
        if elegido == "ollama":
            modelo = modelo or self.config.get("modelo_ollama", "daniela-local")
            ok, texto, ms, nota = ollama_chat(_base_ollama(), modelo, prompt, timeout)
        else:
            modelo = modelo or self.config.get("modelo_llamacpp", "")
            ok, texto, ms, nota = llamacpp_chat(_base_llamacpp(), modelo, prompt, timeout)

        registro = {
            "ts": _ahora(),
            "backend": elegido,
            "modelo": modelo,
            "ms": ms,
            "ok": ok,
            "prompt": prompt[:200],
            "respuesta": texto[:400],
            "nota": nota,
        }
        with self._lock:
            self.historial.append(registro)
            self.historial = self.historial[-MAX_HISTORIAL:]
            clave = f"{elegido}:{modelo}"
            m = self.benchmark.get(clave) or {"veces": 0, "ok": 0, "ms_total": 0, "ms_min": None}
            m["veces"] += 1
            m["ok"] += 1 if ok else 0
            m["ms_total"] += ms
            m["ms_medio"] = round(m["ms_total"] / max(1, m["veces"]))
            if ms and (m["ms_min"] is None or ms < m["ms_min"]):
                m["ms_min"] = ms
            m["ultimo"] = _ahora()
            self.benchmark[clave] = m
            self.ultimo = registro
            self.guardar()

        return {
            "ok": ok,
            "backend": elegido,
            "modelo": modelo,
            "ms": ms,
            "respuesta": texto,
            "nota": nota,
        }

    def sondar(self) -> Dict[str, Any]:
        """Prueba los dos backends con una pregunta de un token."""
        out: Dict[str, Any] = {"cuando": _ahora(), "backends": {}}
        estado = self.modelos()
        for b in BACKENDS:
            info = estado[b]
            if not info["vivo"]:
                out["backends"][b] = {"vivo": False, "nota": info["nota"]}
                continue
            modelo = ""
            if info["modelos"]:
                modelo = info["modelos"][0]["nombre"]
            if b == "ollama":
                modelo = self.config.get("modelo_ollama") or modelo
                ok, _t, ms, nota = ollama_chat(
                    _base_ollama(), modelo, "di Hola", self.config.get("timeout_s", 90)
                )
            else:
                modelo = self.config.get("modelo_llamacpp") or modelo
                ok, _t, ms, nota = llamacpp_chat(
                    _base_llamacpp(), modelo, "di Hola", self.config.get("timeout_s", 90)
                )
            out["backends"][b] = {"vivo": True, "modelo": modelo, "ok": ok, "ms": ms, "nota": nota}
        vivos = [b for b, d in out["backends"].items() if d.get("vivo") and d.get("ok")]
        out["usaria"] = vivos[0] if vivos else ""
        self.ultimo["sonda"] = out
        self.guardar()
        return out

    def estado(self) -> Dict[str, Any]:
        m = self.modelos()
        return {
            "config": dict(self.config),
            "ollama": m["ollama"],
            "llamacpp": m["llamacpp"],
            "usaria": self.elegir(self.config.get("backend_preferido", "auto")),
            "modelos_ollama": len(m["ollama"]["modelos"]),
            "cuando": _ahora(),
        }

    # ── plan de instalacion en el movil ───────────────────────
    def plan(self, escribir: bool = True) -> Dict[str, Any]:
        """Comandos exactos para llama.cpp en Termux. No ejecuta nada."""
        pasos = [
            ("1", "Dependencias", "pkg install -y git cmake clang make"),
            (
                "2",
                "Compilar llama.cpp (tarda unos 10-15 min)",
                "git clone --depth 1 https://github.com/ggerganov/llama.cpp "
                "~/llama.cpp && cd ~/llama.cpp && "
                "cmake -B build -DLLAMA_CURL=OFF && cmake --build build -j4",
            ),
            (
                "3",
                "Localizar el GGUF que YA tienes (no descargues otro)",
                "find /data/data /sdcard -name '*.gguf' 2>/dev/null | head",
            ),
            (
                "4",
                "Arrancar el servidor",
                f"cd ~/llama.cpp && ./build/bin/llama-server -m <RUTA_DEL_GGUF> "
                f"-c 2048 --port {PUERTO_LLAMACPP} --host 0.0.0.0",
            ),
            (
                "5",
                "Decirle al proyecto donde esta",
                f"LLAMACPP_URL=http://<IP_DEL_MOVIL>:{PUERTO_LLAMACPP}  "
                f"(en el .env) o POST /api/local/config con llamacpp_url",
            ),
        ]
        script = [
            "#!/data/data/com.termux/files/usr/bin/bash",
            "# Generado por local_brain.py (E-13) el " + _ahora(),
            "# NO descarga ningun modelo: reutiliza el GGUF que ya hay en el",
            "# movil (com.llmproxy, Qwen2.5-0.5B, 0,46 GB). El movil va justo",
            "# de memoria (swap al 98,5 %) y solo cabe UN modelo a la vez.",
            "set -e",
            "echo '== 1. dependencias =='",
            "pkg install -y git cmake clang make",
            "echo '== 2. compilar llama.cpp =='",
            "[ -d ~/llama.cpp ] || git clone --depth 1 "
            "https://github.com/ggerganov/llama.cpp ~/llama.cpp",
            "cd ~/llama.cpp",
            "cmake -B build -DLLAMA_CURL=OFF",
            "cmake --build build -j4",
            "echo '== 3. buscar el GGUF que ya existe =='",
            "GGUF=$(find /data/data /sdcard -name '*.gguf' 2>/dev/null | head -1)",
            'if [ -z "$GGUF" ]; then',
            "  echo 'NO se encontro ningun GGUF. Descarga uno pequeno a mano.'",
            "  exit 1",
            "fi",
            'echo "usando: $GGUF"',
            f"echo '== 4. arrancar en el puerto {PUERTO_LLAMACPP} =='",
            f'./build/bin/llama-server -m "$GGUF" -c 2048 '
            f"--port {PUERTO_LLAMACPP} --host 0.0.0.0",
        ]
        if escribir:
            try:
                PLAN_FILE.write_text("\n".join(script) + "\n", encoding="utf-8")
            except Exception:  # noqa: BLE001
                pass
        return {
            "pasos": [{"paso": n, "titulo": t, "comando": c} for n, t, c in pasos],
            "script": str(PLAN_FILE.relative_to(ROOT)).replace("\\", "/"),
            "puerto": PUERTO_LLAMACPP,
            "nota": (
                "Este modulo NO arranca nada en el movil: el home de "
                "Termux es inaccesible por adb (no hay run-as ni adb "
                "root), asi que tienes que ejecutar el script tu."
            ),
        }


_instancia: Optional[LocalBrain] = None
_lock = threading.RLock()


def get_instance() -> LocalBrain:
    global _instancia
    with _lock:
        if _instancia is None:
            _instancia = LocalBrain()
        return _instancia


# --------------------------------------------------------------------------
#  Rutas
# --------------------------------------------------------------------------
local_bp = Blueprint("local_brain", __name__)


@local_bp.route("/api/local/status", methods=["GET"])
def local_status():
    return jsonify({"ok": True, **get_instance().estado()})


@local_bp.route("/api/local/models", methods=["GET"])
def local_models():
    return jsonify({"ok": True, **get_instance().modelos()})


@local_bp.route("/api/local/ask", methods=["POST"])
def local_ask():
    cuerpo = request.get_json(silent=True) or {}
    prompt = cuerpo.get("prompt") or ""
    if not prompt:
        return jsonify({"ok": False, "error": "falta prompt"}), 400
    backend = str(cuerpo.get("backend", "auto"))
    if backend not in ("auto",) + BACKENDS:
        return (
            jsonify(
                {"ok": False, "error": f"backend debe ser auto, {BACKENDS[0]} o " f"{BACKENDS[1]}"}
            ),
            400,
        )
    return jsonify(
        get_instance().preguntar(prompt, backend, cuerpo.get("modelo", ""), cuerpo.get("timeout"))
    )


@local_bp.route("/api/local/test", methods=["POST"])
def local_test():
    return jsonify({"ok": True, **get_instance().sondar()})


@local_bp.route("/api/local/config", methods=["GET"])
def local_config_get():
    return jsonify({"ok": True, "config": get_instance().config, "backends": list(BACKENDS)})


@local_bp.route("/api/local/config", methods=["POST"])
def local_config_post():
    cuerpo = request.get_json(silent=True) or {}
    lb = get_instance()
    with lb._lock:
        if "backend_preferido" in cuerpo:
            v = str(cuerpo["backend_preferido"])
            if v in ("auto",) + BACKENDS:
                lb.config["backend_preferido"] = v
        for k in ("modelo_ollama", "modelo_llamacpp", "llamacpp_url"):
            if k in cuerpo:
                lb.config[k] = str(cuerpo[k])[:300]
        if "timeout_s" in cuerpo:
            try:
                lb.config["timeout_s"] = max(5, min(600, int(cuerpo["timeout_s"])))
            except (TypeError, ValueError):
                pass
        lb.guardar()
    return jsonify({"ok": True, "config": lb.config})


@local_bp.route("/api/local/plan", methods=["GET"])
def local_plan():
    escribir = request.args.get("escribir", "1") == "1"
    return jsonify({"ok": True, **get_instance().plan(escribir)})


@local_bp.route("/api/local/benchmark", methods=["GET"])
def local_benchmark():
    return jsonify({"ok": True, "benchmark": get_instance().benchmark})


@local_bp.route("/api/local/history", methods=["GET"])
def local_history():
    limite = 20
    try:
        limite = max(1, min(100, int(request.args.get("limit", 20))))
    except ValueError:
        pass
    return jsonify({"ok": True, "historial": get_instance().historial[-limite:]})


def register_local_routes(app) -> int:
    app.register_blueprint(local_bp)
    print(
        "[Local Brain] Routes registered: /api/local/* "
        "(status, models, ask, test, config, plan, benchmark, history)"
    )
    return 8


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo() -> None:
    print("=" * 66)
    print("E-13 · local_brain — Daniela sin red")
    print("=" * 66)
    lb = get_instance()

    print("\n-- Backends --")
    e = lb.estado()
    for b in BACKENDS:
        d = e[b]
        marca = "VIVO" if d["vivo"] else "caido"
        print(f"  {b:<9} {marca:<6} {len(d['modelos'])} modelos  {d['nota']}")
    print(f"  usaria: {e['usaria'] or '(ninguno)'}")

    print("\n-- Modelos de Ollama --")
    for m in e["ollama"]["modelos"]:
        print(
            f"  {m['nombre']:<28} {m['tamano_mb']:>6} MB  {m['parametros']} " f"{m['cuantizacion']}"
        )

    print("\n-- Pregunta real --")
    r = lb.preguntar("Responde exactamente: Hola", timeout=90)
    if r.get("ok"):
        print(f"  [{r['backend']} / {r['modelo']}] {r['ms']} ms")
        print(f"  -> {r['respuesta'][:160]}")
    else:
        print(f"  fallo: {r.get('nota') or r.get('error')}")

    print("\n-- Plan para el movil --")
    p = lb.plan()
    print(f"  script: {p['script']}")
    for paso in p["pasos"]:
        print(f"  {paso['paso']}. {paso['titulo']}")

    print("\n-- Benchmark --")
    for k, v in lb.benchmark.items():
        print(f"  {k:<40} {v['ok']}/{v['veces']} ok  medio {v['ms_medio']} ms")

    print("\n" + "=" * 66)


if __name__ == "__main__":
    _demo()