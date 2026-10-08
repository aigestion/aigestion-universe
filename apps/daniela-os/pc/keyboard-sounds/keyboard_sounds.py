"""
System 48: Keyboard Sound Engine
Custom keyboard sounds and typing feedback
"""

import json
from pathlib import Path

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


SOUND_PACKS = [
    {
        "id": "mechanical",
        "name": "Mechanical Blue",
        "description": "Crisp blue switch",
        "pitch": 800,
        "decay": 0.08,
        "volume": 0.6,
    },
    {
        "id": "mechanical_red",
        "name": "Mechanical Red",
        "description": "Smooth red switch",
        "pitch": 600,
        "decay": 0.12,
        "volume": 0.5,
    },
    {
        "id": "membrane",
        "name": "Membrane",
        "description": "Soft membrane",
        "pitch": 400,
        "decay": 0.15,
        "volume": 0.4,
    },
    {
        "id": "typewriter",
        "name": "Typewriter",
        "description": "Classic typewriter",
        "pitch": 1200,
        "decay": 0.06,
        "volume": 0.8,
    },
    {
        "id": "click",
        "name": "Click",
        "description": "Simple click",
        "pitch": 1000,
        "decay": 0.05,
        "volume": 0.3,
    },
    {
        "id": "thock",
        "name": "Thock",
        "description": "Deep thock",
        "pitch": 300,
        "decay": 0.2,
        "volume": 0.7,
    },
    {
        "id": "silent",
        "name": "Silent",
        "description": "Near silent",
        "pitch": 500,
        "decay": 0.1,
        "volume": 0.15,
    },
    {
        "id": "spacebar",
        "name": "Spacebar Thump",
        "description": "Heavy spacebar",
        "pitch": 200,
        "decay": 0.25,
        "volume": 0.9,
    },
]


@app.route("/")
def index():
    return KB_HTML


@app.route("/api/kb/sounds")
def sounds():
    return jsonify({"packs": SOUND_PACKS})


@app.route("/api/kb/active")
def active():
    settings = load_json(DATA_DIR / "kb_settings.json", {"active_pack": "mechanical"})
    return jsonify(settings)


@app.route("/api/kb/set", methods=["POST"])
def set_pack():
    data = request.json or {}
    settings = {"active_pack": data.get("pack", "mechanical")}
    save_json(DATA_DIR / "kb_settings.json", settings)
    return jsonify({"ok": True})


KB_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Keyboard Sound Engine</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.packs{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-bottom:20px}
.pack{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;cursor:pointer;transition:all 0.3s}
.pack:hover{border-color:#00f0ff}
.pack.active{border-color:#ff0055;box-shadow:0 0 15px rgba(255,0,85,0.2)}
.pack-name{font-family:'Orbitron',monospace;font-size:12px;color:#00f0ff}
.pack-desc{font-size:10px;color:#64748b;margin-top:4px}
.pack-params{display:flex;gap:8px;margin-top:8px}
.param{font-size:9px;color:#94a3b8;background:rgba(0,240,255,0.05);padding:2px 6px;border-radius:4px}
.typing-area{background:rgba(3,8,20,0.8);border:1px solid rgba(255,0,85,0.2);border-radius:12px;padding:16px;margin-top:16px}
.typing-input{width:100%;min-height:120px;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:12px;border-radius:8px;font-family:'Share Tech Mono',monospace;font-size:14px;resize:vertical}
.visual{display:flex;gap:3px;margin-top:12px;flex-wrap:wrap}
.key{width:30px;height:30px;background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.12);border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:10px;color:#64748b;transition:all 0.1s}
.key.active{background:rgba(0,240,255,0.2);border-color:#00f0ff;color:#00f0ff;transform:scale(0.9)}
.stats{display:flex;gap:12px;margin-top:12px}
.stat{font-size:11px;color:#64748b}
.stat span{color:#00f0ff;font-family:'Share Tech Mono',monospace}
</style></head><body>
<h1>KEYBOARD SOUND ENGINE</h1>
<div class="packs" id="packs"></div>
<div class="typing-area">
  <textarea class="typing-input" id="input" placeholder="Type here to test keyboard sounds..."></textarea>
  <div class="visual" id="visual"></div>
  <div class="stats">
    <div class="stat">Keypresses: <span id="count">0</span></div>
    <div class="stat">WPM: <span id="wpm">0</span></div>
    <div class="stat">Active: <span id="activePack">-</span></div>
  </div>
</div>
<script>
let currentPack=null;let keyCount=0;let startTime=null;let audioCtx;
async function load(){
  const r=await(await fetch('/api/kb/sounds')).json();
  const a=await(await fetch('/api/kb/active')).json();
  currentPack=a.active_pack||'mechanical';
  document.getElementById('activePack').textContent=currentPack;
  const packs=SOUND_PACKS||(r.packs||[]);
  document.getElementById('packs').innerHTML=(r.packs||[]).map(p=>
    '<div class="pack'+(p.id===currentPack?' active':'')+'" onclick="selectPack(\''+p.id+'\')">'+
    '<div class="pack-name">'+p.name+'</div><div class="pack-desc">'+p.description+'</div>'+
    '<div class="pack-params"><span class="param">P:'+p.pitch+'</span><span class="param">D:'+p.decay+'</span><span class="param">V:'+p.volume+'</span></div></div>'
  ).join('');
  initVisual();
}
async function selectPack(id){
  currentPack=id;document.getElementById('activePack').textContent=id;
  await fetch('/api/kb/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pack:id})});
  load();
}
function initVisual(){
  const el=document.getElementById('visual');
  el.innerHTML='';
  const keys='QWERTYUIOPASDFGHJKLZXCVBNM'.split('');
  keys.forEach(k=>{const d=document.createElement('div');d.className='key';d.textContent=k;d.id='k-'+k;el.appendChild(d)});
}
document.getElementById('input').addEventListener('keydown',e=>{
  if(!audioCtx)audioCtx=new(window.AudioContext||window.webkitAudioContext)();
  const osc=audioCtx.createOscillator();const gain=audioCtx.createGain();
  osc.connect(gain);gain.connect(audioCtx.destination);
  osc.frequency.value=600+Math.random()*800;
  osc.type='sine';gain.gain.value=0.1;
  gain.gain.exponentialRampToValueAtTime(0.001,audioCtx.currentTime+0.1);
  osc.start();osc.stop(audioCtx.currentTime+0.1);
  const kEl=document.getElementById('k-'+e.key.toUpperCase());
  if(kEl){kEl.classList.add('active');setTimeout(()=>kEl.classList.remove('active'),100)}
  keyCount++;document.getElementById('count').textContent=keyCount;
  if(!startTime)startTime=Date.now();
  const elapsed=(Date.now()-startTime)/60000;
  if(elapsed>0)document.getElementById('wpm').textContent=Math.round(keyCount/5/elapsed);
});
let SOUND_PACKS=null;
fetch('/api/kb/sounds').then(r=>r.json()).then(d=>SOUND_PACKS=d.packs);
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 48] Keyboard Sound Engine starting on port 5058...")
    app.run(host="0.0.0.0", port=5058, debug=False)
