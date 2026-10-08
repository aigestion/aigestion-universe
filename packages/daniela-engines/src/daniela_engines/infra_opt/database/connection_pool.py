from flask import Blueprint, jsonify

cp_bp = Blueprint("connection_pool", __name__)

@cp_bp.route("/api/infra/db/pool/status")
def c_status():
    return jsonify({"pool_size": 20, "pool_recycle": 3600, "active": 5, "idle": 15})

@cp_bp.route("/api/infra/db/pool/web")
def c_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Connection Pool</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:20px 0}
</style></head><body><h1>CONNECTION POOLING</h1>
<div class="grid"><div class="card"><div class="num">20</div><p>Pool Size</p></div><div class="card"><div class="num">3600s</div><p>Recycle</p></div><div class="card"><div class="num">5</div><p>Active</p></div><div class="card"><div class="num">15</div><p>Idle</p></div></div></body></html>"""
