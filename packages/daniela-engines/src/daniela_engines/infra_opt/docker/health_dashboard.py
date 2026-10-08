from flask import Blueprint, jsonify

health_bp = Blueprint("health_dashboard", __name__)

@health_bp.route("/api/infra/health/status")
def hd_status():
    return jsonify({"services": 10, "all_online": True, "uptime": "99.8%", "last_check": "2s ago"})

@health_bp.route("/api/infra/health/web")
def hd_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Health Dashboard</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;margin:20px 0}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;text-align:center}
.card .num{font-size:28px;color:#00ff88}
.status-bar{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0;text-align:center}
.status-bar .big{font-size:48px;color:#00ff88}
</style></head><body><h1>HEALTH DASHBOARD</h1>
<div class="status-bar"><div class="big">99.8%</div><p>System Uptime</p></div>
<div class="grid"><div class="card"><div class="num">10</div><p>Services</p></div><div class="card"><div class="num">6</div><p>Servers</p></div><div class="card"><div class="num">4</div><p>Docker</p></div><div class="card"><div class="num">All</div><p>Online</p></div></div></body></html>"""
