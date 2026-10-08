from flask import Blueprint, jsonify, request

gesture_bp = Blueprint("gesture_recognition", __name__)
_state = {
    "active": True,
    "last_gesture": None,
    "enabled_gestures": ["shake", "flip", "tap", "double_tap"],
}

GESTURES = {
    "shake": {"action": "SOS", "desc": "Agitar para emergencia"},
    "flip": {"action": "silence", "desc": "Voltear para silenciar"},
    "tap": {"action": "activate", "desc": "Tocar para activar"},
    "double_tap": {"action": "toggle", "desc": "Doble toque para cambiar"},
}


@gesture_bp.route("/api/embodiment/gesture/status")
def g_status():
    return jsonify(_state)


@gesture_bp.route("/api/embodiment/gesture/trigger", methods=["POST"])
def g_trigger():
    data = request.json or {}
    gesture = data.get("gesture", "tap")
    _state["last_gesture"] = gesture
    return jsonify({"ok": True, "action": GESTURES.get(gesture, {}).get("action")})


@gesture_bp.route("/api/embodiment/gesture/web")
def g_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Gesture Recognition</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.gestures{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;max-width:600px;margin:0 auto}
.gesture{background:#111;border:2px solid #333;border-radius:12px;padding:30px;text-align:center;cursor:pointer;transition:all .3s}
.gesture:hover{border-color:#00f0ff;transform:scale(1.05)}
.gesture .icon{font-size:40px;margin:10px 0}
.last{margin-top:30px;text-align:center}
.last .gesture-name{font-size:24px;color:#00ff88}
</style></head><body>
<h1 style="text-align:center">GESTURE RECOGNITION</h1>
<div class="gestures" id="gestures"></div>
<div class="last"><p>Last gesture:</p><div class="gesture-name" id="last">None</div></div>
<script>const gestures=[{n:'shake',i:'📱',d:'Emergency'},{n:'flip',i:'🔄',d:'Silence'},{n:'tap',i:'👆',d:'Activate'},{n:'double_tap',i:'✌',d:'Toggle'}];
const g=document.getElementById('gestures');
gestures.forEach(gest=>{const d=document.createElement('div');d.className='gesture';d.innerHTML=`<div class="icon">${gest.i}</div><h3>${gest.n}</h3><p>${gest.d}</p>`;d.onclick=()=>{fetch('/api/embodiment/gesture/trigger',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({gesture:gest.n})}).then(r=>r.json()).then(r=>{document.getElementById('last').textContent=gest.n+' -> '+r.action})};g.appendChild(d)});
</script></body></html>"""
