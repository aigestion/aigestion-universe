#!/usr/bin/env python3
"""
aig API Gateway v1.0
===========================
Gateway publico que expone endpoints REST para consumo externo.
Features:
- Autenticacion JWT
- Rate limiting
- Routing a modulos del core
- Webhooks
- Documentacion OpenAPI (Swagger)

Autor: aig Team
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import logging
import os
import sys
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

from flask import Flask, Response, g, jsonify, render_template, request
from sqlalchemy import MetaData, create_engine, text

# Optional Prometheus metrics – provide fallbacks if library unavailable
try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
except ImportError:
    class _DummyMetric:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
    Counter = Histogram = _DummyMetric
    def generate_latest():
        return b""
    CONTENT_TYPE_LATEST = "text/plain"
try:
    from flasgger import Swagger, swag_from
except ImportError:
    class _DummySwagger:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return self
    Swagger = _DummySwagger
    def swag_from(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
from flask_cors import CORS

# ── Configuracion ─────────────────────────────────────────────
swagger_template = {
    "info": {"title": "aig API", "version": "1.0.0"},
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
        }
    },
    "security": [{"Bearer": []}]
}


app = Flask(__name__)
CORS(app, origins=["http://localhost:9200", "http://localhost:9300", "http://localhost:9400", "http://localhost:9500"])
# Initialize Swagger with template for JWT auth
swagger = Swagger(app, template=swagger_template)


# Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('api_request_latency_seconds', 'Latency per request', ['endpoint'])


# Configure logger
logger = logging.getLogger('gateway')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    try:
        from pythonjsonlogger import jsonlogger
        formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(module)s %(message)s')
    except ImportError:
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Timing and metrics hooks
@app.before_request
def start_timer():
    g.start_time = time.time()
    logger.info(f"{request.remote_addr} -> {request.method} {request.path}")

@app.after_request
def record_metrics(response):
    # Calculate latency
    latency = time.time() - g.get('start_time', time.time())
    endpoint = request.path
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)
    REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, http_status=response.status_code).inc()
    logger.info(f"Response {response.status_code} for {request.method} {request.path} (latency: {latency:.4f}s)")
    return response

app.config['JSON_SORT_KEYS'] = False

# ── Auth helper endpoints ────────────────────────────────────────


@swag_from
@app.route("/v1/token/refresh", methods=["POST"])
def refresh_token() -> Response:
    """yaml
    post:
      summary: Refresh an existing JWT token
      description: Takes a valid JWT in the Authorization header and returns a new token with refreshed expiry.
      parameters:
        - in: header
          name: Authorization
          required: true
          schema:
            type: string
            example: Bearer <token>
      responses:
        200:
          description: New JWT token
          schema:
            type: object
            properties:
              token:
                type: string
        401:
          description: Invalid or missing token
    ---
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authorization header missing or malformed"}), 401
    old_token = auth_header[7:]
    payload = _decode_jwt(old_token)
    if not payload:
        return jsonify({"error": "Invalid or expired token"}), 401
    # Remove old iat/exp and issue a fresh token
    new_payload = {k: v for k, v in payload.items() if k not in ("iat", "exp")}
    new_token = _encode_jwt(new_payload)
    return jsonify({"token": new_token})


# Duplicate config removed; JSON_SORT_KEYS already set above

# ------------------------------------------------------------------
# Database engine (PostgreSQL) – shared across tenants
# ------------------------------------------------------------------
POSTGRES_URL = os.getenv("AIGESTION_POSTGRES_URL") or "sqlite:///aig.db"
engine = create_engine(POSTGRES_URL, future=True)
metadata = MetaData()
# Removed redundant engine creation; using the future-enabled engine above.

JWT_SECRET = os.getenv("AIGESTION_JWT_SECRET") or os.getenv("JWT_SECRET")
if not JWT_SECRET or JWT_SECRET in {"change-me-in-production", "aigestion-super-secret-key-change-in-production", "aig-super-secret-key-change-in-production"}:
    raise RuntimeError("AIGESTION_JWT_SECRET/JWT_SECRET no definido (o es el default inseguro): define un secreto de alto entropo.")
