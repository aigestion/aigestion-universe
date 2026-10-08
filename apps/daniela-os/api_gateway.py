#!/usr/bin/env python3
"""
AIGestion API Gateway v1.0
===========================
Gateway publico que expone endpoints REST para consumo externo.
Features:
- Autenticacion JWT
- Rate limiting
- Routing a modulos del core
- Webhooks
- Documentacion OpenAPI (Swagger)

Autor: AIGestion Team
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

from flask import Flask, Response, jsonify, request

# ── Configuracion ─────────────────────────────────────────────

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

JWT_SECRET = os.getenv("AIGESTION_JWT_SECRET") or os.getenv("JWT_SECRET")
if not JWT_SECRET or JWT_SECRET in {
    "change-me-in-production",
    "aigestion-super-secret-key-change-in-production",
    "aig-super-secret-key-change-in-production",
}:
    raise RuntimeError(
        "AIGESTION_JWT_SECRET/JWT_SECRET no definido (o es el default inseguro): define un secreto de alto entropo."
    )
API_RATE_LIMIT = int(os.getenv("AIGESTION_RATE_LIMIT", "100"))  # requests per hour

# Rate limiting simple en memoria
_rate_tracker: dict[str, list[float]] = {}


def _check_rate_limit(client_id: str) -> bool:
    """Verifica si el cliente ha excedido el rate limit."""
    now = time.time()
    window = 3600  # 1 hora
    if client_id not in _rate_tracker:
        _rate_tracker[client_id] = []
    # Limpiar requests antiguos
    _rate_tracker[client_id] = [t for t in _rate_tracker[client_id] if now - t < window]
    if len(_rate_tracker[client_id]) >= API_RATE_LIMIT:
        return False
    _rate_tracker[client_id].append(now)
    return True


# ── JWT Utilities ─────────────────────────────────────────────


def _encode_jwt(payload: dict[str, Any], expires_in: int = 3600) -> str:
    """Codifica un JWT simple (sin librerias externas)."""
    header = json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":"))
    payload["exp"] = time.time() + expires_in
    payload["iat"] = time.time()
    encoded_header = _base64url_encode(header.encode())
    encoded_payload = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(
        JWT_SECRET.encode(), f"{encoded_header}.{encoded_payload}".encode(), hashlib.sha256
    ).digest()
    encoded_signature = _base64url_encode(signature)
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def _decode_jwt(token: str) -> dict[str, Any] | None:
    """Decodifica y verifica un JWT."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_bytes = _base64url_decode(parts[1])
        payload = json.loads(payload_bytes)
        if payload.get("exp", 0) < time.time():
            return None
        # Verificar firma
        signature = hmac.new(
            JWT_SECRET.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(_base64url_encode(signature), parts[2]):
            return None
        return payload
    except Exception:
        return None


def _base64url_encode(data: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    import base64

    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


# ── Decoradores ───────────────────────────────────────────────


def require_auth(f):
    """Requiere token JWT valido."""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any):

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Autorizacion requerida. Usa: Bearer <token>"}), 401
        token = auth_header[7:]
        payload = _decode_jwt(token)
        if not payload:
            return jsonify({"error": "Token invalido o expirado"}), 401
        request.user = payload  # type: ignore
        return f(*args, **kwargs)

    return decorated


def rate_limited(f):
    """Aplica rate limiting por client ID."""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any):

        client_id = request.headers.get("X-Client-ID", request.remote_addr or "unknown")
        if not _check_rate_limit(client_id):
            return jsonify({"error": "Rate limit excedido. Intente mas tarde."}), 429
        return f(*args, **kwargs)

    return decorated


# ── Core Integration ──────────────────────────────────────────

_core_obj: Any = None


def get_core() -> Any:
    """Lazy loader para DanielaCore."""
    global _core_obj
    if _core_obj is None:
        core_path = Path(__file__).parent / "daniela_os_core.py"
        if core_path.exists():
            try:
                import importlib.util

                spec = importlib.util.spec_from_file_location("daniela_os_core", core_path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules["daniela_os_core"] = mod
                    spec.loader.exec_module(mod)
                    _core_obj = mod.DanielaCore()
            except Exception as e:
                print(f"[GATEWAY] Error cargando core: {e}")
    return _core_obj


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS PUBLICOS
# ═══════════════════════════════════════════════════════════════


@app.route("/")
def index() -> Response:
    """Documentacion basica de la API."""
    return jsonify(
        {
            "name": "aig API Gateway",
            "version": "1.0.0",
            "status": "online",
            "endpoints": {
                "public": ["/health", "/status", "/docs"],
                "auth_required": ["/v1/ask", "/v1/modules", "/v1/pipeline"],
                "admin": ["/v1/admin/token"],
            },
            "documentation": "/docs",
        }
    )


@app.route("/health")
def health() -> Response:
    """Health check publico."""
    core = get_core()
    return jsonify(
        {
            "gateway": "healthy",
            "core": "online" if core else "offline",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/status")
def status() -> Response:
    """Estado del sistema (publico, solo metadata)."""
    core = get_core()
    if not core:
        return jsonify({"error": "Core no disponible"}), 503
    return jsonify(
        {
            "core_version": core.VERSION,
            "modules_count": len(core.registry.list_enabled()),
            "modules": [
                {"name": m.name, "description": m.description} for m in core.registry.list_enabled()
            ],
        }
    )


@app.route("/docs")
def docs() -> Response:
    """Documentacion interactiva OpenAPI-like."""
    return jsonify(
        {
            "openapi": "3.0.0",
            "info": {
                "title": "AIGestion API",
                "version": "1.0.0",
                "description": "API Gateway para la plataforma AIGestion",
            },
            "paths": {
                "/v1/ask": {
                    "post": {
                        "summary": "Consulta natural al sistema",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {"type": "string"},
                                            "context": {"type": "object"},
                                        },
                                        "required": ["query"],
                                    }
                                }
                            }
                        },
                    }
                },
                "/v1/pipeline": {
                    "post": {
                        "summary": "Ejecutar pipeline de modulos",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "steps": {"type": "array"},
                                        },
                                        "required": ["steps"],
                                    }
                                }
                            }
                        },
                    }
                },
            },
        }
    )


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS CON AUTENTICACION
# ═══════════════════════════════════════════════════════════════


