import time

from flask import Blueprint, jsonify, request

pet_bp = Blueprint("pet", __name__)
_state = {
    "name": "Dani",
    "species": "hologram",
    "mood": "happy",
    "energy": 100,
    "hunger": 0,
    "happiness": 80,
    "position": {"x": 100, "y": 200},
    "state": "idle",
    "last_interaction": time.time(),
    "birth": time.time(),
}

MOODS = {
    "happy": {"color": "#00ff88", "emoji": "😊"},
    "sleepy": {"color": "#6644ff", "emoji": "😴"},
    "hungry": {"color": "#ff8800", "emoji": "🍕"},
    "excited": {"color": "#ff0066", "emoji": "🎉"},
    "sad": {"color": "#4488ff", "emoji": "😢"},
}


@pet_bp.route("/api/ambient/pet/status")
def pet_status():
    elapsed = time.time() - _state["last_interaction"]
    if elapsed > 3600:
        _state["happiness"] = max(0, _state["happiness"] - 1)
    if elapsed > 7200:
        _state["mood"] = "sleepy"
    return jsonify(_state)


@pet_bp.route("/api/ambient/pet/interact", methods=["POST"])
def pet_interact():
    data = request.json or {}
    action = data.get("action", "pet")
    _state["last_interaction"] = time.time()
    if action == "pet":
        _state["happiness"] = min(100, _state["happiness"] + 10)
        _state["mood"] = "happy"
    elif action == "feed":
        _state["hunger"] = 0
        _state["energy"] = min(100, _state["energy"] + 20)
    elif action == "play":
        _state["happiness"] = min(100, _state["happiness"] + 15)
        _state["energy"] = max(0, _state["energy"] - 10)
    return jsonify({"ok": True, "mood": _state["mood"]})


@pet_bp.route("/api/ambient/pet/move", methods=["POST"])
def pet_move():
    data = request.json or {}
    _state["position"] = {"x": data.get("x", 100), "y": data.get("y", 200)}
    return jsonify({"ok": True})


@pet_bp.route("/api/ambient/pet/web")
def pet_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Desktop Pet</title>
<style>body{margin:0;background:#0a0a0f;overflow:hidden;font-family:monospace;color:#00f0ff}
.pet{position:absolute;width:80px;height:80px;border-radius:50%;cursor:move;transition:all .3s;display:flex;align-items:center;justify-content:center;font-size:40px}
.pet:hover{transform:scale(1.2)}
.hud{position:fixed;top:20px;right:20px;background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;font-size:12px}
.hud p{margin:5px 0} .bar{height:8px;background:#222;border-radius:4px;overflow:hidden}
.bar-fill{height:100%;transition:width .5s;border-radius:4px}
.controls{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);display:flex;gap:10px}
.btn{background:#111;border:1px solid #00f0ff33;color:#00f0ff;padding:10px 20px;border-radius:8px;cursor:pointer;font-family:monospace}
.btn:hover{background:#00f0ff22;border-color:#00f0ff}
</style></head><body>
<div class="pet" id="pet" style="left:100px;top:200px">🦊</div>
<div class="hud" id="hud"></div>
<div class="controls">
<button class="btn" onclick="act('pet')">Pet</button>
<button class="btn" onclick="act('feed')">Feed</button>
<button class="btn" onclick="act('play')">Play</button>
</div>
<script>const pet=document.getElementById('pet');
let dragging=false,off={x:0,y:0};
pet.onmousedown=e=>{dragging=true;off={x:e.clientX-pet.offsetLeft,y:e.clientY-pet.offsetTop}};
document.onmousemove=e=>{if(dragging){pet.style.left=(e.clientX-off.x)+'px';pet.style.top=(e.clientY-off.y)+'px'}};
document.onmouseup=()=>{if(dragging){dragging=false;fetch('/api/ambient/pet/move',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({x:parseInt(pet.style.left),y:parseInt(pet.style.top)})})}};
function act(a){fetch('/api/ambient/pet/interact',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:a})}).then(r=>r.json()).then(d=>update(d.mood))}
function update(m){const colors={happy:'#00ff88',sleepy:'#6644ff',hungry:'#ff8800',excited:'#ff0066',sad:'#4488ff'};pet.style.background=radial-gradient(circle,${colors[m]||'#00f0ff'},transparent);pet.style.boxShadow='0 0 30px '+colors[m]}
setInterval(()=>{fetch('/api/ambient/pet/status').then(r=>r.json()).then(d=>{document.getElementById('hud').innerHTML=`<p>Mood: ${d.mood}</p><p>Energy: <div class="bar"><div class="bar-fill" style="width:${d.energy}%;background:#00ff88"></div></div></p><p>Happy: <div class="bar"><div class="bar-fill" style="width:${d.happiness}%;background:#ff0066"></div></div></p>`})},3000)
</script></body></html>"""
