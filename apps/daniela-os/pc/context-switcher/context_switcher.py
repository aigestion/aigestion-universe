"""
System 13: Context Switcher
Smart Alt+Tab - saves/restores window layouts per context
"""

import json
import subprocess
import time
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "contexts"
DATA_DIR.mkdir(exist_ok=True)


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_running_apps():
    try:
        result = subprocess.run(
            [
                "powershell",
                "-Command",
                "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object ProcessName, MainWindowTitle, Id | ConvertTo-Json",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return json.loads(result.stdout) if result.stdout.strip() else []
    except Exception:
        return []


@app.route("/")
def index():
    return CONTEXT_HTML


@app.route("/api/context/list")
def list_contexts():
    contexts = []
    for f in DATA_DIR.glob("*.json"):
        data = load_json(f, {})
        contexts.append(
            {
                "name": f.stem,
                "apps": data.get("apps", []),
                "created": data.get("created", 0),
                "last_used": data.get("last_used", 0),
            }
        )
    contexts.sort(key=lambda x: x.get("last_used", 0), reverse=True)
    return jsonify({"contexts": contexts})


@app.route("/api/context/save", methods=["POST"])
def save_context():
    data = request.json or {}
    name = data.get("name", f"context_{int(time.time())}")
    apps = get_running_apps()
    context = {
        "apps": apps if isinstance(apps, list) else [apps],
        "created": time.time(),
        "last_used": time.time(),
        "description": data.get("description", ""),
    }
    save_json(DATA_DIR / f"{name}.json", context)
    return jsonify({"ok": True, "name": name, "apps_count": len(context["apps"])})


@app.route("/api/context/restore", methods=["POST"])
def restore_context():
    data = request.json or {}
    name = data.get("name", "")
    ctx_file = DATA_DIR / f"{name}.json"
    if not ctx_file.exists():
        return jsonify({"error": "Context not found"}), 404
    context = load_json(ctx_file, {})
    context["last_used"] = time.time()
    save_json(ctx_file, context)
    return jsonify({"ok": True, "apps": context.get("apps", [])})


@app.route("/api/context/delete", methods=["POST"])
def delete_context():
    data = request.json or {}
    name = data.get("name", "")
    ctx_file = DATA_DIR / f"{name}.json"
    if ctx_file.exists():
        ctx_file.unlink()
    return jsonify({"ok": True})


@app.route("/api/running")
def running():
    return jsonify({"apps": get_running_apps()})


CONTEXT_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Context Switcher</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:10px 16px;border-radius:8px;cursor:pointer;font-family:inherit;margin:4px}
.btn:hover{background:rgba(0,240,255,0.2)}
.btn.red{border-color:#ff0055;color:#ff0055}
.btn.red:hover{background:rgba(255,0,85,0.1)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin-top:16px}
.card{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px;cursor:pointer;transition:all 0.3s}
.card:hover{border-color:#00f0ff;box-shadow:0 0 20px rgba(0,240,255,0.1)}
.card-name{font-family:'Orbitron',monospace;color:#00f0ff;font-size:14px;letter-spacing:1px}
.card-info{font-size:11px;color:#64748b;margin-top:4px}
.card-apps{display:flex;flex-wrap:wrap;gap:4px;margin-top:8px}
.app-tag{background:rgba(0,240,255,0.08);color:#94a3b8;padding:2px 8px;border-radius:4px;font-size:10px}
.section{margin-bottom:20px}
.section h2{font-size:13px;color:#00f0ff;font-family:'Orbitron',monospace;letter-spacing:1px;margin-bottom:8px}
.running-list{display:flex;flex-wrap:wrap;gap:6px}
.running-item{background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);color:#22c55e;padding:4px 10px;border-radius:6px;font-size:11px}
.save-area{display:flex;gap:8px;margin-bottom:16px}
.save-area input{flex:1;background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.2);color:#e2e8f0;padding:10px;border-radius:8px;font-family:inherit}
</style></head><body>
<h1>CONTEXT SWITCHER</h1>
<div class="section">
  <h2>Currently Running</h2>
  <div class="running-list" id="running"></div>
</div>
<div class="save-area">
  <input id="ctxName" placeholder="Context name (e.g. 'work', 'coding', 'gaming')">
  <button class="btn" onclick="saveCtx()">Save Current Layout</button>
</div>
<div class="section">
  <h2>Saved Contexts</h2>
  <div class="grid" id="contexts"></div>
</div>
<script>
async function loadRunning(){
  const r=await(await fetch('/api/running')).json();
  const apps=Array.isArray(r.apps)?r.apps:[r.apps];
  document.getElementById('running').innerHTML=apps.map(a=>
    '<div class="running-item">'+(a.ProcessName||a.process_name||'Unknown')+'</div>'
  ).join('')||'<div style="color:#64748b">No apps with windows</div>';
}
async function loadContexts(){
  const r=await(await fetch('/api/context/list')).json();
  document.getElementById('contexts').innerHTML=r.contexts.map(c=>
    '<div class="card" onclick="restoreCtx(\''+c.name+'\')">'+
    '<div class="card-name">'+c.name+'</div>'+
    '<div class="card-info">'+c.apps.length+' apps | Last: '+(c.last_used?new Date(c.last_used*1000).toLocaleString():'Never')+'</div>'+
    '<div class="card-apps">'+c.apps.map(a=>'<span class="app-tag">'+(a.ProcessName||a.process_name||'?')+'</span>').join('')+'</div>'+
    '<button class="btn red" onclick="event.stopPropagation();deleteCtx(\''+c.name+'\')">Delete</button></div>'
  ).join('')||'<div style="color:#64748b">No saved contexts</div>';
}
async function saveCtx(){
  const name=document.getElementById('ctxName').value||'context_'+Date.now();
  await fetch('/api/context/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});
  document.getElementById('ctxName').value='';loadContexts();
}
async function restoreCtx(name){
  await fetch('/api/context/restore',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});
  loadContexts();
}
async function deleteCtx(name){
  await fetch('/api/context/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});
  loadContexts();
}
loadRunning();loadContexts();setInterval(loadRunning,5000);
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 13] Context Switcher starting on port 5023...")
    app.run(host="0.0.0.0", port=5023, debug=False)