@app.route("/v1/ask", methods=["POST"])
@require_auth
@rate_limited
def api_ask() -> Response:
    """Procesa una consulta natural y la enruta al modulo adecuado."""
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query requerida"}), 400

    core = get_core()
    if not core:
        return jsonify({"error": "Core no disponible"}), 503

    result = core.ask(query, **data.get("context", {}))
    return jsonify(result)


@app.route("/v1/pipeline", methods=["POST"])
@require_auth
@rate_limited
def api_pipeline() -> Response:
    """Ejecuta un pipeline de modulos."""
    data = request.get_json() or {}
    steps = data.get("steps", [])
    if not steps:
        return jsonify({"error": "Steps requeridos"}), 400

    core = get_core()
    if not core:
        return jsonify({"error": "Core no disponible"}), 503

    from daniela_os_core import PipelineStep

    pipeline_steps = [PipelineStep(**s) for s in steps]
    result = core.run_pipeline(pipeline_steps)
    return jsonify(
        {
            "success": result.success,
            "duration_ms": result.duration_ms,
            "outputs": result.outputs,
            "errors": result.errors,
            "trace": result.trace,
        }
    )


@app.route("/v1/modules")
@require_auth
def api_modules() -> Response:
    """Lista modulos disponibles."""
    core = get_core()
    if not core:
        return jsonify({"error": "Core no disponible"}), 503
    return jsonify(
        {
            "modules": [
                {
                    "name": m.name,
                    "description": m.description,
                    "intents": m.intents,
                    "enabled": m.enabled,
                }
                for m in core.registry.list_all()
            ]
        }
    )


@app.route("/v1/modules/<module_name>", methods=["POST"])
@require_auth
@rate_limited
def api_module_action(module_name: str) -> Response:
    """Ejecuta una accion en un modulo especifico."""
    data = request.get_json() or {}
    action = data.get("action", "default")

    core = get_core()
    if not core:
        return jsonify({"error": "Core no disponible"}), 503

    mod = core.registry.get(module_name)
    if not mod:
        return jsonify({"error": f"Modulo '{module_name}' no encontrado"}), 404

    try:
        result = mod.handler(action=action, **data.get("params", {}))
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════════════════════

# API Keys simples (en produccion usar base de datos)
_api_keys: dict[str, dict[str, Any]] = {
    "demo-key-001": {
        "name": "Demo Account",
        "tier": "free",
        "created": datetime.now().isoformat(),
    }
}


@app.route("/v1/admin/token", methods=["POST"])
def admin_token() -> Response:
    """Genera un token JWT desde una API key."""
    data = request.get_json() or {}
    api_key = data.get("api_key", "")

    if api_key not in _api_keys:
        return jsonify({"error": "API key invalida"}), 401

    account = _api_keys[api_key]
    token = _encode_jwt(
        {
            "sub": api_key,
            "name": account["name"],
            "tier": account["tier"],
        },
        expires_in=86400,
    )  # 24 horas

    return jsonify(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 86400,
        }
    )


# ═══════════════════════════════════════════════════════════════
# WEBHOOKS
# ═══════════════════════════════════════════════════════════════


@app.route("/webhook/<source>", methods=["POST"])
def webhook(source: str) -> Response:
    """Recibe webhooks de fuentes externas (GitHub, Stripe, etc.)."""
    data = request.get_json() or {}

    # Verificar firma si existe
    request.headers.get("X-Webhook-Signature", "")
    # En produccion: verificar HMAC

    # Procesar segun fuente
    if source == "github":
        event = request.headers.get("X-GitHub-Event", "")
        # Procesar evento GitHub
        return jsonify({"status": "ok", "source": "github", "event": event})

    if source == "stripe":
        event_type = data.get("type", "")
        # Procesar evento Stripe
        return jsonify({"status": "ok", "source": "stripe", "event": event_type})

    # Default: procesar con el core
    core = get_core()
    if core:
        result = core.ask(f"webhook from {source}: {json.dumps(data)[:200]}")
        return jsonify({"status": "processed", "result": result})

    return jsonify({"status": "received", "source": source})


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════


def main() -> int:
    parser = argparse.ArgumentParser(description="AIGestion API Gateway")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--generate-key", action="store_true", help="Generar API key demo")

    args = parser.parse_args()

    if args.generate_key:
        key = hashlib.sha256(os.urandom(32)).hexdigest()[:16]
        print(f"API Key generada: {key}")
        print(
            f'Usa: curl -X POST http://localhost:{args.port}/v1/admin/token -d \'{{"api_key":"{key}"}}\''
        )
        return 0

    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   AIGestion API Gateway v1.0                                 ║
    ║                                                              ║
    ║   URL: http://{args.host}:{args.port:<5}                             ║
    ║   Core: {"CONECTADO" if get_core() else "OFFLINE":<10}                          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
