
from flask import Blueprint, jsonify

dc_bp = Blueprint("docker_compose", __name__)

@dc_bp.route("/api/infra/docker/status")
def d_status():
    return jsonify({
        "version": "3.8",
        "services": 4,
        "networks": 1,
        "ports": ["5000", "80", "443", "6379", "9090"],
        "volumes": 4
    })

@dc_bp.route("/api/infra/docker/web")
def d_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Docker Compose</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.svc{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin:20px 0}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:15px;text-align:center}
.card .num{font-size:28px;color:#00ff88}
</style></head><body><h1>DOCKER COMPOSE V2</h1>
<div class="grid"><div class="card"><div class="num">4</div><p>Services</p></div><div class="card"><div class="num">5</div><p>Ports</p></div><div class="card"><div class="num">1</div><p>Network</p></div><div class="card"><div class="num">4</div><p>Volumes</p></div></div>
<div class="svc"><h3>Daniela OS</h3><p>Container: aig-daniela</p><p>Port: 5000:5000</p></div>
<div class="svc"><h3>Nginx Gateway</h3><p>Port: 80:80, 443:443</p></div>
<div class="svc"><h3>Redis</h3><p>Port: 6379:6379</p></div>
<div class="svc"><h3>Prometheus</h3><p>Port: 9090:9090</p></div></body></html>"""
