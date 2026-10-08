from flask import Blueprint, jsonify, request

sounds_bp = Blueprint("sounds", __name__)
_state = {"active": True, "current": "none", "volume": 30, "auto": True}

SCENES = {
    "rain": {"file": "rain.mp3", "desc": "Lluvia suave"},
    "forest": {"file": "forest.mp3", "desc": "Bosque con pajaros"},
    "ocean": {"file": "ocean.mp3", "desc": "Olas del mar"},
    "cafe": {"file": "cafe.mp3", "desc": "Cafe ambiental"},
    "fireplace": {"file": "fireplace.mp3", "desc": "Chimenea crepitante"},
    "wind": {"file": "wind.mp3", "desc": "Viento suave"},
    "night": {"file": "night.mp3", "desc": "Noche con grillos"},
    "keyboard": {"file": "keyboard.mp3", "desc": "Teclado mecanico"},
}


@sounds_bp.route("/api/ambient/sounds/status")
def snd_status():
    return jsonify(_state)


@sounds_bp.route("/api/ambient/sounds/set", methods=["POST"])
def snd_set():
    data = request.json or {}
    _state["current"] = data.get("scene", "none")
    _state["volume"] = data.get("volume", 30)
    return jsonify({"ok": True})


@sounds_bp.route("/api/ambient/sounds/list")
def snd_list():
    return jsonify(SCENES)


@sounds_bp.route("/api/ambient/sounds/web")
def snd_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Ambient Sounds</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
h1{text-align:center} .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;max-width:800px;margin:40px auto}
.card{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:30px;text-align:center;cursor:pointer;transition:all .3s}
.card:hover,.card.active{background:#00f0ff11;border-color:#00f0ff;transform:scale(1.05)}
.card .icon{font-size:40px;margin-bottom:10px} .card h3{margin:0;font-size:14px}
.vol{text-align:center;margin:20px} input[type=range]{width:300px}
</style></head><body>
<h1>AMBIENT SOUNDSCAPES</h1>
<div class="grid" id="grid"></div>
<div class="vol"><input type="range" min="0" max="100" value="30" id="vol" oninput="setVol(this.value)"><p>Volumen: <span id="vv">30</span>%</p></div>
<script>const scenes=[{n:'rain',i:'🌧',d:'Lluvia'},{n:'forest',i:'🌲',d:'Bosque'},{n:'ocean',i:'🌊',d:'Mar'},{n:'cafe',i:'☕',d:'Cafe'},{n:'fireplace',i:'🔥',d:'Chimenea'},{n:'wind',i:'💨',d:'Viento'},{n:'night',i:'🌙',d:'Noche'},{n:'keyboard',i:'⌨',d:'Teclado'}];
const g=document.getElementById('grid');
scenes.forEach(s=>{const c=document.createElement('div');c.className='card';c.innerHTML=`<div class="icon">${s.i}</div><h3>${s.d}</h3>`;c.onclick=()=>{document.querySelectorAll('.card').forEach(x=>x.classList.remove('active'));c.classList.add('active');fetch('/api/ambient/sounds/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene:s.n})})};g.appendChild(c)});
function setVol(v){document.getElementById('vv').textContent=v;fetch('/api/ambient/sounds/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene:'current',volume:parseInt(v)})})}
</script></body></html>"""
