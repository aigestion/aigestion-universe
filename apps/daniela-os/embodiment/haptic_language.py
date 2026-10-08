from flask import Blueprint, jsonify, request

haptic_bp = Blueprint("haptic_language", __name__)
_patterns = {
    "urgent": {"vibrate": [200, 100, 200], "desc": "Urgente"},
    "gentle": {"vibrate": [100], "desc": "Suave"},
    "notification": {"vibrate": [50, 50, 50], "desc": "Notificacion"},
    "celebration": {"vibrate": [100, 50, 100, 50, 200], "desc": "Celebracion"},
    "heartbeat": {"vibrate": [100, 100, 100, 100], "desc": "Latido"},
}
_state = {"active": True, "current_pattern": "gentle"}


@haptic_bp.route("/api/embodiment/haptic/status")
def h_status():
    return jsonify(_state)


@haptic_bp.route("/api/embodiment/haptic/send", methods=["POST"])
def h_send():
    data = request.json or {}
    pattern = data.get("pattern", "gentle")
    _state["current_pattern"] = pattern
    return jsonify({"ok": True, "pattern": _patterns.get(pattern)})


@haptic_bp.route("/api/embodiment/haptic/web")
def h_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Haptic Language</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.patterns{display:flex;gap:15px;flex-wrap:wrap;justify-content:center}
.pattern{background:#111;border:2px solid #333;border-radius:12px;padding:25px;text-align:center;cursor:pointer;transition:all .3s;width:150px}
.pattern:hover{border-color:#00f0ff;transform:scale(1.05)}
.pattern.active{border-color:#00ff88;background:#00ff8811}
.viz{margin-top:30px;text-align:center}
.bar{display:inline-block;width:8px;background:#00f0ff;margin:0 2px;border-radius:4px;transition:height .1s}
</style></head><body>
<h1 style="text-align:center">HAPTIC LANGUAGE</h1>
<div class="patterns" id="patterns"></div>
<div class="viz" id="viz"></div>
<script>const patterns=[{n:'urgent',i:'🚨'},{n:'gentle',i:'👋'},{n:'notification',i:'🔔'},{n:'celebration',i:'🎉'},{n:'heartbeat',i:'💓'}];
const p=document.getElementById('patterns');
patterns.forEach(pat=>{const d=document.createElement('div');d.className='pattern';d.innerHTML=`<div style="font-size:30px">${pat.i}</div><p>${pat.n}</p>`;d.onclick=()=>{document.querySelectorAll('.pattern').forEach(x=>x.classList.remove('active'));d.classList.add('active');send(pat.n)};p.appendChild(d)});
function send(n){fetch('/api/embodiment/haptic/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pattern:n})}).then(r=>r.json()).then(d=>{const v=document.getElementById('viz');v.innerHTML='';if(d.pattern){d.pattern.vibrate.forEach(vib=>{const bar=document.createElement('div');bar.className='bar';bar.style.height=vib/2+'px';v.appendChild(bar)})}})}
</script></body></html>"""
