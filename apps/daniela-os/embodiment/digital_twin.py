from flask import Blueprint, jsonify

twin_bp = Blueprint("digital_twin", __name__)
_state = {
    "active": True,
    "model": {"sleep": 7.5, "work": 8, "exercise": 1, "social": 2},
    "accuracy": 78,
}


@twin_bp.route("/api/embodiment/twin/status")
def t_status():
    return jsonify(_state)


@twin_bp.route("/api/embodiment/twin/web")
def t_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Digital Twin</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.twin{text-align:center}
.avatar{width:200px;height:200px;border-radius:50%;background:linear-gradient(135deg,#00f0ff,#ff0066);margin:0 auto 20px;animation:rotate 10s linear infinite}
@keyframes rotate{to{transform:rotate(360deg)}}
.model{display:flex;gap:20px;justify-content:center;margin-top:20px}
.category{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;width:100px}
.category .hours{font-size:24px;color:#00ff88}
</style></head><body>
<div class="twin">
<h2>DIGITAL TWIN</h2>
<div class="avatar"></div>
<p>Accuracy: <span id="acc">78</span>%</p>
<div class="model" id="model"></div>
</div>
<script>fetch('/api/embodiment/twin/status').then(r=>r.json()).then(d=>{document.getElementById('acc').textContent=d.accuracy;document.getElementById('model').innerHTML=Object.entries(d.model).map(([k,v])=>'<div class="category"><div class="hours">'+v+'h</div><p>'+k+'</p></div>').join('')})</script>
</body></html>"""