API_RATE_LIMIT = int(os.getenv("AIGESTION_RATE_LIMIT", "100"))  # requests per hour

# ------------------------------------------------------------------
# Rate limiting persisted in SQLite
# ------------------------------------------------------------------
from datetime import timedelta

from sqlalchemy import Column, DateTime, String, Table

# Table to store request timestamps per client
rate_limits_table = Table(
    "rate_limits",
    metadata,
    Column("client_id", String, primary_key=False),
    Column("timestamp", DateTime, nullable=False),
)

# Ensure table exists
with engine.begin() as conn:
    metadata.create_all(bind=conn)

def _check_rate_limit(client_id: str) -> bool:
    """Check and record request for a client using a 1‑hour window.
    Returns ``True`` if the request is allowed, ``False`` otherwise.
    """
    now = datetime.utcnow()
    window_start = now - timedelta(hours=1)
    with engine.begin() as conn:
        # Remove stale entries
        conn.execute(rate_limits_table.delete().where(rate_limits_table.c.timestamp < window_start))
        # Count recent requests for this client
        recent = conn.execute(
            rate_limits_table.select().where(
                (rate_limits_table.c.client_id == client_id) &
                (rate_limits_table.c.timestamp >= window_start)
            )
        ).fetchall()
        if len(recent) >= API_RATE_LIMIT:
            return False
        # Record this request
        conn.execute(rate_limits_table.insert().values(client_id=client_id, timestamp=now))
    return True

# ------------------------------------------------------------------
# Multitenancy helpers (schemas per client)
# ------------------------------------------------------------------

def _tenant_schema_name(tenant_id: str) -> str:
    """Normaliza el ID del cliente a un nombre de schema PostgreSQL.
    Se prefixa con `t_` y se convierten espacios a guiones bajos.
    Solo se permiten caracteres alfanuméricos y guiones bajos.
    """
    import re
    clean = re.sub(r'[^a-z0-9_]', '_', tenant_id.lower().replace(" ", "_"))
    clean = re.sub(r'_+', '_', clean).strip('_')
    return f"t_{clean[:63]}"  # PostgreSQL schema name limit

def create_tenant_schema(tenant_id: str) -> None:
    """Crea (si no existe) el schema aislado para el cliente.
    Esta función se llama al registrar un nuevo cliente o al crear
    un sub‑universo. Utiliza la conexión global `engine` para ejecutar
    el comando SQL directamente.
    """
    schema = _tenant_schema_name(tenant_id)
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

# Flask hook to set tenant schema per request
@app.before_request
def before_request_func():
    # 2026-10-04 (S7): el tenant se deriva del JWT (`sub`) cuando hay auth.
    # Antes venia de la cabecera X-Client-ID (controlada por el cliente), lo
    # que permitia apuntar el schema al de otro tenant y leer sus datos.
    tenant_id = ""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        payload = _decode_jwt(auth_header[7:])
        if payload:
            tenant_id = str(payload.get("sub") or payload.get("client_id") or "")
    if not tenant_id:
        tenant_id = request.headers.get("X-Client-ID", request.remote_addr or "unknown")
    g.tenant_id = tenant_id
    # Only apply schema isolation for PostgreSQL backends.
    if engine.dialect.name == "postgresql":
        try:
            # Ensure schema exists.
            create_tenant_schema(tenant_id)
            # Set search_path for this request.
            schema = _tenant_schema_name(tenant_id)
            with engine.begin() as conn:
                conn.execute(text(f"SET search_path TO {schema}, public"))
        except Exception as e:
            print(f"[GATEWAY] Failed to set tenant schema for {tenant_id}: {e}")
    else:
        # SQLite fallback – no schema isolation.
        pass


# Deprecated in‑memory rate limiting removed; persisted SQLite version defined earlier.


# ── JWT Utilities ─────────────────────────────────────────────

