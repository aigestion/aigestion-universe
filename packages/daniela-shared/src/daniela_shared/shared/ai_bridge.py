"""Daniela AI Bridge - REAL AI via FreeLLMAPIConnector + Ollama embeddings."""

import asyncio
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from flask import Blueprint, jsonify, request

ai_bp = Blueprint("ai", __name__)

# Repo root por MARCADOR: este fichero vivia en `<repo>/daniela-os/shared/` y
# con tres `dirname` llegaba a la raiz. Al entrar en `gev/daniela-os/shared/`
# los tres `dirname` dan `<repo>/gev`, `shared/` deja de existir ahi y
# `aig_shared` no se encuentra: el blueprint `ai` ENTERO dejaba de registrarse
# (Daniela sin IA). Un indice fijo se rompe en silencio al mover el fichero.
def _repo_root() -> str:
    aqui = Path(os.path.abspath(__file__))
    for c in (aqui.parent, *aqui.parents):
        if (c / ".git").exists() or (c / "tests" / "conftest.py").exists():
            return str(c)
    return os.path.dirname(os.path.dirname(os.path.dirname(str(aqui))))


_REPO_ROOT = _repo_root()
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_REPO_ROOT, ".env"))
except Exception:
    pass

try:
    from shared.ai.connector import FreeLLMAPIConnector
except Exception:  # fallback when aig-shared is not on sys.path yet
    for _p in (
        _REPO_ROOT,
        os.path.join(_REPO_ROOT, "shared"),
        os.path.join(_REPO_ROOT, "aig-shared"),    # copia espejo
        os.path.dirname(_REPO_ROOT),               # hermano del repo
    ):
        if os.path.isdir(_p) and _p not in sys.path:
            sys.path.insert(0, _p)
    from shared.ai.connector import FreeLLMAPIConnector

# Las herramientas del visor viven en el MISMO paquete `shared`; hay que tener
# `gev/daniela-os` en el path para importarlo como `shared.gev_tools`
# (es como lo carga `server.py`).
_PAQUETE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PAQUETE not in sys.path:
    sys.path.insert(0, _PAQUETE)
try:
    from shared import gev_tools
except ImportError:  # pragma: no cover - import como modulo suelto
    try:
        from . import gev_tools  # type: ignore
    except ImportError:
        gev_tools = None  # type: ignore

# E-34: Ollama for embeddings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text"
EMBED_TIMEOUT = 30.0

DEFAULT_BASE_URL = "http://localhost:3002/v1"
CHAT_TIMEOUT = 90.0

DREAM_SYSTEM = "Eres Daniela, interprete de suenos calida y breve (max 120 palabras)"
MUSE_SYSTEM = "Eres Daniela, co-escritora creativa y breve. Continua la historia con 80-150 palabras."

_state = {
    "chats": 0,
    "dreams": 0,
    "muses": 0,
    "models_queries": 0,
    "tool_calls": 0,
    "errors": 0,
}

NO_KEY_MSG = "FREELLMAPI_KEY no configurada"


def _api_key():
    return (os.getenv("FREELLMAPI_KEY") or "").strip()


def _base_url():
    return (os.getenv("FREELLMAPI_URL") or DEFAULT_BASE_URL).strip().rstrip("/") or DEFAULT_BASE_URL


def _connector(model="auto"):
    return FreeLLMAPIConnector(api_key=_api_key(), model=model or "auto")


def _resp_to_dict(resp):
    return {
        "content": resp.content,
        "model": resp.model,
        "provider": resp.provider,
        "input_tokens": resp.input_tokens,
        "output_tokens": resp.output_tokens,
        "latency_ms": resp.latency_ms,
    }


def _run_health(conn):
    try:
        return asyncio.run(conn.health())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(conn.health())
        finally:
            loop.close()


def _sistema_herramientas() -> str | None:
    """Bloque de sistema con el catálogo, si el módulo de herramientas cargó."""
    if gev_tools is None:
        return None
    try:
        return gev_tools.describir()
    except Exception:  # noqa: BLE001  el chat no puede caerse por esto
        return None


@ai_bp.route("/api/ai/tools")
def ai_tools():
    """Catálogo de herramientas que Daniela puede usar sobre el visor."""
    if gev_tools is None:
        return jsonify({"ok": False, "error": "gev_tools no disponible",
                        "tools": []}), 503
    return jsonify({
        "ok": True,
        "n": len(gev_tools.HERRAMIENTAS),
        "tools": gev_tools.esquemas(),
        "nombres": gev_tools.nombres(),
        "solo_lectura": [
            n for n in gev_tools.nombres()
            if gev_tools.HERRAMIENTAS[n].solo_lectura
        ],
    })


