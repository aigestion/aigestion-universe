from flask import Blueprint, jsonify, request

aura_bp = Blueprint("aura", __name__)
_state = {"active": True, "color": "#00f0ff", "mood": "neutral", "brightness": 50, "mode": "auto"}

MOOD_COLORS = {
    "neutral": "#00f0ff",
    "happy": "#00ff88",
    "sad": "#4488ff",
    "angry": "#ff0066",
    "calm": "#6644ff",
    "excited": "#ff8800",
    "focus": "#00ff44",
    "sleepy": "#330066",
}


@aura_bp.route("/api/ambient/aura/status")
def aura_status():
    return jsonify(_state)


@aura_bp.route("/api/ambient/aura/set", methods=["POST"])
def aura_set():
    data = request.json or {}
    if "color" in data:
        _state["color"] = data["color"]
    if "mood" in data:
        _state["mood"] = data["mood"]
        _state["color"] = MOOD_COLORS.get(data["mood"], _state["color"])
    _state["brightness"] = data.get("brightness", _state["brightness"])
    return jsonify({"ok": True})


@aura_bp.route("/api/ambient/aura/web")
def aura_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Aura Projection</title>
<style>body{margin:0;background:#0a0a0f;display:flex;justify-content:center;align-items:center;height:100vh;font-family:monospace}
.aura{width:400px;height:400px;border-radius:50%;transition:all 2s;filter:blur(40px)}
.moods{position:fixed;bottom:40px;display:flex;gap:10px}
.mood-btn{padding:10px 20px;border-radius:20px;border:2px solid #333;background:#111;color:#fff;cursor:pointer;font-family:monospace}
</style></head><body>
<div class="aura" id="aura" style="background:#00f0ff"></div>
<div class="moods" id="moods"></div>
<script>const moods=['neutral','happy','sad','angry','calm','excited','focus','sleepy'];
const colors={neutral:'#00f0ff',happy:'#00ff88',sad:'#4488ff',angry:'#ff0066',calm:'#6644ff',excited:'#ff8800',focus:'#00ff44',sleepy:'#330066'};
const m=document.getElementById('moods');
moods.forEach(mood=>{const b=document.createElement('button');b.className='mood-btn';b.textContent=mood;b.style.borderColor=colors[mood];b.onclick=()=>{document.getElementById('aura').style.background=colors[mood];document.getElementById('aura').style.boxShadow='0 0 100px '+colors[mood];fetch('/api/ambient/aura/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mood})})};m.appendChild(b)})
</script></body></html>"""