def _encode_jwt(payload: dict[str, Any], expires_in: int = 3600) -> str:
    """Codifica un JWT simple (sin librerias externas)."""
    header = json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":"))
    payload["exp"] = time.time() + expires_in
    payload["iat"] = time.time()
    encoded_header = _base64url_encode(header.encode())
    encoded_payload = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(
        JWT_SECRET.encode(),
        f"{encoded_header}.{encoded_payload}".encode(),
        hashlib.sha256
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
            JWT_SECRET.encode(),
            f"{parts[0]}.{parts[1]}".encode(),
            hashlib.sha256
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
    """Lazy loader para DanielaCore con tenant awareness.
    Al cargar el core se asegura que la sesión SQL tenga el
    `search_path` correcto del cliente actual.
    """
    global _core_obj
    if _core_obj is None:
        # El core se aploanó: vive en `core/daniela_os_core.py` (y antes tambien se
        # probaba en la raiz). Se buscan desde la RAIZ del repo: este fichero
        # vive en `api/`, asi que antes se miraba `api/core/aig_core.py`, una
        # ruta que no existe en ningun checkout -> el loader nunca encontraba
        # nada y el core quedaba offline en silencio.
        raiz = Path(__file__).resolve().parents[1]
        core_path = next(
            (
                p
                for p in (raiz / "core" / "daniela_os_core.py",
                          raiz / "daniela_os_core.py")
                if p.exists()
            ),
            raiz / "core" / "daniela_os_core.py",
        )
        if core_path.exists():
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("core.daniela_os_core", core_path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules["core.daniela_os_core"] = mod
                    spec.loader.exec_module(mod)
                    _core_obj = mod.DanielaCore()
            except Exception as e:
                print(f"[GATEWAY] Error cargando core: {e}")
    return _core_obj

# ------------------------------------------------------------------
# Dependency: DB session with tenant schema set
# ------------------------------------------------------------------
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    """FastAPI‑style dependency that yields a SQLAlchemy session scoped to the tenant.
    The `before_request` hook already set the search_path, so any query will hit
    the correct schema.
    """
    conn = engine.connect()
    try:
        # 2026-10-04 (S7): aplicar el search_path en ESTA conexion. Antes se
        # asumia que before_request lo habia aplicado en otra (cerrada), asi
        # que el aislamiento por tenant NO funcionaba en estas sesiones.
        tenant_id = getattr(g, "tenant_id", "")
        if tenant_id and engine.dialect.name == "postgresql":
            schema = _tenant_schema_name(tenant_id)
            conn.execute(text(f"SET search_path TO {schema}, public"))
        db = SessionLocal(bind=conn)
        yield db
    finally:
        db.close()
        conn.close()


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS PUBLICOS
# ═══════════════════════════════════════════════════════════════

@swag_from({
    "summary": "Root endpoint providing basic API information",
    "responses": {"200": {"description": "API metadata"}}
})
@app.route("/")
def index() -> Response:
    """Documentacion basica de la API."""
    return jsonify({
        "name": "aig API Gateway",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "public": ["/health", "/status", "/docs"],
            "auth_required": ["/v1/ask", "/v1/modules", "/v1/pipeline"],
            "admin": ["/v1/admin/token"],
        },
        "documentation": "/docs",
    })


@app.route("/health")
def health() -> Response:
    """Health check publico.

    Devuelve el agregado de subsistemas (disco, memoria, scheduler, config)
    ademas del estado del gateway y del core.

    Compatibilidad: las claves `gateway` y `core` se mantienen tal cual porque
    los tests y los consumidores existentes dependen de ellas. El detalle vive
    bajo `checks`, y `status` resume el peor estado para un load balancer.

    Si el modulo de chequeos no esta disponible, se degrada al comportamiento
    anterior en vez de fallar: un health check roto es peor que uno basico.
    """
    core = get_core()
    payload: dict[str, Any] = {
        "gateway": "healthy",
        "core": "online" if core else "offline",
        "timestamp": datetime.now().isoformat(),
    }

    try:
        from health_checks import run_all_checks
        detalle = run_all_checks()
        payload["status"] = detalle["status"]
        payload["checks"] = detalle["checks"]
    except Exception as exc:  # noqa: BLE001 — nunca tumbar /health
        payload["status"] = "unknown"
        payload["checks_error"] = f"{type(exc).__name__}: {exc}"

    return jsonify(payload)


@app.route("/health/ready")
def health_ready() -> Response:
    """Readiness probe: 200 si el sistema puede atender, 503 si no.

    La distincion entre `/health` (liveness) y `/health/ready` (readiness) es
    intencionada y es la convencion de Kubernetes:

      * liveness  -> "el proceso esta vivo". Reiniciar no ayudaria si algo
                     interno falla, asi que devuelve 200 aunque haya degradacion.
      * readiness -> "puedo atender trafico". Si un subsistema critico esta
                     caido, el balanceador debe dejar de enviarme peticiones.

    `/health` siempre responde 200 (para no provocar reinicios en cascada);
    `/health/ready` responde 503 cuando algo va mal de verdad.
    """
    try:
        from health_checks import run_all_checks
        detalle = run_all_checks()
        estado = detalle["status"]
        codigo = 503 if estado == "unhealthy" else 200
        return jsonify({"ready": estado != "unhealthy", **detalle}), codigo
    except Exception as exc:  # noqa: BLE001
        # No poder comprobar la readiness es motivo para no recibir trafico.
        return jsonify({"ready": False, "error": str(exc)}), 503


@app.route("/status")
def status() -> Response:
    """Estado del sistema (publico, solo metadata)."""
    core = get_core()
    if not core:
        return jsonify({"error": "Core no disponible"}), 503
    return jsonify({
        "core_version": core.VERSION,
        "modules_count": len(core.registry.list_enabled()),
        "modules": [
            {"name": m.name, "description": m.description}
            for m in core.registry.list_enabled()
        ],
    })


@app.route("/docs")
def docs() -> Response:
    """Documentacion interactiva OpenAPI-like."""
    return jsonify({
        "openapi": "3.0.0",
        "info": {
            "title": "aig API",
            "version": "1.0.0",
            "description": "API Gateway para la plataforma aig",
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
    })


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS CON AUTENTICACION

@app.route('/metrics')
def metrics() -> Response:
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route("/api/status")
def api_status() -> Response:
    """Simple health check used by Docker healthcheck."""
    return jsonify({"status": "ok"})
# ═══════════════════════════════════════════════════════════════

@app.route("/v1/ask", methods=["POST"])
@require_auth
@rate_limited
@swag_from({
    "summary": "Procesa una consulta natural",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "context": {"type": "object"}
                },
                "required": ["query"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Resultado del core.ask"},
        "400": {"description": "Falta query"},
        "503": {"description": "Core no disponible"}
    }
})
def api_ask() -> Response:
    """
---
post:
  summary: Procesa una consulta natural
  description: Receives a JSON payload with `query` and optional `context`, routes to core.ask.
  parameters:
    - in: body
      name: body
      required: true
      schema:
        type: object
        properties:
          query:
            type: string
            description: Texto de la consulta.
          context:
            type: object
            description: Contexto adicional para el core.
        required:
          - query
  responses:
    200:
      description: Resultado del core.ask
      schema:
        type: object
    400:
      description: Falta query
    503:
      description: Core no disponible
---
"""
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
@swag_from({
    "summary": "Ejecuta un pipeline de módulos",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "module": {"type": "string"},
                                "action": {"type": "string"},
                                "params": {"type": "object"},
                                "condition": {"type": "string"}
                            },
                            "required": ["name"]
                        }
                    }
                },
                "required": ["steps"]
            }
        }
    ],
    "responses": {
        "200": {"description": "Pipeline ejecutado exitosamente"},
        "400": {"description": "Steps requeridos"},
        "503": {"description": "Core no disponible"}
    }
})
def api_pipeline() -> Response:
    """Ejecuta un pipeline de modulos."""
    data = request.get_json() or {}
    steps = data.get("steps", [])
    if not steps:
        return jsonify({"error": "Steps requeridos"}), 400

    core = get_core()
    if not core:
        return jsonify({"error": "Core no disponible"}), 503

    # Normalize step dicts: accept 'name' as module name and set defaults
    normalized_steps = []
    for s in steps:
        module = s.get('name') or s.get('module')
        if not module:
            continue  # skip invalid step
        action = s.get('action', 'run')
        params = s.get('params', {})
        condition = s.get('condition')
        normalized_steps.append({
            'module': module,
            'action': action,
            'params': params,
            'condition': condition,
        })
    from core.daniela_os_core import PipelineStep
    pipeline_steps = [PipelineStep(**s) for s in normalized_steps]
    result = core.run_pipeline(pipeline_steps)
    return jsonify({
        "success": result.success,
        "duration_ms": result.duration_ms,
        "outputs": result.outputs,
        "errors": result.errors,
        "trace": result.trace,
    })


