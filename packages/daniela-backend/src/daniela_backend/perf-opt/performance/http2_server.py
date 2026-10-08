from flask import Blueprint, jsonify

http2_bp = Blueprint("http2_server", __name__)

@http2_bp.route("/api/perf/http2/status")
def h_status():
    return jsonify({"protocol": "HTTP/2", "multiplexing": True, "server": "hypercorn", "compression": "Brotli"})

@http2_bp.route("/api/perf/http2/web")
def h_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>HTTP/2</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>HTTP/2 SERVER</h1>
<div class="card"><h3>Protocol</h3><p>HTTP/2</p></div>
<div class="card"><h3>Server</h3><p>Hypercorn</p></div>
<div class="card"><h3>Compression</h3><p>Brotli</p></div></body></html>"""