@ai_bp.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    data = request.json or {}
    messages = data.get("messages", [])
    model = data.get("model") or "auto"
    max_tokens = data.get("max_tokens", 500)
    # Las herramientas del visor entran por defecto: Daniela tiene que poder
    # GESTIONAR su pantalla, no solo hablar de ella. `tools: false` las apaga
    # (para chats que no quieren ni la posibilidad de una llamada).
    con_herramientas = bool(data.get("tools", True))
    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "messages requerido (lista no vacia)"}), 400
    if not _api_key():
        _state["errors"] += 1
        return jsonify({"error": NO_KEY_MSG}), 503
    try:
        sistema = _sistema_herramientas() if con_herramientas else None
        msgs = ([{"role": "system", "content": sistema}] + list(messages)
                if sistema else list(messages))
        conn = _connector(model)
        resp = conn.chat(msgs, model=model, max_tokens=max_tokens,
                         timeout=CHAT_TIMEOUT)
        _state["chats"] += 1
        out = _resp_to_dict(resp)
        out["tool"] = None
        if not sistema:
            return jsonify(out)

        # Segunda pasada: si el modelo pidió una herramienta, se ejecuta y se
        # le devuelve el resultado REAL para que lo cuente. Una sola vuelta:
        # si vuelve a pedir, se devuelve tal cual (que decida el cliente).
        llamada = gev_tools.detectar(resp.content) if gev_tools else None
        if llamada is None:
            return jsonify(out)
        nombre, args = llamada
        sujeto = (gev_tools.sujeto_por_defecto() if gev_tools else None)
        resultado = (gev_tools.ejecutar(nombre, args, sujeto=sujeto)
                     if gev_tools else {"ok": False, "error": "sin gev_tools"})
        _state["tool_calls"] += 1
        out["tool"] = {"name": nombre, "args": args}
        out["tool_result"] = resultado

        segunda = msgs + [
            {"role": "assistant", "content": resp.content},
            {"role": "system", "content":
             "Resultado de la herramienta "
             f"`{nombre}` (JSON):\n"
             + json.dumps(resultado, ensure_ascii=False, default=str)[:8000]
             + "\n\nResponde al usuario en español usando esos datos, breve y "
               "concreto. No vuelvas a pedir la herramienta."},
        ]
        resp2 = conn.chat(segunda, model=model, max_tokens=max_tokens,
                          timeout=CHAT_TIMEOUT)
        _state["chats"] += 1
        final = _resp_to_dict(resp2)
        final["tool"] = out["tool"]
        final["tool_result"] = resultado
        return jsonify(final)
    except Exception as e:
        _state["errors"] += 1
        return jsonify({"error": str(e)[:300]}), 502


@ai_bp.route("/api/ai/health")
def ai_health():
    key_configured = bool(_api_key())
    try:
        info = _run_health(_connector())
    except Exception as e:
        info = {"status": "unhealthy", "provider": "freellmapi", "error": str(e)[:200]}
    info = dict(info or {})
    info["key_configured"] = key_configured
    return jsonify(info)


@ai_bp.route("/api/ai/models")
def ai_models():
    if not _api_key():
        return jsonify({"error": NO_KEY_MSG}), 503
    _state["models_queries"] += 1
    url = _base_url() + "/models"
    try:
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + _api_key()})
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _state["errors"] += 1
        return jsonify({"error": str(e)[:300]}), 502
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        models = payload["data"]
    elif isinstance(payload, list):
        models = payload
    else:
        models = payload
    if isinstance(models, list):
        return jsonify({"models": models, "count": len(models)})
    return jsonify({"models": models})


@ai_bp.route("/api/ai/dream/interpret", methods=["POST"])
def ai_dream_interpret():
    data = request.json or {}
    dream = (data.get("dream") or "").strip()
    model = data.get("model") or "auto"
    if not dream:
        return jsonify({"error": "dream requerido"}), 400
    if not _api_key():
        _state["errors"] += 1
        return jsonify({"error": NO_KEY_MSG}), 503
    try:
        conn = _connector(model)
        resp = conn.chat(
            [{"role": "system", "content": DREAM_SYSTEM}, {"role": "user", "content": dream}],
            model=model,
            max_tokens=data.get("max_tokens", 300),
            timeout=CHAT_TIMEOUT,
        )
        _state["dreams"] += 1
        out = _resp_to_dict(resp)
        out["dream"] = dream
        return jsonify(out)
    except Exception as e:
        _state["errors"] += 1
        return jsonify({"error": str(e)[:300]}), 502


