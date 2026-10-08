"""
System 34: Smart File Watcher
Monitors folders and executes actions on file events
"""

import json
import os
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
    return WATCHER_HTML


@app.route("/api/watcher/rules")
def get_rules():
    return jsonify(load_json(DATA_DIR / "rules.json", {"rules": []}))


@app.route("/api/watcher/rules", methods=["POST"])
def add_rule():
    data = request.json or {}
    rules = load_json(DATA_DIR / "rules.json", {"rules": []})
    rule = {
        "id": int(time.time()),
        "folder": data.get("folder", ""),
        "event": data.get("event", "created"),
        "action": data.get("action", "log"),
        "target_ext": data.get("target_ext", ""),
        "active": True,
        "created": time.time(),
    }
    rules["rules"].append(rule)
    save_json(DATA_DIR / "rules.json", rules)
    return jsonify({"ok": True})


@app.route("/api/watcher/delete", methods=["POST"])
def delete_rule():
    data = request.json or {}
    rules = load_json(DATA_DIR / "rules.json", {"rules": []})
    rules["rules"] = [r for r in rules["rules"] if r["id"] != data.get("id")]
    save_json(DATA_DIR / "rules.json", rules)
    return jsonify({"ok": True})


@app.route("/api/watcher/logs")
def get_logs():
    logs = load_json(DATA_DIR / "logs.json", {"entries": []})
    return jsonify(logs)


@app.route("/api/watcher/scan", methods=["POST"])
def scan_folder():
    data = request.json or {}
    folder = data.get("folder", "")
    if not folder or not os.path.exists(folder):
        return jsonify({"error": "Folder not found"}), 400
    files = []
    for f in Path(folder).iterdir():
        files.append(
            {
                "name": f.name,
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime,
                "is_dir": f.is_dir(),
            }
        )
    files.sort(key=lambda x: x["modified"], reverse=True)
    logs = load_json(DATA_DIR / "logs.json", {"entries": []})
    logs["entries"].append(
        {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "folder": folder, "files_found": len(files)}
    )
    logs["entries"] = logs["entries"][-100:]
    save_json(DATA_DIR / "logs.json", logs)
    return jsonify({"files": files[:50], "total": len(files)})


WATCHER_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Smart File Watcher</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:16px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px}
.btn:hover{background:rgba(0,240,255,0.2)}
.input{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px;width:100%}
.section{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px;margin-bottom:12px}
.section h2{font-size:13px;color:#00f0ff;font-family:'Orbitron',monospace;letter-spacing:1px;margin-bottom:10px}
.rule{display:flex;gap:8px;align-items:center;padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px}
.rule-folder{color:#00f0ff;flex:1}
.rule-action{background:rgba(0,240,255,0.08);padding:2px 8px;border-radius:4px;color:#94a3b8}
select{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px;border-radius:6px;font-family:inherit}
.log{font-size:10px;color:#64748b;padding:3px 0;border-bottom:1px solid rgba(0,240,255,0.03);font-family:'Share Tech Mono',monospace}
</style></head><body>
<h1>SMART FILE WATCHER</h1>
<div class="section">
  <h2>Add Watch Rule</h2>
  <div style="display:flex;gap:8px">
    <input class="input" id="folder" placeholder="Folder to watch" style="flex:2">
    <select id="event"><option value="created">Created</option><option value="modified">Modified</option><option value="deleted">Deleted</option></select>
    <select id="action"><option value="log">Log</option><option value="alert">Alert</option><option value="organize">Organize</option></select>
    <button class="btn" onclick="addRule()">Add Rule</button>
  </div>
</div>
<div class="section">
  <h2>Active Rules</h2>
  <div id="rules"></div>
</div>
<div class="section">
  <h2>Scan Folder</h2>
  <div style="display:flex;gap:8px">
    <input class="input" id="scanFolder" placeholder="Path to scan" style="flex:1">
    <button class="btn" onclick="scan()">Scan Now</button>
  </div>
  <div id="scanResult" style="margin-top:8px"></div>
</div>
<div class="section">
  <h2>Event Log</h2>
  <div id="logs"></div>
</div>
<script>
async function load(){
  const r=await(await fetch('/api/watcher/rules')).json();
  document.getElementById('rules').innerHTML=(r.rules||[]).map(rule=>
    '<div class="rule"><span class="rule-folder">'+rule.folder+'</span>'+
    '<span class="rule-action">'+rule.event+'</span><span class="rule-action">'+rule.action+'</span>'+
    '<button class="btn" style="border-color:#ff0055;color:#ff0055" onclick="del('+rule.id+')">X</button></div>'
  ).join('')||'<div style="color:#64748b">No rules</div>';
  const l=await(await fetch('/api/watcher/logs')).json();
  document.getElementById('logs').innerHTML=(l.entries||[]).slice(-10).reverse().map(e=>
    '<div class="log">['+e.time+'] '+e.folder+' - '+e.files_found+' files</div>'
  ).join('')||'<div style="color:#64748b">No logs</div>';
}
async function addRule(){
  const data={folder:document.getElementById('folder').value,event:document.getElementById('event').value,action:document.getElementById('action').value};
  await fetch('/api/watcher/rules',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});load();
}
async function del(id){await fetch('/api/watcher/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
async function scan(){
  const r=await(await fetch('/api/watcher/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({folder:document.getElementById('scanFolder').value})})).json();
  document.getElementById('scanResult').innerHTML='<div style="font-size:11px;color:#94a3b8">'+r.total+' files found</div>';load();
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 34] Smart File Watcher starting on port 5044...")
    app.run(host="0.0.0.0", port=5044, debug=False)
