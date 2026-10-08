from flask import Blueprint, jsonify

async_bp = Blueprint("async_io", __name__)

@async_bp.route("/api/perf/async/status")
def a_status():
    return jsonify({"engine": "Quart", "protocol": "HTTP/2", "workers": 4, "non_blocking": True})

@async_bp.route("/api/perf/async/web")
def a_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Async I/O</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>ASYNC I/O</h1>
<div class="card"><h3>Engine</h3><p>Quart</p></div>
<div class="card"><h3>Protocol</h3><p>HTTP/2</p></div>
<div class="card"><h3>Workers</h3><p>4</p></div></body></html>"""
