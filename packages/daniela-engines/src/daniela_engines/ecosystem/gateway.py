"""API Gateway - 10 ideas: Rate limiting, request/response transformation, API key management, routing, load balancing, circuit breaker, validation, caching, CORS, analytics."""

import hashlib
import json
import logging
import threading
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class GatewayStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class GatewayRequest:
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None
    query_params: dict[str, str] = field(default_factory=dict)
    client_ip: str = ""
    api_key: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class GatewayResponse:
    status_code: int
    body: Any
    headers: dict[str, str] = field(default_factory=dict)
    latency_ms: float = 0.0
    cached: bool = False


@dataclass
class Route:
    path: str
    target: str
    methods: list[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    strip_prefix: bool = False
    headers: dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retries: int = 3


class RateLimiter:
    """41. Rate limiting (token bucket)"""

    def __init__(self, default_rate: int = 100, default_period: int = 60):
        self.default_rate = default_rate
        self.default_period = default_period
        self.buckets: dict[str, dict[str, Any]] = {}
        self.custom_limits: dict[str, tuple[int, int]] = {}
        self._lock = threading.Lock()

    def set_limit(self, identifier: str, rate: int, period: int = 60):
        self.custom_limits[identifier] = (rate, period)

    def remove_limit(self, identifier: str):
        self.custom_limits.pop(identifier, None)
        self.buckets.pop(identifier, None)

    def _get_bucket(self, identifier: str) -> dict[str, Any]:
        if identifier not in self.buckets:
            rate, period = self.custom_limits.get(identifier, (self.default_rate, self.default_period))
            self.buckets[identifier] = {
                "tokens": rate,
                "max_tokens": rate,
                "refill_rate": rate / period,
                "last_refill": time.time(),
                "period": period
            }
        return self.buckets[identifier]

    def _refill(self, bucket: dict[str, Any]):
        now = time.time()
        elapsed = now - bucket["last_refill"]
        tokens_to_add = elapsed * bucket["refill_rate"]
        bucket["tokens"] = min(bucket["max_tokens"], bucket["tokens"] + tokens_to_add)
        bucket["last_refill"] = now

    def allow(self, identifier: str, tokens: int = 1) -> tuple[bool, dict[str, Any]]:
        with self._lock:
            bucket = self._get_bucket(identifier)
            self._refill(bucket)

            info = {
                "limit": bucket["max_tokens"],
                "remaining": max(0, int(bucket["tokens"])),
                "reset": int(bucket["last_refill"] + bucket["period"]),
                "retry_after": 0
            }

            if bucket["tokens"] >= tokens:
                bucket["tokens"] -= tokens
                info["remaining"] = int(bucket["tokens"])
                return True, info
            else:
                wait_time = (tokens - bucket["tokens"]) / bucket["refill_rate"]
                info["retry_after"] = int(wait_time) + 1
                return False, info

    def get_status(self, identifier: str) -> dict[str, Any]:
        with self._lock:
            bucket = self._get_bucket(identifier)
            self._refill(bucket)
            return {
                "limit": bucket["max_tokens"],
                "remaining": int(bucket["tokens"]),
                "reset": int(bucket["last_refill"] + bucket["period"])
            }


class RequestTransformer:
    """42. Request/response transformation"""

    def __init__(self):
        self.request_transforms: list[Callable] = []
        self.response_transforms: list[Callable] = []
        self.header_transforms: dict[str, Callable] = {}

    def add_request_transform(self, transform: Callable):
        self.request_transforms.append(transform)

    def add_response_transform(self, transform: Callable):
        self.response_transforms.append(transform)

    def add_header_transform(self, header_name: str, transform: Callable):
        self.header_transforms[header_name] = transform

    def transform_request(self, request: GatewayRequest) -> GatewayRequest:
        for transform in self.request_transforms:
            try:
                request = transform(request)
            except Exception as e:
                logger.error(f"Request transform error: {e}")
        return request

    def transform_response(self, response: GatewayResponse) -> GatewayResponse:
        for transform in self.response_transforms:
            try:
                response = transform(response)
            except Exception as e:
                logger.error(f"Response transform error: {e}")
        return response

    def add_auth_header(self, request: GatewayRequest, token: str,
                        scheme: str = "Bearer") -> GatewayRequest:
        request.headers["Authorization"] = f"{scheme} {token}"
        return request

    def add_request_id(self, request: GatewayRequest) -> GatewayRequest:
        request.headers["X-Request-ID"] = str(uuid.uuid4())
        return request

    def add_timestamp(self, request: GatewayRequest) -> GatewayRequest:
        request.headers["X-Timestamp"] = datetime.utcnow().isoformat()
        return request

    def map_fields(self, data: dict[str, Any], field_map: dict[str, str]) -> dict[str, Any]:
        result = {}
        for old_key, new_key in field_map.items():
            if old_key in data:
                result[new_key] = data[old_key]
        return result

    def add_prefix_to_keys(self, data: dict[str, Any], prefix: str) -> dict[str, Any]:
        return {f"{prefix}{k}": v for k, v in data.items()}

    def remove_fields(self, data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
        return {k: v for k, v in data.items() if k not in fields}


class APIKeyManager:
    """43. API key management"""

    def __init__(self):
        self.keys: dict[str, dict[str, Any]] = {}
        self.key_permissions: dict[str, list[str]] = {}
        self._revoked: set = set()

    def generate_key(self, name: str, owner: str, scopes: list[str] | None = None,
                     expires_days: int = 365) -> str:
        key = f"ak_{uuid.uuid4().hex}"
        self.keys[key] = {
            "name": name,
            "owner": owner,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=expires_days)).isoformat(),
            "active": True,
            "last_used": None,
            "usage_count": 0
        }
        self.key_permissions[key] = scopes or ["read"]
        return key

    def validate_key(self, key: str) -> tuple[bool, dict[str, Any]]:
        if key in self._revoked:
            return False, {"error": "Key revoked"}
        if key not in self.keys:
            return False, {"error": "Key not found"}
        key_info = self.keys[key]
        if not key_info["active"]:
            return False, {"error": "Key inactive"}
        expires = datetime.fromisoformat(key_info["expires_at"])
        if datetime.utcnow() > expires:
            return False, {"error": "Key expired"}
        key_info["last_used"] = datetime.utcnow().isoformat()
        key_info["usage_count"] += 1
        return True, {"permissions": self.key_permissions.get(key, [])}

    def revoke_key(self, key: str) -> bool:
        if key in self.keys:
            self.keys[key]["active"] = False
            self._revoked.add(key)
            logger.info(f"Revoked API key: {key[:8]}...")
            return True
        return False

    def rotate_key(self, old_key: str) -> str | None:
        if old_key not in self.keys:
            return None
        old_info = self.keys[old_key]
        new_key = self.generate_key(
            name=f"{old_info['name']}_rotated",
            owner=old_info["owner"],
            scopes=self.key_permissions.get(old_key, [])
        )
        self.revoke_key(old_key)
        return new_key

    def get_key_info(self, key: str) -> dict[str, Any] | None:
        info = self.keys.get(key)
        if info:
            return {**info, "permissions": self.key_permissions.get(key, [])}
        return None

    def list_keys(self, owner: str | None = None) -> list[dict[str, Any]]:
        keys = []
        for key, info in self.keys.items():
            if owner and info["owner"] != owner:
                continue
            keys.append({
                "key_preview": f"{key[:8]}...",
                "name": info["name"],
                "owner": info["owner"],
                "active": info["active"],
                "created_at": info["created_at"],
                "usage_count": info["usage_count"]
            })
        return keys


