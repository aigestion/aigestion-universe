"""
System 36: Desktop Macros AI
Records and replays macro sequences that adapt to screen changes
"""

import json
import time
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


@app.route("/")
def index():
    return MACROS_HTML


@app.route("/api/macros/list")
def list_macros():
    return jsonify(load_json(DATA_DIR / "macros.json", {"macros": []}))


@app.route("/api/macros/save", methods=["POST"])
def save_macro():
    data = request.json or {}
    macros = load_json(DATA_DIR / "macros.json", {"macros": []})
    macro = {
        "id": int(time.time()),
        "name": data.get("name", f"Macro_{int(time.time())}"),
        "steps": data.get("steps", []),
        "created": time.time(),
        "runs": 0,
    }
    macros["macros"].append(macro)
    save_json(DATA_DIR / "macros.json", macros)
    return jsonify({"ok": True, "id": macro["id"]})


@app.route("/api/macros/run", methods=["POST"])
def run_macro():
    data = request.json or {}
    macros = load_json(DATA_DIR / "macros.json", {"macros": []})
    for m in macros["macros"]:
        if m["id"] == data.get("id"):
            m["runs"] = m.get("runs", 0) + 1
            m["last_run"] = time.time()
            break
    save_json(DATA_DIR / "macros.json", macros)
    return jsonify({"ok": True, "steps": len(m.get("steps", []))})


@app.route("/api/macros/delete", methods=["POST"])
def delete_macro():
    data = request.json or {}
    macros = load_json(DATA_DIR / "macros.json", {"macros": []})
    macros["macros"] = [m for m in macros["macros"] if m["id"] != data.get("id")]
    save_json(DATA_DIR / "macros.json", macros)
    return jsonify({"ok": True})


MACROS_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Desktop Macros AI</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:16px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px}
.btn:hover{background:rgba(0,240,255,0.2)}
.btn.green{border-color:#22c55e;color:#22c55e}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.card{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px}
.card-name{font-family:'Orbitron',monospace;color:#00f0ff;font-size:14px}
.card-info{font-size:11px;color:#64748b;margin:4px 0}
.card-steps{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.step{background:rgba(0,240,255,0.08);padding:2px 8px;border-radius:4px;font-size:9px;color:#94a3b8}
.recording{position:fixed;top:20px;right:20px;background:rgba(239,68,68,0.2);border:1px solid #ef4444;color:#ef4444;padding:8px 16px;border-radius:8px;font-family:'Share Tech Mono',monospace;font-size:12px;display:none;z-index:10}
.recording.show{display:flex;align-items:center;gap:8px}
.rec-dot{width:8px;height:8px;border-radius:50%;background:#ef4444;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}
#recPanel{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:rgba(3,8,20,0.95);border:1px solid rgba(0,240,255,0.2);border-radius:10px;padding:14px;display:none;z-index:10}
#recPanel.show{display:block}
</style></head><body>
<h1>DESKTOP MACROS AI</h1>
<div class="recording" id="recIndicator"><div class="rec-dot"></div>RECORDING</div>
<div id="recPanel" class="">
  <div style="font-size:12px;color:#00f0ff;margin-bottom:8px">Record Macro</div>
  <input id="macroName" placeholder="Macro name" style="background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:6px 10px;border-radius:6px;font-family:inherit;width:200px;margin-bottom:8px">
  <div style="display:flex;gap:8px">
    <button class="btn green" onclick="startRec()">Start Recording</button>
    <button class="btn" style="border-color:#ef4444;color:#ef4444" onclick="stopRec()">Stop</button>
  </div>
  <div style="margin-top:8px;font-size:10px;color:#64748b">Steps recorded: <span id="stepCount">0</span></div>
</div>
<div style="margin-bottom:12px"><button class="btn" onclick="toggleRec()">Record New Macro</button></div>
<div class="grid" id="macros"></div>
<script>
let recording=false;let steps=[];let recStart=0;
function toggleRec(){document.getElementById('recPanel').classList.toggle('show')}
async function startRec(){recording=true;steps=[];recStart=Date.now();document.getElementById('recIndicator').classList.add('show');document.getElementById('stepCount').textContent='0'}
function stopRec(){recording=false;document.getElementById('recIndicator').classList.remove('show');if(steps.length>0)saveMacro()}
async function saveMacro(){
  const name=document.getElementById('macroName').value||'Macro_'+Date.now();
  await fetch('/api/macros/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,steps})});
  document.getElementById('macroName').value='';load();
}
document.addEventListener('keydown',e=>{if(!recording)return;steps.push({type:'key',key:e.key,time:Date.now()-recStart});document.getElementById('stepCount').textContent=steps.length});
document.addEventListener('click',e=>{if(!recording)return;steps.push({type:'click',x:e.clientX,y:e.clientY,time:Date.now()-recStart});document.getElementById('stepCount').textContent=steps.length});
async function load(){
  const r=await(await fetch('/api/macros/list')).json();
  document.getElementById('macros').innerHTML=(r.macros||[]).map(m=>
    '<div class="card"><div class="card-name">'+m.name+'</div>'+
    '<div class="card-info">Steps: '+(m.steps||[]).length+' | Runs: '+(m.runs||0)+'</div>'+
    '<div class="card-steps">'+(m.steps||[]).slice(0,5).map(s=>'<span class="step">'+s.type+(s.key||'')+'</span>').join('')+'</div>'+
    '<div style="margin-top:8px"><button class="btn green" onclick="runMacro('+m.id+')">Run</button> '+
    '<button class="btn" style="border-color:#ff0055;color:#ff0055" onclick="del('+m.id+')">Delete</button></div></div>'
  ).join('')||'<div style="color:#64748b">No macros recorded yet</div>';
}
async function runMacro(id){await fetch('/api/macros/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
async function del(id){await fetch('/api/macros/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 36] Desktop Macros AI starting on port 5046...")
    app.run(host="0.0.0.0", port=5046, debug=False)
