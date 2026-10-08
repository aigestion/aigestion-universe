"""
System 25: Desktop Pets 2.0
Digital pets that react to your productivity
"""

import json
import time
from pathlib import Path

import psutil
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.route("/")
def index():
    return PETS_HTML


@app.route("/api/pets/list")
def list_pets():
    state = load_json(DATA_DIR / "pets.json", {"pets": []})
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    for pet in state["pets"]:
        health = 100 - (cpu * 0.3 + mem * 0.2)
        if health > 80:
            pet["mood"] = "happy"
            pet["behavior"] = "play"
        elif health > 60:
            pet["mood"] = "content"
            pet["behavior"] = "idle"
        elif health > 40:
            pet["mood"] = "tired"
            pet["behavior"] = "sleep"
        else:
            pet["mood"] = "stressed"
            pet["behavior"] = "panic"
        pet["energy"] = min(100, pet.get("energy", 50) + (5 if health > 60 else -2))
        pet["happiness"] = min(
            100, max(0, pet.get("happiness", 50) + (2 if pet["mood"] == "happy" else -1))
        )
    save_json(DATA_DIR / "pets.json", state)
    return jsonify(state)


@app.route("/api/pets/create", methods=["POST"])
def create_pet():
    data = request.json or {}
    state = load_json(DATA_DIR / "pets.json", {"pets": []})
    pet = {
        "id": int(time.time()),
        "name": data.get("name", "Pixie"),
        "type": data.get("type", "cat"),
        "x": 400,
        "y": 300,
        "energy": 80,
        "happiness": 70,
        "mood": "happy",
        "behavior": "idle",
        "created": time.time(),
    }
    state["pets"].append(pet)
    save_json(DATA_DIR / "pets.json", state)
    return jsonify({"ok": True})


@app.route("/api/pets/feed", methods=["POST"])
def feed_pet():
    data = request.json or {}
    state = load_json(DATA_DIR / "pets.json", {"pets": []})
    for pet in state["pets"]:
        if pet["id"] == data.get("id"):
            pet["energy"] = min(100, pet.get("energy", 50) + 20)
            pet["happiness"] = min(100, pet.get("happiness", 50) + 10)
            break
    save_json(DATA_DIR / "pets.json", state)
    return jsonify({"ok": True})


@app.route("/api/pets/pet", methods=["POST"])
def pet_animal():
    data = request.json or {}
    state = load_json(DATA_DIR / "pets.json", {"pets": []})
    for pet in state["pets"]:
        if pet["id"] == data.get("id"):
            pet["happiness"] = min(100, pet.get("happiness", 50) + 15)
            break
    save_json(DATA_DIR / "pets.json", state)
    return jsonify({"ok": True})


@app.route("/api/pets/delete", methods=["POST"])
def delete_pet():
    data = request.json or {}
    state = load_json(DATA_DIR / "pets.json", {"pets": []})
    state["pets"] = [p for p in state["pets"] if p["id"] != data.get("id")]
    save_json(DATA_DIR / "pets.json", state)
    return jsonify({"ok": True})


PETS_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Desktop Pets 2.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100vw;height:100vh;overflow:hidden;background:#0a0a1a;font-family:'Rajdhani',sans-serif}
canvas{position:fixed;top:0;left:0;z-index:0}
#ui{position:fixed;top:20px;left:20px;z-index:10}
.btn{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.3);color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px;margin:4px}
.btn:hover{background:rgba(0,240,255,0.15)}
.pet-info{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.2);border-radius:8px;padding:10px;margin:4px;font-size:11px;font-family:'Share Tech Mono',monospace}
#controls{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:10;display:flex;gap:8px}
</style></head><body>
<canvas id="c"></canvas>
<div id="ui"></div>
<div id="controls">
  <button class="btn" onclick="createPet()">+ New Pet</button>
</div>
<script>
const canvas=document.getElementById('c');const ctx=canvas.getContext('2d');
canvas.width=innerWidth;canvas.height=innerHeight;
window.onresize=()=>{canvas.width=innerWidth;canvas.height=innerHeight};

let pets=[];let time=0;
const petEmojis={cat:'🐱',dog:'🐶',bunny:'🐰',bird:'🐦',fox:'🦊',dragon:'🐉'};

async function loadPets(){const r=await(await fetch('/api/pets/list')).json();pets=r.pets||[];renderUI()}
async function createPet(){const name=prompt('Pet name:');if(!name)return;await fetch('/api/pets/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,type:'cat'})});loadPets()}
async function feedPet(id){await fetch('/api/pets/feed',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});loadPets()}
async function petAnimal(id){await fetch('/api/pets/pet',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});loadPets()}
async function deletePet(id){await fetch('/api/pets/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});loadPets()}

function renderUI(){
  document.getElementById('ui').innerHTML=pets.map(p=>
    '<div class="pet-info">'+petEmojis[p.type||'cat']+' '+p.name+
    ' <span style="color:'+(p.mood==='happy'?'#22c55e':p.mood==='stressed'?'#ef4444':'#f59e0b')+'">'+p.mood+'</span>'+
    '<br>Energy: '+Math.round(p.energy)+'% | Happy: '+Math.round(p.happiness)+'%'+
    '<br><button class="btn" onclick="feedPet('+p.id+')">Feed</button>'+
    '<button class="btn" onclick="petAnimal('+p.id+')">Pet</button>'+
    '<button class="btn" style="border-color:#ff0055;color:#ff0055" onclick="deletePet('+p.id+')">X</button></div>'
  ).join('');
}

function draw(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  const grad=ctx.createLinearGradient(0,canvas.height-100,0,canvas.height);
  grad.addColorStop(0,'#0a0a1a');grad.addColorStop(1,'#1a1a2e');
  ctx.fillStyle=grad;ctx.fillRect(0,canvas.height-100,canvas.width,100);

  pets.forEach(p=>{
    p.x=p.x||200+Math.random()*(canvas.width-400);
    p.y=canvas.height-130;
    const bounce=Math.sin(time*2+p.id)*5;
    const size=30;
    ctx.font=size+'px serif';ctx.textAlign='center';
    ctx.fillText(petEmojis[p.type||'cat'],p.x,p.y+bounce);
    ctx.font='10px Share Tech Mono';ctx.fillStyle='#e2e8f0';
    ctx.fillText(p.name,p.x,p.y+20);
    if(p.mood==='happy'){ctx.fillStyle='rgba(34,197,94,0.3)';ctx.beginPath();ctx.arc(p.x,p.y-10,20,0,Math.PI*2);ctx.fill()}
    else if(p.mood==='stressed'){ctx.fillStyle='rgba(239,68,68,0.2)';ctx.beginPath();ctx.arc(p.x,p.y-10,25,0,Math.PI*2);ctx.fill()}
    p.x+=Math.sin(time+p.id)*0.5;
  });
  time+=0.02;requestAnimationFrame(draw);
}
loadPets();draw();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 25] Desktop Pets 2.0 starting on port 5035...")
    app.run(host="0.0.0.0", port=5035, debug=False)
