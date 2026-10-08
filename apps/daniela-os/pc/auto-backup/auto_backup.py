"""
System 40: Auto-Backup Brain
Smart file backup - detects important files and backs them up automatically
"""

import json
import os
import shutil
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
    return BACKUP_HTML


@app.route("/api/backup/rules")
def get_rules():
    return jsonify(load_json(DATA_DIR / "rules.json", {"rules": []}))


@app.route("/api/backup/rules", methods=["POST"])
def add_rule():
    data = request.json or {}
    rules = load_json(DATA_DIR / "rules.json", {"rules": []})
    rule = {
        "id": int(time.time()),
        "source": data.get("source", ""),
        "dest": data.get("dest", ""),
        "pattern": data.get("pattern", "*"),
        "interval": data.get("interval", "daily"),
        "active": True,
        "last_backup": None,
        "created": time.time(),
    }
    rules["rules"].append(rule)
    save_json(DATA_DIR / "rules.json", rules)
    return jsonify({"ok": True})


@app.route("/api/backup/delete", methods=["POST"])
def delete_rule():
    data = request.json or {}
    rules = load_json(DATA_DIR / "rules.json", {"rules": []})
    rules["rules"] = [r for r in rules["rules"] if r["id"] != data.get("id")]
    save_json(DATA_DIR / "rules.json", rules)
    return jsonify({"ok": True})


@app.route("/api/backup/execute", methods=["POST"])
def execute():
    data = request.json or {}
    rule_id = data.get("id")
    rules = load_json(DATA_DIR / "rules.json", {"rules": []})
    log = load_json(DATA_DIR / "log.json", {"entries": []})
    for r in rules["rules"]:
        if r["id"] == rule_id:
            source = Path(r["source"])
            dest = Path(r["dest"])
            if not source.exists():
                return jsonify({"error": "Source not found"}), 400
            dest.mkdir(parents=True, exist_ok=True)
            count = 0
            for f in source.glob(r.get("pattern", "*")):
                if f.is_file():
                    try:
                        shutil.copy2(str(f), str(dest / f.name))
                        count += 1
                    except Exception:
                        pass
            r["last_backup"] = time.time()
            save_json(DATA_DIR / "rules.json", rules)
            log["entries"].append(
                {
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "rule": r["source"],
                    "files": count,
                    "dest": r["dest"],
                }
            )
            log["entries"] = log["entries"][-100:]
            save_json(DATA_DIR / "log.json", log)
            return jsonify({"ok": True, "files_backed_up": count})
    return jsonify({"error": "Rule not found"}), 404


@app.route("/api/backup/scan", methods=["POST"])
def scan():
    data = request.json or {}
    source = data.get("source", "")
    if not source or not os.path.exists(source):
        return jsonify({"error": "Folder not found"}), 400
    files = []
    for f in Path(source).iterdir():
        if f.is_file():
            files.append({"name": f.name, "size": f.stat().st_size, "modified": f.stat().st_mtime})
    files.sort(key=lambda x: x["modified"], reverse=True)
    important = [f for f in files if f["size"] > 10000]
    return jsonify({"total": len(files), "important": len(important), "files": files[:20]})


@app.route("/api/backup/log")
def get_log():
    return jsonify(load_json(DATA_DIR / "log.json", {"entries": []}))


BACKUP_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Auto-Backup Brain</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:16px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px}
.btn:hover{background:rgba(0,240,255,0.2)}
.btn.green{border-color:#22c55e;color:#22c55e}
.input{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px;width:100%}
select{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px;border-radius:6px;font-family:inherit}
.section{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px;margin-bottom:12px}
.section h2{font-size:13px;color:#00f0ff;font-family:'Orbitron',monospace;letter-spacing:1px;margin-bottom:10px}
.rule{display:flex;gap:8px;align-items:center;padding:8px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px}
.rule-path{color:#00f0ff;flex:1;font-family:'Share Tech Mono',monospace}
.rule-arrow{color:#64748b}
.log-entry{font-size:10px;color:#94a3b8;padding:3px 0;border-bottom:1px solid rgba(0,240,255,0.03);font-family:'Share Tech Mono',monospace}
</style></head><body>
<h1>AUTO-BACKUP BRAIN</h1>
<div class="section">
  <h2>Add Backup Rule</h2>
  <div style="display:flex;gap:8px;margin-bottom:8px">
    <input class="input" id="source" placeholder="Source folder" style="flex:2">
    <input class="input" id="dest" placeholder="Backup destination" style="flex:2">
    <input class="input" id="pattern" placeholder="Pattern (e.g. *.pdf)" style="flex:1" value="*">
    <select id="interval"><option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option></select>
    <button class="btn green" onclick="addRule()">Add Rule</button>
  </div>
</div>
<div class="section">
  <h2>Backup Rules</h2>
  <div id="rules"></div>
</div>
<div class="section">
  <h2>Backup Log</h2>
  <div id="log"></div>
</div>
<script>
async function load(){
  const r=await(await fetch('/api/backup/rules')).json();
  document.getElementById('rules').innerHTML=(r.rules||[]).map(rule=>
    '<div class="rule"><span class="rule-path">'+rule.source+'</span>'+
    '<span class="rule-arrow">-></span><span class="rule-path">'+rule.dest+'</span>'+
    '<span style="color:#64748b">'+rule.interval+'</span>'+
    '<button class="btn green" onclick="execute('+rule.id+')">Backup Now</button>'+
    '<button class="btn" style="border-color:#ff0055;color:#ff0055" onclick="del('+rule.id+')">X</button></div>'
  ).join('')||'<div style="color:#64748b">No backup rules</div>';
  const l=await(await fetch('/api/backup/log')).json();
  document.getElementById('log').innerHTML=(l.entries||[]).slice(-10).reverse().map(e=>
    '<div class="log-entry">['+e.time+'] '+e.files+' files -> '+e.dest+'</div>'
  ).join('')||'<div style="color:#64748b">No backup activity</div>';
}
async function addRule(){
  const data={source:document.getElementById('source').value,dest:document.getElementById('dest').value,pattern:document.getElementById('pattern').value,interval:document.getElementById('interval').value};
  await fetch('/api/backup/rules',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});load();
}
async function execute(id){const r=await(await fetch('/api/backup/execute',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})})).json();alert(r.files_backed_up+' files backed up!');load()}
async function del(id){await fetch('/api/backup/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 40] Auto-Backup Brain starting on port 5050...")
    app.run(host="0.0.0.0", port=5050, debug=False)