class RequestRouter:
    """44. Request routing"""

    def __init__(self):
        self.routes: list[Route] = []
        self._compiled_routes: dict[str, Route] = {}
        self.middleware: list[Callable] = []
        self.fallback_target: str | None = None

    def add_route(self, route: Route):
        self.routes.append(route)
        pattern = self._normalize_path(route.path)
        self._compiled_routes[pattern] = route

    def remove_route(self, path: str):
        pattern = self._normalize_path(path)
        self.routes = [r for r in self.routes if self._normalize_path(r.path) != pattern]
        self._compiled_routes.pop(pattern, None)

    def add_middleware(self, middleware: Callable):
        self.middleware.append(middleware)

    def set_fallback(self, target: str):
        self.fallback_target = target

    def _normalize_path(self, path: str) -> str:
        return "/" + path.strip("/")

    def _match_route(self, path: str) -> tuple[Route, dict[str, str]] | None:
        normalized = self._normalize_path(path)
        if normalized in self._compiled_routes:
            return self._compiled_routes[normalized], {}

        for route in self.routes:
            route_pattern = self._normalize_path(route.path)
            if route_pattern.endswith("/*"):
                prefix = route_pattern[:-2]
                if normalized.startswith(prefix):
                    return route, {"_remainder": normalized[len(prefix):]}
            params = self._extract_params(route_pattern, normalized)
            if params is not None:
                return route, params

        return None

    def _extract_params(self, pattern: str, path: str) -> dict[str, str] | None:
        pattern_parts = pattern.strip("/").split("/")
        path_parts = path.strip("/").split("/")
        if len(pattern_parts) != len(path_parts):
            return None
        params = {}
        for pp, rp in zip(pattern_parts, path_parts):
            if pp.startswith("{") and pp.endswith("}"):
                params[pp[1:-1]] = rp
            elif pp != rp:
                return None
        return params

    def resolve(self, request: GatewayRequest) -> tuple[str, dict[str, Any]] | None:
        for mw in self.middleware:
            try:
                result = mw(request)
                if result is False:
                    return None
            except Exception as e:
                logger.error(f"Middleware error: {e}")

        match = self._match_route(request.path)
        if match is None:
            if self.fallback_target:
                return self.fallback_target, {}
            return None

        route, params = match
        if request.method not in route.methods:
            return None

        target = route.target
        if route.strip_prefix:
            base = self._normalize_path(route.path).rstrip("/*")
            remaining = request.path[len(base):]
            target = f"{target.rstrip('/')}/{remaining.lstrip('/')}"

        return target, {"route": asdict(route), "params": params}


