from flask import Blueprint, jsonify

worker_bp = Blueprint("bg_workers", __name__)

@worker_bp.route("/api/perf/worker/status")
def w_status():
    return jsonify({"enabled": True, "queue": "redis", "concurrency": 10, "tasks": ["parse", "encode", "compress"]})

@worker_bp.route("/api/perf/worker/web")
def w_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Background Workers</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>BACKGROUND WORKERS</h1>
<div class="card"><h3>Queue</h3><p>Redis</p></div>
<div class="card"><h3>Concurrency</h3><p>10</p></div>
<div class="card"><h3>Tasks</h3><p>3 queued</p></div></body></html>"""
