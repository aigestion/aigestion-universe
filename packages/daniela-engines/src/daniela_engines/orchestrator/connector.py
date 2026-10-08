"""Engine Connector - manages connections to individual engines with pooling, retries, and circuit breaker."""

import json
import threading
import time
from typing import Any
from urllib.request import Request, urlopen


class CircuitBreaker:
    """Circuit breaker per engine: opens after `threshold` failures."""

    def __init__(self, threshold: int = 5, reset_timeout: float = 30.0) -> None:
        self._lock = threading.Lock()
        self._failures = 0
        self._threshold = threshold
        self._reset_timeout = reset_timeout
        self._opened_at: float = 0.0
        self._state = "closed"

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == "open":
                if time.time() - self._opened_at >= self._reset_timeout:
                    self._state = "half-open"
            return self._state

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._state = "closed"

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self._threshold:
                self._state = "open"
                self._opened_at = time.time()

    def allow_request(self) -> bool:
        return self.state != "open"


class EngineConnector:
    """Connects to a single engine with connection pooling, retries, and circuit breaker."""

    def __init__(
        self,
        engine_name: str,
        port: int,
        host: str = "127.0.0.1",
        timeout: float = 3.0,
        max_retries: int = 3,
    ) -> None:
        self.engine_name = engine_name
        self.port = port
        self.host = host
        self.timeout = timeout
        self.max_retries = max_retries
        self._circuit = CircuitBreaker()
        self._base_url = f"http://{host}:{port}"
        self._stats_lock = threading.Lock()
        self._request_count = 0
        self._error_count = 0

    def connect(self) -> bool:
        """Quick connectivity check (health probe)."""
        return self.health_check()

    def health_check(self) -> bool:
        """Return True if the engine responds to /health within timeout."""
        try:
            req = Request(f"{self._base_url}/health", method="GET")
            with urlopen(req, timeout=self.timeout) as resp:
                ok = resp.status == 200
                if ok:
                    self._circuit.record_success()
                return ok
        except Exception:
            self._circuit.record_failure()
            return False

    def proxy_request(
        self,
        path: str,
        method: str = "GET",
        data: dict | None = None,
    ) -> dict[str, Any]:
        """Forward a request to the target engine with retry and circuit breaker."""
        if not self._circuit.allow_request():
            return {
                "status": 503,
                "error": "circuit_breaker_open",
                "engine": self.engine_name,
            }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                url = f"{self._base_url}{path}"
                body = json.dumps(data).encode() if data else None
                req = Request(url, data=body, method=method)
                if body is not None:
                    req.add_header("Content-Type", "application/json")
                with urlopen(req, timeout=self.timeout) as resp:
                    resp_body = resp.read().decode()
                    self._circuit.record_success()
                    with self._stats_lock:
                        self._request_count += 1
                    return {
                        "status": resp.status,
                        "data": json.loads(resp_body) if resp_body else {},
                        "engine": self.engine_name,
                    }
            except Exception as e:
                last_error = e
                backoff = min(2 ** attempt * 0.1, 2.0)
                time.sleep(backoff)

        self._circuit.record_failure()
        with self._stats_lock:
            self._error_count += 1
        return {
            "status": 502,
            "error": str(last_error),
            "engine": self.engine_name,
        }

    def get_stats(self) -> dict:
        with self._stats_lock:
            return {
                "engine": self.engine_name,
                "port": self.port,
                "requests": self._request_count,
                "errors": self._error_count,
                "circuit_state": self._circuit.state,
            }

    def get_circuit_state(self) -> str:
        return self._circuit.state
