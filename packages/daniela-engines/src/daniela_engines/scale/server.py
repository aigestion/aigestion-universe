"""
Scale Engine Flask Server - Port 9820
======================================
Endpoints:
  /api/scale/status
  /api/scale/cache      (stats/invalidate/warm)
  /api/scale/compress   (compress/decompress)
  /api/scale/concurrency (pool/stats)
  /api/scale/resilience (circuit-breaker/bulkhead)
  /api/scale/optimize   (analyze/suggest)
"""

from __future__ import annotations

import time

from caching import CacheWarmer, WarmingStrategy, default_cache
from concurrency import ConcurrencyManager
from data_compression import CompressionManager
from flask import Flask, jsonify, request
from optimization import OptimizationManager, QueryPlan, QueryStep, QueryType
from resilience import (
    CircuitOpenError,
    ResilienceManager,
    RetryStrategy,
    RetryWithJitter,
)

app = Flask(__name__)

cache = default_cache
compression = CompressionManager()
concurrency = ConcurrencyManager()
resilience = ResilienceManager()
optimization = OptimizationManager()

_start_time = time.time()


# ---------------------------------------------------------------------------
# /api/scale/status
# ---------------------------------------------------------------------------

@app.route("/api/scale/status", methods=["GET"])
def status():
    uptime = time.time() - _start_time
    return jsonify({
        "status": "running",
        "service": "scale_engine",
        "version": "1.0.0",
        "uptime_seconds": round(uptime, 2),
        "modules": ["caching", "compression", "concurrency", "resilience", "optimization"],
        "ideas_count": 50,
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "scale_engine"})


# ---------------------------------------------------------------------------
# /api/scale/cache
# ---------------------------------------------------------------------------

@app.route("/api/scale/cache", methods=["GET"])
def cache_stats():
    return jsonify(cache.stats())


@app.route("/api/scale/cache/invalidate", methods=["POST"])
def cache_invalidate():
    data = request.get_json(force=True, silent=True) or {}
    key = data.get("key")
    if key:
        cache.invalidate(key)
        return jsonify({"status": "invalidated", "key": key})
    return jsonify({"error": "Missing 'key'"}), 400


@app.route("/api/scale/cache/warm", methods=["POST"])
def cache_warm():
    data = request.get_json(force=True, silent=True) or {}
    entries = data.get("entries", {})
    warmer = CacheWarmer(strategy=WarmingStrategy.EAGER)
    for key, value in entries.items():
        warmer.register(key, lambda v=value: v)
    warmer.warm(cache)
    return jsonify({"status": "warmed", "count": len(entries)})


# ---------------------------------------------------------------------------
# /api/scale/compress
# ---------------------------------------------------------------------------

