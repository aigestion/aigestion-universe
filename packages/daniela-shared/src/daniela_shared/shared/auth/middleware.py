"""Flask middleware that enforces JWT auth on all /api/* routes.

Usage in any Flask server:
    from shared.auth.middleware import create_auth_middleware
    create_auth_middleware(app)
"""

import logging
import os

from flask import jsonify, request

logger = logging.getLogger(__name__)

# Paths that are always public (no auth required)
PUBLIC_PATHS = {
    "/", "/health", "/status", "/api/status",
    "/docs", "/metrics", "/favicon.ico",
}

# Prefixes that are always public
PUBLIC_PREFIXES = (
    "/static", "/web", "/favicon",
)

def create_auth_middleware(app, public_paths=None, public_prefixes=None):
    """Register a before_request hook that validates JWT on all /api/* routes.

    Args:
        app: Flask application instance
        public_paths: Additional paths to exempt from auth
        public_prefixes: Additional prefixes to exempt from auth
    """
    from shared.auth import create_jwt_handler

    jwt_handler = create_jwt_handler()
    exempt = PUBLIC_PATHS | (public_paths or set())
    prefixes = PUBLIC_PREFIXES + tuple(public_prefixes or ())

    # Check if this is an internal service call (Docker network)
    internal_ips = {"127.0.0.1", "::1", "localhost"}

    @app.before_request
    def _require_jwt():
        path = request.path

        # Skip public paths
        if path in exempt:
            return None

        # Skip public prefixes
        if any(path.startswith(p) for p in prefixes):
            return None

        # Skip non-API paths (HTML dashboards, etc.)
        if not path.startswith("/api/") and not path.startswith("/v1/"):
            return None

        # Skip internal service calls (Docker health checks, inter-service)
        remote_ip = request.remote_addr or ""
        if remote_ip in internal_ips:
            return None

        # Check for service-to-service token
        service_token = request.headers.get("X-Service-Token", "")
        if service_token:
            expected = os.getenv("SERVICE_TOKEN", "")
            if expected and service_token == expected:
                return None

        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization required. Send Authorization: Bearer <JWT>"}), 401

        token = auth_header[7:]
        payload = jwt_handler.decode(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Attach user to request context
        request.user = payload
        return None
