"""Unified API Gateway - routes requests to all 19 engines with rate limiting and circuit breaker."""

import json
import threading
import time
from collections import defaultdict
from urllib.request import Request, urlopen

from flask import Flask, Response, jsonify, request

from .event_bus import get_event_bus
from .orchestrator import CrossEngineOrchestrator
from .protocols import ENGINE_PATHS, ENGINE_PORTS

app = Flask(__name__)

_event_bus = get_event_bus()
_orchestrator = CrossEngineOrchestrator()


class RateLimiter:
    """Per-engine rate limiter (100 req/min)."""

    def __init__(self, limit: int = 100, window: float = 60.0) -> None:
        self._lock = threading.Lock()
        self._limit = limit
        self._window = window
        self._requests: dict[str, list[float]] = defaultdict(list)

    def allow(self, engine: str) -> bool:
        now = time.time()
        with self._lock:
            timestamps = self._requests[engine]
            self._requests[engine] = [t for t in timestamps if now - t < self._window]
            if len(self._requests[engine]) >= self._limit:
                return False
            self._requests[engine].append(now)
            return True

    def remaining(self, engine: str) -> int:
        now = time.time()
        with self._lock:
            timestamps = self._requests[engine]
            active = [t for t in timestamps if now - t < self._window]
            return max(0, self._limit - len(active))


class CircuitBreakers:
    """Per-engine circuit breakers (open after 5 failures)."""

    def __init__(self, threshold: int = 5, reset_timeout: float = 30.0) -> None:
        self._lock = threading.Lock()
        self._failures: dict[str, int] = defaultdict(int)
        self._opened_at: dict[str, float] = {}
        self._threshold = threshold
        self._reset_timeout = reset_timeout

    def state(self, engine: str) -> str:
        with self._lock:
            opened = self._opened_at.get(engine, 0)
            if opened and time.time() - opened < self._reset_timeout:
                return "open"
            if opened and time.time() - opened >= self._reset_timeout:
                self._failures[engine] = 0
                self._opened_at.pop(engine, None)
                return "half-open"
            return "closed"

    def record_success(self, engine: str) -> None:
        with self._lock:
            self._failures[engine] = 0
            self._opened_at.pop(engine, None)

    def record_failure(self, engine: str) -> None:
        with self._lock:
            self._failures[engine] += 1
            if self._failures[engine] >= self._threshold:
                self._opened_at[engine] = time.time()

    def allow(self, engine: str) -> bool:
        return self.state(engine) != "open"


_rate_limiter = RateLimiter()
_circuit_breakers = CircuitBreakers()
_request_log: list[dict] = []


def _find_engine_for_path(path: str):
    """Match a request path to an engine name."""
    for engine_name, prefix in ENGINE_PATHS.items():
        if path.startswith(prefix):
            sub_path = path[len(prefix):] or "/"
            return engine_name, sub_path
    return None, None


def _proxy_to_engine(engine_name: str, sub_path: str, method: str, body=None):
    """Forward request to the target engine."""
    if not _circuit_breakers.allow(engine_name):
        return jsonify({"error": "circuit_breaker_open", "engine": engine_name}), 503

    if not _rate_limiter.allow(engine_name):
        return jsonify({"error": "rate_limited", "engine": engine_name, "remaining": _rate_limiter.remaining(engine_name)}), 429

    port = ENGINE_PORTS[engine_name]
    url = f"http://127.0.0.1:{port}{sub_path}"
    try:
        data_bytes = json.dumps(body).encode() if body else None
        req = Request(url, data=data_bytes, method=method)
        if body:
            req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=5) as resp:
            resp_body = resp.read().decode()
            _circuit_breakers.record_success(engine_name)
            _event_bus.publish(engine_name, "integration.webhook.received", {"path": sub_path})
            return Response(resp_body, status=resp.status, content_type="application/json")
    except Exception as e:
        _circuit_breakers.record_failure(engine_name)
        _event_bus.publish(engine_name, "service.error", {"error": str(e)})
        return jsonify({"error": str(e), "engine": engine_name}), 502


def _log_request(engine: str, path: str, method: str, status: int):
    entry = {
        "engine": engine,
        "path": path,
        "method": method,
        "status": status,
        "timestamp": time.time(),
    }
    _request_log.append(entry)
    if len(_request_log) > 1000:
        _request_log.clear()


# --- Generic engine proxy route ---
@app.route("/api/<engine_prefix>/", defaults={"subpath": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.route("/api/<engine_prefix>/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy_engine(engine_prefix, subpath):
    path = f"/api/{engine_prefix}"
    if subpath:
        path += f"/{subpath}"

    engine_name, sub_path = _find_engine_for_path(path)
    if not engine_name:
        return jsonify({"error": "unknown_engine", "path": path}), 404

    body = request.get_json(silent=True) if request.method in ("POST", "PUT", "PATCH") else None
    resp = _proxy_to_engine(engine_name, sub_path or "/", request.method, body)
    _log_request(engine_name, path, request.method, resp.status_code if hasattr(resp, "status_code") else 502)
    return resp


# --- Gateway meta routes ---
@app.route("/api/gateway/status", methods=["GET"])
def gateway_status():
    return jsonify({
        "gateway": "active",
        "engines": len(ENGINE_PORTS),
        "uptime": time.time(),
    })


@app.route("/api/gateway/engines", methods=["GET"])
def gateway_engines():
    statuses = {}
    for name, port in ENGINE_PORTS.items():
        statuses[name] = {
            "port": port,
            "path": ENGINE_PATHS[name],
            "circuit": _circuit_breakers.state(name),
            "rate_remaining": _rate_limiter.remaining(name),
        }
    return jsonify(statuses)


@app.route("/api/gateway/events", methods=["GET"])
def gateway_events():
    limit = request.args.get("limit", 50, type=int)
    events = _event_bus.get_events(limit=limit)
    return jsonify(events)


@app.route("/api/gateway/flows", methods=["GET"])
def gateway_flows():
    flows = _orchestrator.get_cross_engine_flows()
    return jsonify(flows)


@app.route("/api/gateway/logs", methods=["GET"])
def gateway_logs():
    limit = request.args.get("limit", 100, type=int)
    return jsonify(_request_log[-limit:])


def run_gateway(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Start the gateway on the given port."""
    _orchestrator.start()
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    run_gateway()
