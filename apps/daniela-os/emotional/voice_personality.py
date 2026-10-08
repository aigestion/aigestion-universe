from flask import Blueprint, jsonify, request

voice_personality_bp = Blueprint("voice_personality", __name__)
_state = {"style": "warm", "speed": 1.0, "pitch": 1.0, "energy": "medium"}

STYLES = {
    "warm": {"speed": 1.0, "pitch": 1.0, "desc": "Cálida y amigable"},
    "professional": {"speed": 1.1, "pitch": 0.9, "desc": "Formal y clara"},
    "casual": {"speed": 0.9, "pitch": 1.1, "desc": "Relajada"},
    "dramatic": {"speed": 0.8, "pitch": 1.2, "desc": "Teatral"},
}


@voice_personality_bp.route("/api/emotional/voice/status")
def v_status():
    return jsonify(_state)


@voice_personality_bp.route("/api/emotional/voice/set", methods=["POST"])
def v_set():
    data = request.json or {}
    style = data.get("style", "warm")
    if style in STYLES:
        _state["style"] = style
        _state["speed"] = STYLES[style]["speed"]
        _state["pitch"] = STYLES[style]["pitch"]
    return jsonify({"ok": True})


@voice_personality_bp.route("/api/emotional/voice/web")
def v_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Voice Personality</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.voice{text-align:center}
.avatar{width:150px;height:150px;border-radius:50%;background:radial-gradient(circle,#00f0ff,#001a33);margin:0 auto 20px;display:flex;align-items:center;justify-content:center;font-size:60px;animation:breathe 3s infinite}
@keyframes breathe{0%,100%{box-shadow:0 0 20px #00f0ff44}50%{box-shadow:0 0 60px #00f0ff88}}
.styles{display:flex;gap:10px;margin-top:20px}
.style-btn{padding:10px 20px;border:2px solid #333;border-radius:10px;background:#111;cursor:pointer;color:#fff}
.style-btn.active{border-color:#00ff88;background:#00ff8822}
</style></head><body>
<div class="voice">
<h2>VOICE PERSONALITY</h2>
<div class="avatar">🎙</div>
<p>Current: <strong id="current">warm</strong></p>
<div class="styles" id="styles"></div>
</div>
<script>const styles=['warm','professional','casual','dramatic'];
const s=document.getElementById('styles');
styles.forEach(st=>{const b=document.createElement('button');b.className='style-btn';b.textContent=st;b.onclick=()=>{fetch('/api/emotional/voice/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({style:st})}).then(()=>{document.getElementById('current').textContent=st;document.querySelectorAll('.style-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active')})};s.appendChild(b)})</script>
</body></html>"""
