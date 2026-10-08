from flask import Blueprint, jsonify

dual_bp = Blueprint("dual_presence", __name__)
_state = {
    "pc": {"online": True, "syncing": False},
    "phone": {"online": False, "syncing": False},
    "unified": True,
}


@dual_bp.route("/api/ambient/dual/status")
def dual_status():
    return jsonify(_state)


@dual_bp.route("/api/ambient/dual/sync", methods=["POST"])
def dual_sync():
    _state["pc"]["syncing"] = True
    _state["phone"]["syncing"] = True
    return jsonify({"ok": True})


@dual_bp.route("/api/ambient/dual/web")
def dual_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Dual Presence</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;gap:40px}
.device{width:250px;height:350px;background:#111;border:2px solid #00f0ff33;border-radius:20px;padding:20px;text-align:center}
.device .icon{font-size:60px;margin:20px 0}
.link{font-size:40px;color:#00f0ff;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
</style></head><body>
<div class="device"><div class="icon">🖥</div><h3>PC</h3><p id="pc-status">Online</p></div>
<div class="link">⟷</div>
<div class="device"><div class="icon">📱</div><h3>Phone</h3><p id="phone-status">Offline</p></div>
<script>setInterval(()=>{fetch('/api/ambient/dual/status').then(r=>r.json()).then(d=>{document.getElementById('pc-status').textContent=d.pc.online?'Online':'Offline';document.getElementById('phone-status').textContent=d.phone.online?'Online':'Offline'})},5000)</script>
</body></html>"""