class LoadBalancer:
    """45. Load balancing (weighted)"""

    def __init__(self):
        self.backends: list[dict[str, Any]] = []
        self._current_index = 0
        self._weights: dict[str, int] = {}
        self._health: dict[str, bool] = {}
        self._response_times: dict[str, list[float]] = defaultdict(list)

    def add_backend(self, url: str, weight: int = 1, metadata: dict[str, Any] | None = None):
        backend = {"url": url, "weight": weight, "metadata": metadata or {}}
        self.backends.append(backend)
        self._weights[url] = weight
        self._health[url] = True

    def remove_backend(self, url: str):
        self.backends = [b for b in self.backends if b["url"] != url]
        self._weights.pop(url, None)
        self._health.pop(url, None)

    def mark_healthy(self, url: str):
        self._health[url] = True

    def mark_unhealthy(self, url: str):
        self._health[url] = False

    def record_response_time(self, url: str, response_time_ms: float):
        self._response_times[url].append(response_time_ms)
        if len(self._response_times[url]) > 100:
            self._response_times[url] = self._response_times[url][-100:]

    def get_backend(self, strategy: str = "weighted_round_robin") -> str | None:
        healthy = [b for b in self.backends if self._health.get(b["url"], False)]
        if not healthy:
            return None

        if strategy == "round_robin":
            backend = healthy[self._current_index % len(healthy)]
            self._current_index += 1
            return backend["url"]

        elif strategy == "weighted_round_robin":
            total_weight = sum(self._weights.get(b["url"], 1) for b in healthy)
            import random
            r = random.uniform(0, total_weight)
            cumulative = 0
            for b in healthy:
                cumulative += self._weights.get(b["url"], 1)
                if r <= cumulative:
                    return b["url"]
            return healthy[-1]["url"]

        elif strategy == "least_connections":
            return min(healthy, key=lambda b: self._weights.get(b["url"], 1))["url"]

        elif strategy == "least_latency":
            def avg_latency(url):
                times = self._response_times.get(url, [])
                return sum(times) / len(times) if times else float("inf")
            return min(healthy, key=lambda b: avg_latency(b["url"]))["url"]

        elif strategy == "random":
            import random
            return random.choice(healthy)["url"]

        return healthy[0]["url"]

    def get_all_backends(self) -> list[dict[str, Any]]:
        return [
            {**b, "healthy": self._health.get(b["url"], True)}
            for b in self.backends
        ]


