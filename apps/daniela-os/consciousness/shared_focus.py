import time

from flask import Blueprint, jsonify

focus_bp = Blueprint("shared_focus", __name__)
_state = {"active": False, "since": None, "devices": [], "intensity": 0}


@focus_bp.route("/api/consciousness/focus/status")
def f_status():
    return jsonify(_state)


@focus_bp.route("/api/consciousness/focus/toggle", methods=["POST"])
def f_toggle():
    _state["active"] = not _state["active"]
    _state["since"] = time.time() if _state["active"] else None
    _state["devices"] = ["pc", "phone"] if _state["active"] else []
    _state["intensity"] = 80 if _state["active"] else 0
    return jsonify({"ok": True, "active": _state["active"]})


@focus_bp.route("/api/consciousness/focus/web")
def f_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Shared Focus</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.focus-container{text-align:center}
.ring{width:250px;height:250px;border-radius:50%;border:4px solid #333;display:flex;align-items:center;justify-content:center;transition:all 1s;margin:0 auto}
.ring.active{border-color:#00ff88;box-shadow:0 0 80px #00ff8844}
.ring .timer{font-size:48px;font-weight:bold}
.btn{margin-top:30px;padding:15px 40px;border-radius:30px;border:2px solid #00f0ff;background:#00f0ff22;color:#00f0ff;font-size:18px;cursor:pointer;font-family:monospace}
.btn.active{background:#00ff8822;border-color:#00ff88;color:#00ff88}
</style></head><body>
<div class="focus-container">
<div class="ring" id="ring"><div class="timer" id="timer">00:00</div></div>
<button class="btn" id="btn" onclick="toggle()">Activate Focus</button>
</div>
<script>let active=false,started=0;
function toggle(){active=!active;fetch('/api/consciousness/focus/toggle',{method:'POST'}).then(r=>r.json()).then(d=>{document.getElementById('ring').className='ring '+(d.active?'active':'');document.getElementById('btn').className='btn '+(d.active?'active':'');document.getElementById('btn').textContent=d.active?'Deactivate':'Activate Focus';if(d.active)started=Date.now()})}
setInterval(()=>{if(active){const s=Math.floor((Date.now()-started)/1000);const m=Math.floor(s/60).toString().padStart(2,'0');const sec=(s%60).toString().padStart(2,'0');document.getElementById('timer').textContent=m+':'+sec}},1000)
</script></body></html>"""
