from flask import Blueprint, jsonify, request

energy_bp = Blueprint("energy_management", __name__)
_state = {"pc_battery": None, "phone_battery": 80, "strategy": "balanced", "power_saving": False}


@energy_bp.route("/api/proactive/energy/status")
def e_status():
    return jsonify(_state)


@energy_bp.route("/api/proactive/energy/set", methods=["POST"])
def e_set():
    data = request.json or {}
    _state["strategy"] = data.get("strategy", "balanced")
    _state["power_saving"] = _state["strategy"] == "power_save"
    return jsonify({"ok": True})


@energy_bp.route("/api/proactive/energy/web")
def e_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Energy Management</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.energy{text-align:center}
.battery{width:200px;height:100px;border:3px solid #00f0ff;border-radius:10px;margin:20px auto;position:relative;overflow:hidden}
.battery::after{content:'';position:absolute;right:-15px;top:25px;width:10px;height:50px;background:#00f0ff;border-radius:0 5px 5px 0}
.battery-fill{height:100%;background:linear-gradient(90deg,#00ff88,#00cc66);transition:width .5s}
.strategies{display:flex;gap:10px;margin-top:20px}
.strat{padding:10px 20px;border:1px solid #333;border-radius:8px;cursor:pointer;background:#111}
.strat.active{border-color:#00ff88;background:#00ff8822}
</style></head><body>
<div class="energy">
<h2>ENERGY MANAGEMENT</h2>
<div class="battery"><div class="battery-fill" id="fill" style="width:80%"></div></div>
<p>Phone: <span id="pct">80</span>%</p>
<div class="strategies">
<div class="strat active" onclick="set('balanced')">Balanced</div>
<div class="strat" onclick="set('power_save')">Power Save</div>
<div class="strat" onclick="set('performance')">Performance</div>
</div>
</div>
<script>function set(s){fetch('/api/proactive/energy/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({strategy:s})}).then(()=>location.reload())}
fetch('/api/proactive/energy/status').then(r=>r.json()).then(d=>{document.getElementById('fill').style.width=d.phone_battery+'%';document.getElementById('pct').textContent=d.phone_battery})</script>
</body></html>"""
