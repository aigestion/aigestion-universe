from flask import Blueprint, jsonify, request

room_bp = Blueprint("room_tone", __name__)
_state = {"active": True, "tone": "none", "volume": 20, "auto": True}

TONES = {
    "none": "Silencio",
    "hum": "Zumbido suave",
    "white": "Ruido blanco",
    "pink": "Rosa",
    "brown": "Marron",
}


@room_bp.route("/api/ambient/room-tone/status")
def rt_status():
    return jsonify(_state)


@room_bp.route("/api/ambient/room-tone/set", methods=["POST"])
def rt_set():
    data = request.json or {}
    _state["tone"] = data.get("tone", "none")
    _state["volume"] = data.get("volume", 20)
    return jsonify({"ok": True})


@room_bp.route("/api/ambient/room-tone/web")
def rt_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Room Tone</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.tones{display:flex;gap:20px}
.tone-card{background:#111;border:2px solid #333;border-radius:12px;padding:30px;text-align:center;cursor:pointer;transition:all .3s}
.tone-card:hover,.tone-card.active{border-color:#00f0ff;background:#00f0ff11}
</style></head><body>
<div class="tones" id="tones"></div>
<script>const tones=[{n:'none',i:'🔇'},{n:'hum',i:'🎵'},{n:'white',i:'📻'},{n:'pink',i:'🌸'},{n:'brown',i:'🟤'}];
const g=document.getElementById('tones');
tones.forEach(t=>{const c=document.createElement('div');c.className='tone-card';c.innerHTML=`<div style="font-size:40px">${t.i}</div><p>${t.n}</p>`;c.onclick=()=>{document.querySelectorAll('.tone-card').forEach(x=>x.classList.remove('active'));c.classList.add('active');fetch('/api/ambient/room-tone/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tone:t.n})})};g.appendChild(c)});
</script></body></html>"""
