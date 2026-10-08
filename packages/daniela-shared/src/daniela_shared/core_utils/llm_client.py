"""Cliente LLM compartido (Fase 3 extendida) — una sola puerta al router E-32.

Lo usan el swarm (`agents.swarm_intelligence`) y el code-gen
(`code_generation_agent`). Capas:

1. `llm_available()` — True si hay clave remota con pinta de real u
   Ollama local reachable (TCP probe 3 s, 0 tokens).
2. `llm_call(prompt)` — `model_router.responder()` tal cual
   ({ok, proveedor, modelo, texto, latencia_ms, intentos}) o fallo
   honesto si no hay router. Nunca lanza excepcion.

Sin claves reales (placeholders de Fase 0, Ollama caido) todo degrada
a flujos simulados etiquetados. Nunca se llama a ciegas con timeouts
largos: el Ollama muerto colgaba 70 s por intento (TIMEOUT_LOCAL).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

# Raiz del repo (este modulo vive en core/, o sea UNO dentro de la raiz).
# OJO: ponia parents[2], que se salia a C:\Users\Alejandro: por eso
# `load_dotenv(_REPO_ROOT / ".env")` no cargaba NADA y las claves solo
# aparecian si el proceso ya las traia en el entorno.
_REPO_ROOT = Path(__file__).resolve().parents[1]

# Env vars con clave de LLM (las que el router E-32 sabe usar + host local).
LLM_ENV_VARS = (
    "GEMINI_API_KEY", "GOOGLE_API_KEY", "DEEPSEEK_API_KEY",
    "OPENROUTER_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY",
    "COHERE_API_KEY", "QWEN_API_KEY", "DASHSCOPE_API_KEY",
    "TENCENT_HUNYUAN_API_KEY", "HUGGINGFACE_TOKEN", "OLLAMA_HOST",
)

# Fragmentos tipicos de valores placeholder (Fase 0 redacto las reales).
PLACEHOLDER_HINTS = (
    "replace_with", "your_", "your-", "example", "tu_clave",
    "changeme", "change-me", "xxxx", "test", "demo-key",
)


def cargar_env() -> None:
    """Carga .env de la raiz si existe (sin pisar variables definidas)."""
    try:
        from dotenv import load_dotenv

        load_dotenv(_REPO_ROOT / ".env")
    except Exception:
        pass


def clave_valida(valor: str | None) -> bool:
    """True si parece una clave real (no vacia ni placeholder de ejemplo)."""
    v = (valor or "").strip()
    if len(v) < 8:
        return False
    return not any(h in v.lower() for h in PLACEHOLDER_HINTS)


def ollama_vivo(host: str, timeout_s: float = 3.0) -> bool:
    """TCP connect rapido: OLLAMA_HOST configurado no significa reachable."""
    import socket
    from urllib.parse import urlparse

    h = (host or "").strip()
    if not h:
        return False
    if "://" not in h:
        h = "http://" + h
    try:
        u = urlparse(h)
        with socket.create_connection(
            (u.hostname or "127.0.0.1", u.port or 11434), timeout=timeout_s
        ):
            return True
    except Exception:
        return False


def llm_available() -> bool:
    """Hay LLM usable? Clave remota real, u Ollama reachable."""
    cargar_env()
    for var in LLM_ENV_VARS:
        v = os.getenv(var) or ""
        if var == "OLLAMA_HOST":
            if v.strip() and ollama_vivo(v):
                return True
            continue
        if clave_valida(v):
            return True
    return False


def _rutas_router() -> list[Path]:
    """Rutas candidatas al enrutador E-32, en orden.

    `mobile-app/` en la raiz del repo es un FICHERO PUNTERO de 36 bytes (no un
    directorio): construir el path a ciegas daba FileNotFoundError y
    `llm_call()` devolvia "router no disponible" para siempre sin importar
    cuantas claves hubiera. Se resuelve el puntero como hace `core/model_router`.
    """
    rutas = [
        _REPO_ROOT / "frontend" / "apps" / "android-app" / "mobile-app"
        / "core" / "autonomy" / "model_router.py",
        _REPO_ROOT / "scripts" / "core" / "model_router.py",
    ]
    puntero = _REPO_ROOT / "mobile-app"
    if puntero.is_file():
        dest = (_REPO_ROOT / puntero.read_text(encoding="utf-8").strip()).resolve()
        rutas.append(dest / "core" / "autonomy" / "model_router.py")
    return rutas


def _router_de_modelos():
    """Carga el enrutador de modelos (E-32) por ruta, con sus candidatas.

    Vive en `frontend/apps/android-app/mobile-app/core/autonomy/model_router.py`,
    y `mobile-app/` no es un paquete Python (lleva guion ni es directorio en la
    raiz) ni esta en `sys.path` de los procesos de raiz (`daniela`, `hermes`),
    asi que se carga por ruta bajo un nombre propio. El modulo es autocontenido
    (stdlib + flask), asi que no arrastra imports internos de `core/`.
    """
    from importlib.util import module_from_spec, spec_from_file_location

    ruta = next((r for r in _rutas_router() if r.is_file()), None)
    if ruta is None:
        raise ImportError(
            "enrutador no encontrado. Rutas probadas:\n  "
            + "\n  ".join(str(r) for r in _rutas_router())
        )
    spec = spec_from_file_location("_aig_model_router", ruta)
    if spec is None or spec.loader is None:
        raise ImportError(f"enrutador no cargable: {ruta}")
    mod = module_from_spec(spec)
    sys.modules["_aig_model_router"] = mod
    spec.loader.exec_module(mod)
    return mod.get_instance


def llm_call(prompt: str, max_tokens: int = 512,
             proveedor: str | None = None) -> dict[str, Any]:
    """Llama al router de modelos E-32. Nunca lanza excepcion."""
    t0 = time.perf_counter()
    try:
        get_instance = _router_de_modelos()
    except Exception as e:
        return {"ok": False, "error": f"router no disponible: {e}", "intentos": []}
    try:
        r = get_instance().responder(prompt, max_tokens=max_tokens,
                                     proveedor=proveedor)
    except Exception as e:
        return {"ok": False, "error": f"router fallo: {e}", "intentos": []}
    if isinstance(r, dict):
        r.setdefault("latencia_ms", round((time.perf_counter() - t0) * 1000, 1))
        return r
    return {"ok": False, "error": "router devolvio formato inesperado", "intentos": []}
