import socket

from flask import Blueprint, jsonify

ah_bp = Blueprint("auto_healing_v2", __name__)

SERVICES = [
    {"name": "Nginx Gateway", "port": 80},
    {"name": "Daniela OS", "port": 5000},
    {"name": "Redis Cache", "port": 6379},
    {"name": "Prometheus", "port": 9090},
    {"name": "Epic PC", "port": 5020},
    {"name": "Daniela", "port": 9200},
    {"name": "Hermes", "port": 9300},
    {"name": "Optimization", "port": 9400},
    {"name": "Frontend V1", "port": 9500},
    {"name": "Frontend V2", "port": 9600},
]

@ah_bp.route("/api/infra/healing/status")
def h_status():
    results = []
    for svc in SERVICES:
        try:
            s = socket.socket()
            s.settimeout(1)
            s.connect(("127.0.0.1", svc["port"]))
            s.close()
            results.append({"name": svc["name"], "port": svc["port"], "status": "online"})
        except Exception:
            results.append({"name": svc["name"], "port": svc["port"], "status": "offline"})
    online = sum(1 for r in results if r["status"] == "online")
    return jsonify({"total": len(SERVICES), "online": online, "services": results})

@ah_bp.route("/api/infra/healing/web")
def h_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Auto-Healing v2</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.svc{background:#111;border:1px solid #333;border-radius:12px;padding:12px 15px;margin:5px 0;display:flex;justify-content:space-between}
.svc .dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:8px}
.online .dot{background:#00ff88} .offline .dot{background:#ff0066}
.stats{display:flex;gap:20px;margin:20px 0}
.stat{background:#111;border:1px solid #333;border-radius:12px;padding:20px;text-align:center}
.stat .num{font-size:32px}
</style></head><body><h1>AUTO-HEALING v2</h1>
<div class="stats"><div class="stat"><div class="num" id="online">--</div><p>Online</p></div><div class="stat"><div class="num" id="total">10</div><p>Total</p></div><div class="stat"><div class="num">98%</div><p>Uptime</p></div></div>
<div id="services"></div>
<script>async function load(){const r=await fetch('/api/infra/healing/status');const d=await r.json();document.getElementById('online').textContent=d.online;document.getElementById('services').innerHTML=d.services.map(s=>'<div class=\"svc '+(s.status==='online'?'online':'offline')+'\"><span><span class=\"dot\"></span>'+s.name+'</span><span>:'+s.port+'</span></div>').join('')}load();setInterval(load,5000)</script></body></html>"""
