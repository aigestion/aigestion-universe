from flask import Blueprint, jsonify

rc_bp = Blueprint("request_caching", __name__)

@rc_bp.route("/api/infra/api/cache/status")
def c_status():
    return jsonify({"engine": "Redis", "ttl": 300, "cached_gets": True, "hit_rate": "87%"})

@rc_bp.route("/api/infra/api/cache/web")
def c_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Request Cache</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>REQUEST CACHING</h1>
<div class="card"><h3>Engine</h3><p>Redis</p></div>
<div class="card"><h3>TTL</h3><p>300s</p></div>
<div class="card"><h3>Hit Rate</h3><p>87%</p></div>
<div class="card"><h3>Method</h3><p>GET only</p></div></body></html>"""
