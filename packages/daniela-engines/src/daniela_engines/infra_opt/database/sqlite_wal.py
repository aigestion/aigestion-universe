from flask import Blueprint, jsonify

wal_bp = Blueprint("sqlite_wal", __name__)

@wal_bp.route("/api/infra/db/wal/status")
def w_status():
    return jsonify({"mode": "WAL", "wal_size": "4MB", "checkpoint": "60s", "concurrent_readers": 5})

@wal_bp.route("/api/infra/db/wal/web")
def w_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>SQLite WAL</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>SQLITE WAL MODE</h1>
<div class="card"><h3>Mode</h3><p>WAL (Write-Ahead Logging)</p></div>
<div class="card"><h3>WAL Size</h3><p>4MB max</p></div>
<div class="card"><h3>Checkpoint</h3><p>Every 60s</p></div>
<div class="card"><h3>Concurrent Readers</h3><p>5 simultaneous</p></div></body></html>"""