@app.route("/v1/modules")
@require_auth
@swag_from({
    "summary": "Lista modulos disponibles.",
    "responses": {
        "200": {"description": "Listado de modulos"},
        "503": {"description": "Core no disponible"}
    }
})
def api_modules() -> Response:
    """Lista modulos disponibles."""
    core = get_core()
    if not core:
        return jsonify({"error": "Core no disponible"}), 503
    return jsonify({
        "modules": [
            {
                "name": m.name,
                "description": m.description,
                "intents": m.intents,
                "enabled": m.enabled,
            }
            for m in core.registry.list_all()
        ]
    })

# ------------------------------------------------------------------
# Universe (sub‑schema) management endpoints
# ------------------------------------------------------------------

@swag_from({
    "summary": "Create a new universe (sub-schema)",
    "responses": {
        "201": {"description": "Universe created"},
        "400": {"description": "Universe name required"},
        "500": {"description": "Server error"}
    }
})
@app.route("/v1/universes", methods=["POST"])
@require_auth
@rate_limited
def create_universe() -> Response:
    """Crea un sub‑universo (schema) aislado para el cliente autenticado.
    El nombre del universo se recibe en el cuerpo JSON bajo la clave
    `name`. El schema resultante será `t_<clientId>_<universe>`.
    """
    data = request.get_json() or {}
    uni_name = data.get("name")
    if not uni_name:
        return jsonify({"error": "Universe name required"}), 400
    client_id = request.headers.get("X-Client-ID", request.remote_addr or "unknown")
    import re
    safe_uni = re.sub(r'[^a-z0-9_]', '_', uni_name.lower().replace(" ", "_"))
    safe_uni = re.sub(r'_+', '_', safe_uni).strip('_')
    schema = f"{_tenant_schema_name(client_id)}_{safe_uni[:63]}"
    try:
        with engine.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        return jsonify({"universe": uni_name, "schema": schema, "status": "created"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@swag_from({
    "summary": "List universes for the authenticated client",
    "responses": {
        "200": {"description": "List of universes"},
        "500": {"description": "Server error"}
    }
})
@app.route("/v1/universes", methods=["GET"])
@require_auth
@rate_limited
def list_universes() -> Response:
    """Lista los sub‑universos (schemas) asociados al cliente.
    Se buscan todos los schemas que inicien con el prefijo del cliente.
    """
    client_id = request.headers.get("X-Client-ID", request.remote_addr or "unknown")
    prefix = _tenant_schema_name(client_id) + "_"
    with engine.begin() as conn:
        rows = conn.execute(text(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE :pref"
        ), {"pref": f"{prefix}%"}).fetchall()
    universes = [r[0].replace(prefix, "") for r in rows]
    return jsonify({"universes": universes})


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
# DOCKER MARKETPLACE
# ═══════════════════════════════════════════════════════════════

try:
    from docker_marketplace import register_docker_routes
    register_docker_routes(app)
except Exception as e:  # noqa: BLE001
    print(f"[Docker Marketplace] Not available: {e}")

try:
    from universe_deploy import register_universe_routes
    register_universe_routes(app)
except Exception as e:  # noqa: BLE001
    print(f"[Universe Deploy] Not available: {e}")

# ═══════════════════════════════════════════════════════════════
# DANIELA ECOSYSTEM
# ═══════════════════════════════════════════════════════════════

try:
    from personas_system import register_persona_routes
    register_persona_routes(app)
except Exception as e:  # noqa: BLE001
    print(f"[Personas System] Not available: {e}")

try:
    from agent_marketplace import register_agent_routes
    register_agent_routes(app)
except Exception as e:  # noqa: BLE001
    print(f"[Agent Marketplace] Not available: {e}")

try:
    from predictive_engine import register_predictive_routes
    register_predictive_routes(app)
except Exception as e:  # noqa: BLE001
    print(f"[Predictive Engine] Not available: {e}")

try:
    from plugin_store import register_plugin_routes
    register_plugin_routes(app)
except Exception as e:  # noqa: BLE001
    print(f"[Plugin Store] Not available: {e}")

try:
    from self_healing import register_healing_routes
    register_healing_routes(app)
except Exception as e:  # noqa: BLE001
    print(f"[Self-Healing] Not available: {e}")

try:
    from daniela_ecosystem import (
        register_dna_routes,
        register_economy_routes,
        register_gamification_routes,
    )
    register_economy_routes(app)
    register_gamification_routes(app)
    register_dna_routes(app)
except Exception as e:  # noqa: BLE001
    print(f"[Ecosystem] Not available: {e}")


# ═══════════════════════════════════════════════════════════════
# EPIC RUN ENDPOINT
# ═══════════════════════════════════════════════════════════════

@app.route("/v1/initiative-run", methods=["POST"])
@require_auth
@rate_limited
def epic_run() -> Response:
    """Ejecuta un pipeline épico predefinido.
    Ideal para pruebas automatizadas o demo rápida.
    """
    # reutilizamos el core si está disponible
    core = get_core()
    if not core:
        return jsonify({"error": "Core no disponible"}), 503
    # Definir pasos épicos (audit → content → notify)
    steps = [
        {"name": "audit", "params": {}},
        {"name": "content_factory", "params": {"type": "viral", "language": "es"}},
        {"name": "notify", "params": {"channel": "telegram", "target": "@grupo"}},
    ]
    # Reusar la lógica de pipeline del endpoint existente
    from core.daniela_os_core import PipelineStep
    pipeline_steps = [PipelineStep(**s) for s in steps]
    result = core.run_pipeline(pipeline_steps)
    return jsonify(result)



# ═══════════════════════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════════════════════

# API Keys simples (en produccion usar base de datos)
# API Keys persisted in PostgreSQL (table: api_keys).
# The table is created at startup if it does not exist.
from sqlalchemy import Column, DateTime, MetaData, String, Table

metadata = MetaData()
api_keys_table = Table(
    "api_keys",
    metadata,
    Column("key", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("tier", String, nullable=False),
    Column("created", DateTime, nullable=False),
)

# Ensure the table exists.
with engine.begin() as conn:
    metadata.create_all(bind=conn)

def _db_get_api_key(key: str):
    """Fetch API key record from DB, returns dict or None."""
    with engine.begin() as conn:
        result = conn.execute(api_keys_table.select().where(api_keys_table.c.key == key))
        row = result.fetchone()
        if row:
            return {"name": row["name"], "tier": row["tier"], "created": row["created"].isoformat()}
    return None

def _db_create_api_key(name: str, tier: str = "free") -> str:
    """Generate a new API key, store it, and return the key string."""
    import secrets

    # 2026-10-04 (S13): antes `sha256(urandom)[:16]` = 64 bits de entropia
    # (fuerza bruta viable). token_urlsafe(32) = 256 bits.
    key = secrets.token_urlsafe(32)
    now = datetime.now()
    with engine.begin() as conn:
        conn.execute(
            api_keys_table.insert().values(key=key, name=name, tier=tier, created=now)
        )
    return key
@app.route("/v1/admin/token", methods=["POST"])
def admin_token() -> Response:
    """Genera un token JWT desde una API key."""
    data = request.get_json() or {}
    api_key = data.get("api_key", "")

    account = _db_get_api_key(api_key)
    if not account:
        return jsonify({"error": "API key invalida"}), 401

    token = _encode_jwt({
        "sub": api_key,
        "name": account["name"],
        "tier": account["tier"],
    }, expires_in=86400)  # 24 horas

    return jsonify({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 86400,
    })


# ═══════════════════════════════════════════════════════════════
# WEBHOOKS
# ═══════════════════════════════════════════════════════════════

@app.route("/webhook/<source>", methods=["POST"])
def webhook(source: str) -> Response:
    """Recibe webhooks de fuentes externas (GitHub, Stripe, etc.)."""
    # 2026-10-04 (S8): antes era PUBLICO (sin auth) y la rama por defecto
    # hacia `core.ask(f"webhook from {source}: {json.dumps(data)[:200]}")`
    # con datos crudos externos -> prompt injection sin autenticacion.
    # Ahora: exige firma HMAC-SHA256 (env WEBHOOK_SECRET) y NO pasa el body
    # crudo al core.
    secret = os.getenv("WEBHOOK_SECRET", "")
    if not secret:
        return jsonify({"error": "webhooks no configurados (define WEBHOOK_SECRET)"}), 503
    body = request.get_data()
    signature = request.headers.get("X-Webhook-Signature", "")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return jsonify({"error": "firma invalida"}), 401

    data = request.get_json(silent=True) or {}

    # Procesar segun fuente
    if source == "github":
        event = request.headers.get("X-GitHub-Event", "")
        # Procesar evento GitHub
        return jsonify({"status": "ok", "source": "github", "event": event})

    if source == "stripe":
        event_type = data.get("type", "")
        # Procesar evento Stripe
        return jsonify({"status": "ok", "source": "stripe", "event": event_type})

    return jsonify({"status": "received", "source": source})


# ── Additional Endpoints ───────────────────────────────────────

@app.route("/v1/token/refresh", methods=["POST"])
@require_auth
def token_refresh() -> Response:
    """Refresh JWT token extending its expiration (24h)."""
    payload = getattr(request, "user", {})
    new_token = _encode_jwt({
        "sub": payload.get("sub"),
        "name": payload.get("name"),
        "tier": payload.get("tier")
    }, expires_in=86400)
    return jsonify({"access_token": new_token, "token_type": "Bearer", "expires_in": 86400})

@app.route("/v1/tenant/info")
@require_auth
def tenant_info() -> Response:
    """Return current tenant schema and its tables."""
    client_id = request.headers.get("X-Client-ID", request.remote_addr or "unknown")
    schema = _tenant_schema_name(client_id)
    from sqlalchemy import inspect
    inspector = inspect(engine)
    try:
        tables = inspector.get_table_names(schema=schema)
    except Exception:
        tables = []
    return jsonify({"tenant": client_id, "schema": schema, "tables": tables})

@app.after_request
def after_request(response):
    logger = logging.getLogger("aigateway")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.info("%s %s %s %s", request.remote_addr, request.method, request.full_path, response.status_code)
    return response

# ═══════════════════════════════════════════════════════════════
# DOCKER MARKETPLACE UI
# ═══════════════════════════════════════════════════════════════

@app.route("/docker-marketplace")
def docker_marketplace_ui():
    return render_template("docker_marketplace.html")


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(description="aig API Gateway")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--generate-key", action="store_true", help="Generar API key demo")

    args = parser.parse_args()

    if args.generate_key:
        key = hashlib.sha256(os.urandom(32)).hexdigest()[:16]
        print(f"API Key generada: {key}")
        print(f"Usa: curl -X POST http://localhost:{args.port}/v1/admin/token -d '{{\"api_key\":\"{key}\"}}'")
        return 0

    print(f"aig API Gateway v1.0 | URL: http://{args.host}:{args.port} | Core: {'CONECTADO' if get_core() else 'OFFLINE'}")

    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    sys.exit(main())