@ai_bp.route("/api/ai/muse/continue", methods=["POST"])
def ai_muse_continue():
    data = request.json or {}
    story = (data.get("story") or "").strip()
    twist = bool(data.get("twist", False))
    model = data.get("model") or "auto"
    if not story:
        return jsonify({"error": "story requerido"}), 400
    if not _api_key():
        _state["errors"] += 1
        return jsonify({"error": NO_KEY_MSG}), 503
    tail = "Dale un giro inesperado." if twist else "Continua de forma natural."
    try:
        conn = _connector(model)
        resp = conn.chat(
            [{"role": "system", "content": MUSE_SYSTEM}, {"role": "user", "content": story + "\n" + tail}],
            model=model,
            max_tokens=data.get("max_tokens", 400),
            timeout=CHAT_TIMEOUT,
        )
        _state["muses"] += 1
        out = _resp_to_dict(resp)
        out["twist"] = twist
        return jsonify(out)
    except Exception as e:
        _state["errors"] += 1
        return jsonify({"error": str(e)[:300]}), 502


@ai_bp.route("/api/ai/status")
def ai_status():
    return jsonify({**_state, "key_configured": bool(_api_key()), "base_url": _base_url()})


# ---------------------------------------------------------------------------
# E-34: Ollama Embeddings
# ---------------------------------------------------------------------------

def _ollama_embed(texts, model=EMBED_MODEL, timeout=EMBED_TIMEOUT):
    """Generate embeddings via Ollama /api/embed endpoint."""
    url = f"{OLLAMA_BASE_URL}/api/embed"
    payload = json.dumps({"model": model, "input": texts}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.time()
    resp = urllib.request.urlopen(req, timeout=timeout)
    data = json.loads(resp.read().decode("utf-8"))
    latency = (time.time() - start) * 1000
    embeddings = data.get("embeddings", [])
    return embeddings, latency


@ai_bp.route("/api/ai/embeddings", methods=["POST"])
def ai_embeddings():
    """
    POST /api/ai/embeddings
    Body: {"texts": ["hello", "world"], "model": "nomic-embed-text"}
    Returns: {"embeddings": [[...], [...]], "model": "...", "count": 2, "latency_ms": ...}
    """
    data = request.json or {}
    texts = data.get("texts", [])
    model = data.get("model", EMBED_MODEL)

    if not isinstance(texts, list) or not texts:
        return jsonify({"error": "texts requerido (lista no vacia)"}), 400
    if not isinstance(texts[0], str):
        return jsonify({"error": "texts debe ser lista de strings"}), 400

    try:
        embeddings, latency = _ollama_embed(texts, model=model)
        _state["embeddings"] = _state.get("embeddings", 0) + 1
        return jsonify({
            "embeddings": embeddings,
            "model": model,
            "count": len(embeddings),
            "dimensions": len(embeddings[0]) if embeddings else 0,
            "latency_ms": round(latency, 2),
        })
    except Exception as e:
        _state["errors"] += 1
        return jsonify({"error": str(e)[:300], "model": model}), 502


@ai_bp.route("/api/ai/embeddings/status")
def ai_embeddings_status():
    """Check if Ollama is reachable and has the embedding model."""
    try:
        start = time.time()
        url = f"{OLLAMA_BASE_URL}/api/tags"
        resp = urllib.request.urlopen(url, timeout=5)
        data = json.loads(resp.read().decode("utf-8"))
        latency = (time.time() - start) * 1000
        models = [m["name"] for m in data.get("models", [])]
        has_embed = any(EMBED_MODEL in m for m in models)
        return jsonify({
            "ollama_online": True,
            "latency_ms": round(latency, 2),
            "models": models,
            "embed_model_available": has_embed,
            "embed_model": EMBED_MODEL,
            "base_url": OLLAMA_BASE_URL,
        })
    except Exception as e:
        return jsonify({
            "ollama_online": False,
            "error": str(e)[:200],
            "base_url": OLLAMA_BASE_URL,
        })
