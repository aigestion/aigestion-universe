import time

from flask import Blueprint, jsonify

smart_interrupt_bp = Blueprint("smart_interruptions", __name__)
_state = {"focus_mode": False, "flow_detected": False, "last_interruption": 0, "cooldown_min": 5}


@smart_interrupt_bp.route("/api/proactive/interrupt/status")
def si_status():
    return jsonify(_state)


@smart_interrupt_bp.route("/api/proactive/interrupt/check", methods=["POST"])
def si_check():
    can_interrupt = True
    reason = ""
    if _state["flow_detected"]:
        can_interrupt = False
        reason = "Flow state detected"
    elif time.time() - _state["last_interruption"] < _state["cooldown_min"] * 60:
        can_interrupt = False
        reason = "Cooldown active"
    return jsonify({"can_interrupt": can_interrupt, "reason": reason})


@smart_interrupt_bp.route("/api/proactive/interrupt/web")
def si_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Smart Interruptions</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.status{text-align:center}
.flow-indicator{width:200px;height:200px;border-radius:50%;border:4px solid #333;display:flex;align-items:center;justify-content:center;margin:20px auto;transition:all .5s}
.flow-indicator.flow{border-color:#00ff88;background:#00ff8822;box-shadow:0 0 60px #00ff8844}
.flow-indicator.normal{border-color:#00f0ff;background:#00f0ff11}
</style></head><body>
<div class="status">
<h2>SMART INTERRUPTIONS</h2>
<div class="flow-indicator" id="flow"><span id="icon">🔔</span></div>
<p id="status-text">Normal mode</p>
<button onclick="toggle()" style="padding:10px 20px;background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;border-radius:8px;cursor:pointer">Toggle Flow Detection</button>
</div>
<script>let flow=false;
function toggle(){flow=!flow;fetch('/api/proactive/interrupt/status').then(r=>r.json()).then(d=>{document.getElementById('flow').className='flow-indicator '+(flow?'flow':'normal');document.getElementById('icon').textContent=flow?'🧘':'🔔';document.getElementById('status-text').textContent=flow?'Flow state - No interruptions':'Normal mode'})}
</script></body></html>"""
