from flask import Blueprint, jsonify

grpc_bp = Blueprint("grpc_bridge", __name__)

@grpc_bp.route("/api/infra/api/grpc/status")
def g_status():
    return jsonify({"enabled": True, "port": 50051, "protocol": "HTTP/2", "services": 4})

@grpc_bp.route("/api/infra/api/grpc/web")
def g_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>gRPC Bridge</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>gRPC BRIDGE</h1>
<div class="card"><h3>Port</h3><p>50051</p></div>
<div class="card"><h3>Protocol</h3><p>HTTP/2</p></div>
<div class="card"><h3>Services</h3><p>4 registered</p></div></body></html>"""
