from flask import Blueprint, jsonify

vs_bp = Blueprint("vector_search", __name__)

@vs_bp.route("/api/infra/db/vector/status")
def v_status():
    return jsonify({"engine": "sqlite-vec", "database": "memory_rag.db", "dimensions": 1536, "indexed": 5000})

@vs_bp.route("/api/infra/db/vector/web")
def v_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Vector Search</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>VECTOR SEARCH</h1>
<div class="card"><h3>Engine</h3><p>sqlite-vec</p></div>
<div class="card"><h3>Database</h3><p>memory_rag.db</p></div>
<div class="card"><h3>Dimensions</h3><p>1536</p></div>
<div class="card"><h3>Indexed</h3><p>5000 vectors</p></div></body></html>"""