@app.route("/api/scale/compress", methods=["POST"])
def compress():
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "")
    method = data.get("method", "gzip")

    try:
        compressed = compression.compress(text, method=method)
        return jsonify({
            "method": method,
            "original_size": len(text.encode("utf-8")),
            "compressed_size": len(compressed),
            "ratio": round(len(compressed) / max(1, len(text.encode("utf-8"))), 4),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/scale/compress/decompress", methods=["POST"])
def decompress():
    data = request.get_json(force=True, silent=True) or {}
    method = data.get("method", "gzip")
    text = data.get("text", "")

    try:
        compressed = compression.compress(text, method=method)
        decompressed = compression.decompress(compressed, method=method)
        return jsonify({
            "method": method,
            "roundtrip_ok": decompressed == text,
            "decompressed_size": len(str(decompressed).encode("utf-8")),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


# ---------------------------------------------------------------------------
# /api/scale/concurrency
# ---------------------------------------------------------------------------

@app.route("/api/scale/concurrency", methods=["GET"])
def concurrency_stats():
    return jsonify(concurrency.stats())


@app.route("/api/scale/concurrency/pool", methods=["POST"])
def concurrency_pool():
    data = request.get_json(force=True, silent=True) or {}
    service = data.get("service", "default")
    max_size = data.get("max_size", 20)

    pool = concurrency.connection_pools.get_pool(service, max_size=max_size)
    return jsonify({
        "service": service,
        "pool": pool.stats(),
    })


@app.route("/api/scale/concurrency/backpressure", methods=["GET"])
def backpressure_stats():
    return jsonify(concurrency.backpressure.stats())


# ---------------------------------------------------------------------------
# /api/scale/resilience
# ---------------------------------------------------------------------------

@app.route("/api/scale/resilience", methods=["GET"])
def resilience_stats():
    return jsonify(resilience.stats())


@app.route("/api/scale/resilience/circuit-breaker", methods=["POST"])
def circuit_breaker_call():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "default")
    action = data.get("action", "stats")
    failure_threshold = data.get("failure_threshold", 5)

    if action == "stats":
        cb = resilience.get_circuit_breaker(name, failure_threshold=failure_threshold)
        return jsonify(cb.stats())
    elif action == "reset":
        cb = resilience.get_circuit_breaker(name, failure_threshold=failure_threshold)
        cb.reset()
        return jsonify({"status": "reset", "name": name})
    elif action == "call":
        # Simulate a call with optional failure
        simulate_fail = data.get("simulate_fail", False)
        cb = resilience.get_circuit_breaker(name, failure_threshold=failure_threshold)
        try:
            def _dummy():
                if simulate_fail:
                    raise ValueError("Simulated failure")
                return "ok"
            result = cb.call(_dummy)
            return jsonify({"status": "success", "result": result, "circuit": cb.stats()})
        except CircuitOpenError as exc:
            return jsonify({"status": "rejected", "error": str(exc), "circuit": cb.stats()}), 503
        except ValueError as exc:
            return jsonify({"status": "failed", "error": str(exc), "circuit": cb.stats()}), 500

    return jsonify({"error": f"Unknown action: {action}"}), 400


@app.route("/api/scale/resilience/bulkhead", methods=["POST"])
def bulkhead_call():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "default")
    max_concurrent = data.get("max_concurrent", 10)

    bh = resilience.bulkheads.get(name, max_concurrent=max_concurrent)
    return jsonify(bh.stats())


@app.route("/api/scale/resilience/retry", methods=["POST"])
def retry_call():
    data = request.get_json(force=True, silent=True) or {}
    max_retries = data.get("max_retries", 3)
    strategy_str = data.get("strategy", "exponential")
    simulate_fail = data.get("simulate_fail", False)
    fail_count = data.get("fail_count", 2)

    strategy_map = {
        "fixed": RetryStrategy.FIXED,
        "exponential": RetryStrategy.EXPONENTIAL,
        "linear": RetryStrategy.LINEAR,
    }
    strategy = strategy_map.get(strategy_str, RetryStrategy.EXPONENTIAL)
    retrier = RetryWithJitter(max_retries=max_retries, strategy=strategy, base_delay=0.01)

    call_count = [0]

    def _fn():
        call_count[0] += 1
        if simulate_fail and call_count[0] <= fail_count:
            raise ValueError(f"Failure #{call_count[0]}")
        return "success"

    try:
        retrier._fn = _fn
        retrier.execute(_fn)
        return jsonify({"status": "success", "attempts": call_count[0]})
    except ValueError as exc:
        return jsonify({"status": "failed", "error": str(exc), "attempts": call_count[0]}), 500


@app.route("/api/scale/resilience/rate-limit", methods=["GET"])
def rate_limit_stats():
    return jsonify(resilience.rate_limiter.stats())


@app.route("/api/scale/resilience/chaos", methods=["POST"])
def chaos_action():
    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action", "stats")

    if action == "stats":
        return jsonify(resilience.chaos_injector.stats())
    elif action == "disable_all":
        resilience.chaos_injector.disable_all()
        return jsonify({"status": "chaos_disabled"})

    return jsonify({"error": f"Unknown action: {action}"}), 400


# ---------------------------------------------------------------------------
# /api/scale/optimize
# ---------------------------------------------------------------------------

@app.route("/api/scale/optimize", methods=["GET"])
def optimize_stats():
    return jsonify(optimization.stats())


@app.route("/api/scale/optimize/analyze", methods=["POST"])
def optimize_analyze():
    data = request.get_json(force=True, silent=True) or {}
    query_type_str = data.get("query_type", "SELECT")
    table = data.get("table", "unknown")
    steps_data = data.get("steps", [])

    qt_map = {
        "SELECT": QueryType.SELECT,
        "INSERT": QueryType.INSERT,
        "UPDATE": QueryType.UPDATE,
        "DELETE": QueryType.DELETE,
    }
    query_type = qt_map.get(query_type_str, QueryType.SELECT)

    steps = []
    for s in steps_data:
        steps.append(QueryStep(
            operation=s.get("operation", "scan"),
            table=s.get("table", table),
            cost_estimate=s.get("cost_estimate", 100),
            rows_estimate=s.get("rows_estimate", 1000),
            index_used=s.get("index_used", False),
        ))

    plan = QueryPlan(query_type=query_type, steps=steps)
    analyzed = optimization.query_analyzer.analyze(plan)

    return jsonify({
        "total_cost": round(analyzed.total_cost, 2),
        "warnings": analyzed.warnings,
        "suggestions": analyzed.suggestions,
        "stats": optimization.query_analyzer.get_stats(),
    })


@app.route("/api/scale/optimize/suggest", methods=["POST"])
def optimize_suggest():
    data = request.get_json(force=True, silent=True) or {}
    category = data.get("category", "general")

    suggestions = {
        "caching": [
            "Enable multi-tier caching (L1 + L2)",
            "Implement cache warming for hot keys",
            "Use cache-aside pattern for read-heavy workloads",
        ],
        "compression": [
            "Enable gzip for responses > 1KB",
            "Use msgpack for binary payloads",
            "Enable streaming compression for large data",
        ],
        "concurrency": [
            "Use connection pooling for external services",
            "Implement backpressure under load",
            "Configure thread pool based on CPU cores",
        ],
        "resilience": [
            "Add circuit breakers to external calls",
            "Implement retry with exponential backoff",
            "Add health check endpoints",
        ],
        "general": [
            "Profile startup time and defer non-critical init",
            "Use object pooling for frequently created objects",
            "Enable string interning for repeated values",
            "Monitor N+1 query patterns",
        ],
    }

    items = suggestions.get(category, suggestions["general"])
    return jsonify({"category": category, "suggestions": items})


@app.route("/api/scale/optimize/batch", methods=["POST"])
def optimize_batch():
    data = request.get_json(force=True, silent=True) or {}
    items = data.get("items", [])
    batch_size = data.get("batch_size", 100)

    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        results.append({"batch_index": i // batch_size, "size": len(batch), "items": batch})

    return jsonify({
        "total_items": len(items),
        "batches": len(results),
        "results": results,
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    return app


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.getenv("SERVICE_PORT", "9820")), debug=False)
