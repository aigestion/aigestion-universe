from flask import Blueprint, jsonify, request

voice_engine_bp = Blueprint("voice_engine", __name__)
_state = {"provider": "edge-tts", "voice": "es-ES-ElviraNeural", "speed": 1.0, "mood": "neutral"}

@voice_engine_bp.route("/api/hermes/voice/status")
def ve_status():
    return jsonify(_state)

@voice_engine_bp.route("/api/hermes/voice/set", methods=["POST"])
def ve_set():
    data = request.json or {}
    for k, v in data.items():
        if k in _state:
            _state[k] = v
    return jsonify({"ok": True})

@voice_engine_bp.route("/api/hermes/voice/speak", methods=["POST"])
def ve_speak():
    data = request.json or {}
    text = data.get("text", "")
    return jsonify({"ok": True, "text": text, "voice": _state["voice"]})

@voice_engine_bp.route("/api/hermes/voice/web")
def ve_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Voice Engine</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.voice{text-align:center}
.avatar{width:150px;height:150px;border-radius:50%;background:linear-gradient(135deg,#00f0ff,#ff0066);margin:0 auto 20px;display:flex;align-items:center;justify-content:center;font-size:60px}
textarea{width:300px;height:80px;background:#111;border:1px solid #333;color:#00f0ff;padding:10px;border-radius:8px;font-family:monospace;margin:10px 0}
button{padding:10px 20px;background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;border-radius:8px;cursor:pointer}
select{background:#111;border:1px solid #333;color:#00f0ff;padding:8px;border-radius:6px;margin:5px}
</style></head><body>
<div class="voice"><h2>VOICE ENGINE</h2><div class="avatar">🎙</div>
<select id="voice" onchange="setVoice()"><option>es-ES-ElviraNeural</option><option>es-ES-AlvaroNeural</option><option>en-US-JennyNeural</option><option>en-US-GuyNeural</option></select>
<textarea id="text" placeholder="Type something to speak..."></textarea><br>
<button onclick="speak()">Speak</button></div>
<script>function setVoice(){fetch('/api/hermes/voice/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({voice:document.getElementById('voice').value})})}
function speak(){fetch('/api/hermes/voice/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:document.getElementById('text').value})}).then(r=>r.json()).then(d=>alert('Speaking: '+d.text))}</script></body></html>"""
