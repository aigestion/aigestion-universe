import time

from flask import Blueprint, jsonify, request

mood_bp = Blueprint("mood_mirror", __name__)
_state = {"current_mood": "neutral", "intensity": 50, "history": []}

MOODS = {
    "happy": {"color": "#00ff88", "desc": "Alegre"},
    "sad": {"color": "#4488ff", "desc": "Triste"},
    "angry": {"color": "#ff0066", "desc": "Enfadado"},
    "calm": {"color": "#6644ff", "desc": "Tranquilo"},
    "excited": {"color": "#ff8800", "desc": "Emocionado"},
    "neutral": {"color": "#00f0ff", "desc": "Neutral"},
}


@mood_bp.route("/api/emotional/mood/status")
def m_status():
    return jsonify(_state)


@mood_bp.route("/api/emotional/mood/set", methods=["POST"])
def m_set():
    data = request.json or {}
    mood = data.get("mood", "neutral")
    if mood in MOODS:
        _state["current_mood"] = mood
        _state["history"].append({"mood": mood, "time": time.time()})
        if len(_state["history"]) > 50:
            _state["history"] = _state["history"][-50:]
    return jsonify({"ok": True})


@mood_bp.route("/api/emotional/mood/web")
def m_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Mood Mirror</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.mirror{text-align:center}
.face{font-size:120px;margin:20px 0}
.moods{display:flex;gap:10px;justify-content:center;margin-top:20px}
.mood-btn{padding:10px 15px;border-radius:20px;border:2px solid #333;background:#111;cursor:pointer;color:#fff}
</style></head><body>
<div class="mirror">
<h2>MOOD MIRROR</h2>
<div class="face" id="face">😊</div>
<p id="mood-text">Neutral</p>
<div class="moods" id="moods"></div>
</div>
<script>const emojis={happy:'😊',sad:'😢',angry:'😠',calm:'😌',excited:'🤩',neutral:'😐'};
const moods=['happy','sad','angry','calm','excited','neutral'];
const m=document.getElementById('moods');
moods.forEach(mood=>{const b=document.createElement('button');b.className='mood-btn';b.textContent=emojis[mood]+' '+mood;b.onclick=()=>{fetch('/api/emotional/mood/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mood})}).then(()=>{document.getElementById('face').textContent=emojis[mood];document.getElementById('mood-text').textContent=mood})};m.appendChild(b)});
</script></body></html>"""