class CircuitBreaker:
    """46. Circuit breaker"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30,
                 half_open_max: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max = half_open_max
        self._states: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _get_state(self, service: str) -> dict[str, Any]:
        if service not in self._states:
            self._states[service] = {
                "state": CircuitState.CLOSED,
                "failure_count": 0,
                "success_count": 0,
                "last_failure_time": None,
                "half_open_count": 0
            }
        return self._states[service]

    def can_execute(self, service: str) -> bool:
        with self._lock:
            state = self._get_state(service)
            if state["state"] == CircuitState.CLOSED:
                return True
            if state["state"] == CircuitState.OPEN:
                if state["last_failure_time"]:
                    elapsed = (datetime.utcnow() - state["last_failure_time"]).total_seconds()
                    if elapsed >= self.recovery_timeout:
                        state["state"] = CircuitState.HALF_OPEN
                        state["half_open_count"] = 0
                        return True
                return False
            if state["state"] == CircuitState.HALF_OPEN:
                return state["half_open_count"] < self.half_open_max
        return False

    def record_success(self, service: str):
        with self._lock:
            state = self._get_state(service)
            state["failure_count"] = 0
            if state["state"] == CircuitState.OPEN:
                if state["last_failure_time"]:
                    elapsed = (datetime.utcnow() - state["last_failure_time"]).total_seconds()
                    if elapsed >= self.recovery_timeout:
                        state["state"] = CircuitState.CLOSED
                        state["success_count"] = 0
                        logger.info(f"Circuit breaker closed for {service}")
            elif state["state"] == CircuitState.HALF_OPEN:
                state["success_count"] += 1
                if state["success_count"] >= self.half_open_max:
                    state["state"] = CircuitState.CLOSED
                    state["success_count"] = 0
                    logger.info(f"Circuit breaker closed for {service}")

    def record_failure(self, service: str):
        with self._lock:
            state = self._get_state(service)
            state["failure_count"] += 1
            state["last_failure_time"] = datetime.utcnow()

            if state["state"] == CircuitState.HALF_OPEN:
                state["state"] = CircuitState.OPEN
                state["half_open_count"] = 0
                logger.warning(f"Circuit breaker reopened for {service}")
            elif state["failure_count"] >= self.failure_threshold:
                state["state"] = CircuitState.OPEN
                logger.warning(f"Circuit breaker opened for {service}")

    def get_state(self, service: str) -> dict[str, Any]:
        with self._lock:
            state = self._get_state(service)
            return {
                "service": service,
                "state": state["state"].value,
                "failure_count": state["failure_count"],
                "last_failure": state["last_failure_time"].isoformat() if state["last_failure_time"] else None
            }

    def reset(self, service: str):
        with self._lock:
            self._states[service] = {
                "state": CircuitState.CLOSED,
                "failure_count": 0,
                "success_count": 0,
                "last_failure_time": None,
                "half_open_count": 0
            }


class RequestValidator:
    """47. Request validation"""

    def __init__(self):
        self._schemas: dict[str, dict[str, Any]] = {}
        self._rules: dict[str, list[Callable]] = {}

    def register_schema(self, path: str, schema: dict[str, Any]):
        self._schemas[path] = schema

    def add_rule(self, path: str, rule: Callable):
        if path not in self._rules:
            self._rules[path] = []
        self._rules[path].append(rule)

    def validate(self, request: GatewayRequest) -> tuple[bool, list[str]]:
        errors = []
        schema = self._schemas.get(request.path)
        if schema:
            body_errors = self._validate_body(request.body, schema)
            errors.extend(body_errors)

        rules = self._rules.get(request.path, [])
        for rule in rules:
            try:
                result = rule(request)
                if isinstance(result, str):
                    errors.append(result)
                elif result is False:
                    errors.append("Validation failed")
            except Exception as e:
                errors.append(f"Rule error: {e}")

        if request.method in ("POST", "PUT", "PATCH") and request.body is None:
            errors.append("Request body required")

        content_type = request.headers.get("Content-Type", "")
        if request.method in ("POST", "PUT") and "json" in content_type:
            if request.body and not isinstance(request.body, (dict, list)):
                errors.append("Invalid JSON body")

        return len(errors) == 0, errors

    def _validate_body(self, body: Any, schema: dict[str, Any]) -> list[str]:
        errors = []
        if not body:
            return errors

        required = schema.get("required", [])
        properties = schema.get("properties", {})

        if isinstance(body, dict):
            for field in required:
                if field not in body:
                    errors.append(f"Missing required field: {field}")

            for field, prop_schema in properties.items():
                if field in body:
                    value = body[field]
                    expected_type = prop_schema.get("type")
                    if expected_type == "string" and not isinstance(value, str):
                        errors.append(f"Field '{field}' must be string")
                    elif expected_type == "integer" and not isinstance(value, int):
                        errors.append(f"Field '{field}' must be integer")
                    elif expected_type == "number" and not isinstance(value, (int, float)):
                        errors.append(f"Field '{field}' must be number")
                    elif expected_type == "boolean" and not isinstance(value, bool):
                        errors.append(f"Field '{field}' must be boolean")
                    elif expected_type == "array" and not isinstance(value, list):
                        errors.append(f"Field '{field}' must be array")

                    if "minLength" in prop_schema and isinstance(value, str):
                        if len(value) < prop_schema["minLength"]:
                            errors.append(f"Field '{field}' too short")
                    if "maxLength" in prop_schema and isinstance(value, str):
                        if len(value) > prop_schema["maxLength"]:
                            errors.append(f"Field '{field}' too long")
                    if "enum" in prop_schema:
                        if value not in prop_schema["enum"]:
                            errors.append(f"Field '{field}' invalid value")
        return errors


class ResponseCache:
    """48. Response caching"""

    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def _make_key(self, method: str, path: str, params: dict[str, str] | None = None) -> str:
        param_str = json.dumps(params or {}, sort_keys=True)
        return hashlib.md5(f"{method}:{path}:{param_str}".encode()).hexdigest()

    def get(self, method: str, path: str, params: dict[str, str] | None = None) -> GatewayResponse | None:
        key = self._make_key(method, path, params)
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() < entry["expires_at"]:
                    self._stats["hits"] += 1
                    response = entry["response"]
                    response.cached = True
                    return response
                else:
                    del self._cache[key]
            self._stats["misses"] += 1
        return None

    def set(self, method: str, path: str, response: GatewayResponse,
            ttl: int | None = None, params: dict[str, str] | None = None):
        key = self._make_key(method, path, params)
        with self._lock:
            self._cache[key] = {
                "response": response,
                "expires_at": time.time() + (ttl or self.default_ttl),
                "created_at": time.time()
            }

    def invalidate(self, method: str | None = None, path: str | None = None):
        with self._lock:
            if method is None and path is None:
                self._cache.clear()
                return
            keys_to_remove = []
            for key in self._cache:
                keys_to_remove.append(key)
            for key in keys_to_remove:
                del self._cache[key]

    def invalidate_pattern(self, pattern: str):
        with self._lock:
            keys_to_remove = [k for k in self._cache if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]
                self._stats["evictions"] += 1

    def get_stats(self) -> dict[str, Any]:
        total = self._stats["hits"] + self._stats["misses"]
        return {
            **self._stats,
            "total_requests": total,
            "hit_rate": round(self._stats["hits"] / total * 100, 2) if total > 0 else 0,
            "cache_size": len(self._cache)
        }

    def cleanup(self):
        now = time.time()
        with self._lock:
            expired = [k for k, v in self._cache.items() if v["expires_at"] < now]
            for key in expired:
                del self._cache[key]
                self._stats["evictions"] += 1


class CORSManager:
    """49. CORS management"""

    def __init__(self):
        self._rules: dict[str, dict[str, Any]] = {}
        self._default_rule = {
            "allow_origins": ["*"],
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
            "expose_headers": [],
            "allow_credentials": False,
            "max_age": 86400
        }

    def set_default(self, **kwargs):
        self._default_rule.update(kwargs)

    def add_rule(self, path: str, allow_origins: list[str] | None = None,
                 allow_methods: list[str] | None = None,
                 allow_headers: list[str] | None = None,
                 allow_credentials: bool = False):
        self._rules[path] = {
            "allow_origins": allow_origins or self._default_rule["allow_origins"],
            "allow_methods": allow_methods or self._default_rule["allow_methods"],
            "allow_headers": allow_headers or self._default_rule["allow_headers"],
            "allow_credentials": allow_credentials,
            "max_age": self._default_rule["max_age"]
        }

    def remove_rule(self, path: str):
        self._rules.pop(path, None)

    def _match_rule(self, path: str) -> dict[str, Any]:
        if path in self._rules:
            return self._rules[path]
        for pattern, rule in self._rules.items():
            if path.startswith(pattern.rstrip("/*")):
                return rule
        return self._default_rule

    def check_origin(self, origin: str, path: str) -> bool:
        rule = self._match_rule(path)
        if "*" in rule["allow_origins"]:
            return True
        return origin in rule["allow_origins"]

    def get_headers(self, origin: str, method: str, path: str,
                    request_headers: list[str] | None = None) -> dict[str, str]:
        rule = self._match_rule(path)
        headers = {}

        if self.check_origin(origin, path):
            headers["Access-Control-Allow-Origin"] = origin
        elif "*" in rule["allow_origins"]:
            headers["Access-Control-Allow-Origin"] = "*"

        headers["Access-Control-Allow-Methods"] = ", ".join(rule["allow_methods"])
        headers["Access-Control-Allow-Headers"] = ", ".join(rule["allow_headers"])

        if rule["allow_credentials"]:
            headers["Access-Control-Allow-Credentials"] = "true"

        if rule["expose_headers"]:
            headers["Access-Control-Expose-Headers"] = ", ".join(rule["expose_headers"])

        headers["Access-Control-Max-Age"] = str(rule["max_age"])

        return headers

    def handle_preflight(self, origin: str, method: str, path: str) -> GatewayResponse:
        headers = self.get_headers(origin, "OPTIONS", path)
        return GatewayResponse(status_code=204, body="", headers=headers)


class APIAnalytics:
    """50. API analytics (usage, latency, errors)"""

    def __init__(self):
        self._requests: list[dict[str, Any]] = []
        self._metrics: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "count": 0, "errors": 0, "total_latency": 0, "methods": defaultdict(int),
            "status_codes": defaultdict(int), "endpoints": defaultdict(int)
        })
        self._hourly: dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def record_request(self, method: str, path: str, status_code: int,
                       latency_ms: float, client_ip: str = "",
                       api_key: str | None = None):
        timestamp = datetime.utcnow()
        entry = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "client_ip": client_ip,
            "api_key": api_key,
            "timestamp": timestamp.isoformat()
        }

        with self._lock:
            self._requests.append(entry)
            if len(self._requests) > 100000:
                self._requests = self._requests[-50000:]

            hour_key = timestamp.strftime("%Y-%m-%d-%H")
            self._hourly[hour_key] += 1

            day_key = timestamp.strftime("%Y-%m-%d")
            day_metrics = self._metrics[day_key]
            day_metrics["count"] += 1
            day_metrics["total_latency"] += latency_ms
            day_metrics["methods"][method] += 1
            day_metrics["status_codes"][str(status_code)] += 1

            endpoint_key = f"{method} {path}"
            day_metrics["endpoints"][endpoint_key] += 1

            if status_code >= 400:
                day_metrics["errors"] += 1

    def get_summary(self, days: int = 7) -> dict[str, Any]:
        summary = {
            "total_requests": 0,
            "total_errors": 0,
            "avg_latency_ms": 0,
            "top_endpoints": [],
            "error_rate": 0,
            "daily_metrics": {}
        }

        total_latency = 0
        all_endpoints = defaultdict(int)

        for day_key in sorted(self._metrics.keys())[-days:]:
            metrics = self._metrics[day_key]
            summary["total_requests"] += metrics["count"]
            summary["total_errors"] += metrics["errors"]
            total_latency += metrics["total_latency"]
            summary["daily_metrics"][day_key] = {
                "requests": metrics["count"],
                "errors": metrics["errors"],
                "avg_latency": round(metrics["total_latency"] / metrics["count"], 2) if metrics["count"] > 0 else 0
            }
            for endpoint, count in metrics["endpoints"].items():
                all_endpoints[endpoint] += count

        if summary["total_requests"] > 0:
            summary["avg_latency_ms"] = round(total_latency / summary["total_requests"], 2)
            summary["error_rate"] = round(summary["total_errors"] / summary["total_requests"] * 100, 2)

        summary["top_endpoints"] = sorted(
            [{"endpoint": ep, "count": c} for ep, c in all_endpoints.items()],
            key=lambda x: x["count"], reverse=True
        )[:10]

        return summary

    def get_endpoint_stats(self, method: str, path: str) -> dict[str, Any]:
        stats = {"count": 0, "errors": 0, "total_latency": 0, "latencies": []}
        for entry in self._requests:
            if entry["method"] == method and entry["path"] == path:
                stats["count"] += 1
                stats["total_latency"] += entry["latency_ms"]
                stats["latencies"].append(entry["latency_ms"])
                if entry["status_code"] >= 400:
                    stats["errors"] += 1

        if stats["count"] > 0:
            stats["avg_latency"] = round(stats["total_latency"] / stats["count"], 2)
            stats["p95_latency"] = round(sorted(stats["latencies"])[int(len(stats["latencies"]) * 0.95)] if stats["latencies"] else 0, 2)
            stats["p99_latency"] = round(sorted(stats["latencies"])[int(len(stats["latencies"]) * 0.99)] if stats["latencies"] else 0, 2)
            stats["error_rate"] = round(stats["errors"] / stats["count"] * 100, 2)

        del stats["latencies"]
        return stats

    def get_hourly_distribution(self, date: str | None = None) -> dict[str, int]:
        if date:
            return {k: v for k, v in self._hourly.items() if k.startswith(date)}
        return dict(self._hourly)

    def get_error_breakdown(self) -> dict[str, int]:
        breakdown = defaultdict(int)
        for entry in self._requests:
            if entry["status_code"] >= 400:
                breakdown[str(entry["status_code"])] += 1
        return dict(breakdown)

    def get_slowest_endpoints(self, limit: int = 10) -> list[dict[str, Any]]:
        endpoint_times = defaultdict(list)
        for entry in self._requests:
            key = f"{entry['method']} {entry['path']}"
            endpoint_times[key].append(entry["latency_ms"])

        slowest = []
        for endpoint, times in endpoint_times.items():
            avg = sum(times) / len(times)
            slowest.append({"endpoint": endpoint, "avg_latency_ms": round(avg, 2), "count": len(times)})

        return sorted(slowest, key=lambda x: x["avg_latency_ms"], reverse=True)[:limit]
