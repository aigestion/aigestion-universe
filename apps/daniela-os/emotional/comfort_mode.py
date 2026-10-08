from flask import Blueprint, jsonify

comfort_bp = Blueprint("comfort_mode", __name__)
_state = {"active": False, "level": "low", "notifications": "minimal", "tone": "soft"}


@comfort_bp.route("/api/emotional/comfort/status")
def c_status():
    return jsonify(_state)


@comfort_bp.route("/api/emotional/comfort/toggle", methods=["POST"])
def c_toggle():
    _state["active"] = not _state["active"]
    return jsonify({"ok": True, "active": _state["active"]})


@comfort_bp.route("/api/emotional/comfort/web")
def c_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Comfort Mode</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.comfort{text-align:center}
.cozy{width:300px;height:300px;border-radius:50%;border:4px solid #333;display:flex;align-items:center;justify-content:center;font-size:80px;transition:all 1s}
.cozy.active{border-color:#6644ff;background:#6644ff22;box-shadow:0 0 80px #6644ff44}
.btn{margin-top:30px;padding:15px 30px;border-radius:30px;border:2px solid #6644ff;background:#6644ff22;color:#6644ff;font-size:16px;cursor:pointer}
</style></head><body>
<div class="comfort">
<h2>COMFORT MODE</h2>
<div class="cozy" id="cozy">🌙</div>
<button class="btn" id="btn" onclick="toggle()">Activate</button>
</div>
<script>let active=false;
function toggle(){active=!active;fetch('/api/emotional/comfort/toggle',{method:'POST'}).then(r=>r.json()).then(d=>{document.getElementById('cozy').className='cozy '+(d.active?'active':'');document.getElementById('btn').textContent=d.active?'Deactivate':'Activate';document.getElementById('cozy').textContent=d.active?'☕':'🌙'})}
</script></body></html>"""
