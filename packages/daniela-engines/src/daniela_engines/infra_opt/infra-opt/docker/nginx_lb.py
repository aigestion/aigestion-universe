from flask import Blueprint, jsonify

nginx_bp = Blueprint("nginx_lb", __name__)

@nginx_bp.route("/api/infra/nginx/status")
def n_status():
    return jsonify({"upstreams": 6, "load_balancer": True, "strategy": "round_robin", "ssl_termination": True})

@nginx_bp.route("/api/infra/nginx/web")
def n_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Nginx LB</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:20px 0}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;text-align:center}
.card .num{font-size:28px;color:#00ff88}
.upstream{background:#111;border:1px solid #333;border-radius:12px;padding:15px;margin:5px 0}
.upstream.online{border-color:#00ff88}
</style></head><body><h1>NGINX LOAD BALANCER</h1>
<div class="grid"><div class="card"><div class="num">6</div><p>Upstreams</p></div><div class="card"><div class="num">RR</div><p>Strategy</p></div><div class="card"><div class="num">SSL</div><p>TLS</p></div></div>
<div class="upstream online"><h3>:5020</h3><p>Epic PC</p></div>
<div class="upstream online"><h3>:9200</h3><p>Daniela</p></div>
<div class="upstream online"><h3>:9300</h3><p>Hermes</p></div>
<div class="upstream online"><h3>:9400</h3><p>Optimization</p></div>
<div class="upstream online"><h3>:9500</h3><p>Frontend V1</p></div>
<div class="upstream online"><h3>:9600</h3><p>Frontend V2</p></div></body></html>"""
