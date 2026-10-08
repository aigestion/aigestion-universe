from flask import Blueprint, jsonify

brotli_bp = Blueprint("brotli_compression", __name__)

@brotli_bp.route("/api/perf/brotli/status")
def b_status():
    return jsonify({"enabled": True, "level": 6, "ratio": "2.5x", "algorithms": ["brotli", "gzip", "deflate"]})

@brotli_bp.route("/api/perf/brotli/web")
def b_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Brotli Compression</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>BROTLI COMPRESSION</h1>
<div class="card"><h3>Level</h3><p>6 (balanced)</p></div>
<div class="card"><h3>Ratio</h3><p>2.5x</p></div>
<div class="card"><h3>Fallback</h3><p>gzip, deflate</p></div></body></html>"""
