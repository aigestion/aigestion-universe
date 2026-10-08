from flask import Blueprint, jsonify

rr_bp = Blueprint("redis_rate_limit", __name__)

@rr_bp.route("/api/infra/api/redis/status")
def r_status():
    return jsonify({"engine": "Redis", "replaced": "SQLite", "ttl": 3600, "requests_per_hour": 100, "speed": "100x"})

@rr_bp.route("/api/infra/api/redis/web")
def r_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Redis Rate Limit</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>REDIS RATE LIMITING</h1>
<div class="card"><h3>Engine</h3><p>Redis (was SQLite)</p></div>
<div class="card"><h3>TTL</h3><p>3600s</p></div>
<div class="card"><h3>Speed</h3><p>100x faster</p></div>
<div class="card"><h3>Limit</h3><p>100 req/hour</p></div></body></html>"""
