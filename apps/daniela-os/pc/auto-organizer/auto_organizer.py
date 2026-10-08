"""
System 14: AI Auto-Organizer
Classifies and moves files automatically by content/type
"""

import json
import shutil
import time
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

RULES_FILE = Path(__file__).parent / "rules.json"
LOG_FILE = Path(__file__).parent / "organize_log.json"


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


DEFAULT_RULES = [
    {
        "name": "Documents",
        "extensions": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
        "folder": "Documents",
    },
    {
        "name": "Images",
        "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
        "folder": "Images",
    },
    {
        "name": "Videos",
        "extensions": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
        "folder": "Videos",
    },
    {
        "name": "Music",
        "extensions": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"],
        "folder": "Music",
    },
    {
        "name": "Archives",
        "extensions": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "folder": "Archives",
    },
    {
        "name": "Code",
        "extensions": [".py", ".js", ".html", ".css", ".java", ".cpp", ".ts"],
        "folder": "Code",
    },
    {
        "name": "Executables",
        "extensions": [".exe", ".msi", ".bat", ".cmd"],
        "folder": "Executables",
    },
]


@app.route("/")
def index():
    return ORGANIZER_HTML


@app.route("/api/rules")
def get_rules():
    return jsonify(
        {"rules": load_json(RULES_FILE, {"rules": DEFAULT_RULES}).get("rules", DEFAULT_RULES)}
    )


@app.route("/api/rules", methods=["POST"])
def set_rules():
    data = request.json or {}
    save_json(RULES_FILE, {"rules": data.get("rules", DEFAULT_RULES)})
    return jsonify({"ok": True})


@app.route("/api/organize/preview")
def preview():
    source = request.args.get("source", str(Path.home() / "Downloads"))
    rules = load_json(RULES_FILE, {"rules": DEFAULT_RULES}).get("rules", DEFAULT_RULES)
    plan = []
    source_path = Path(source)
    if not source_path.exists():
        return jsonify({"error": "Source folder not found"}), 400
    for item in source_path.iterdir():
        if item.is_file():
            ext = item.suffix.lower()
            target_folder = "Other"
            for rule in rules:
                if ext in rule.get("extensions", []):
                    target_folder = rule["folder"]
                    break
            plan.append(
                {
                    "file": item.name,
                    "size": item.stat().st_size,
                    "target": target_folder,
                    "ext": ext,
                }
            )
    return jsonify({"plan": plan, "total": len(plan)})


@app.route("/api/organize/execute", methods=["POST"])
def execute():
    data = request.json or {}
    source = data.get("source", str(Path.home() / "Downloads"))
    base = data.get("base", str(Path.home() / "Organized"))
    rules = load_json(RULES_FILE, {"rules": DEFAULT_RULES}).get("rules", DEFAULT_RULES)
    log = load_json(LOG_FILE, {"moves": []})
    source_path = Path(source)
    base_path = Path(base)
    moved = 0
    for item in source_path.iterdir():
        if item.is_file():
            ext = item.suffix.lower()
            target_folder = "Other"
            for rule in rules:
                if ext in rule.get("extensions", []):
                    target_folder = rule["folder"]
                    break
            dest_dir = base_path / target_folder
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / item.name
            if dest.exists():
                dest = dest_dir / f"{item.stem}_{int(time.time())}{item.suffix}"
            try:
                shutil.move(str(item), str(dest))
                log["moves"].append(
                    {"file": item.name, "from": str(item), "to": str(dest), "time": time.time()}
                )
                moved += 1
            except Exception:
                pass
    save_json(LOG_FILE, log)
    return jsonify({"ok": True, "moved": moved})


@app.route("/api/log")
def get_log():
    return jsonify(load_json(LOG_FILE, {"moves": []}))


ORGANIZER_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>AI Auto-Organizer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:10px 16px;border-radius:8px;cursor:pointer;font-family:inherit;margin:4px}
.btn:hover{background:rgba(0,240,255,0.2)}
.btn.green{border-color:#22c55e;color:#22c55e}
.btn.green:hover{background:rgba(34,197,94,0.1)}
.section{margin-bottom:20px;padding:16px;background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px}
.section h2{font-size:13px;color:#00f0ff;font-family:'Orbitron',monospace;letter-spacing:1px;margin-bottom:10px}
.paths{display:flex;gap:8px;margin-bottom:12px}
.paths input{flex:1;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:10px;border-radius:6px;font-family:inherit;font-size:12px}
.table{width:100%;border-collapse:collapse;font-size:11px}
.table th{text-align:left;color:#00f0ff;padding:6px 8px;border-bottom:1px solid rgba(0,240,255,0.15);font-family:'Share Tech Mono',monospace}
.table td{padding:6px 8px;border-bottom:1px solid rgba(0,240,255,0.05);color:#94a3b8}
.table tr:hover td{background:rgba(0,240,255,0.03)}
.log-entry{padding:4px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:10px;color:#94a3b8}
</style></head><body>
<h1>AI AUTO-ORGANIZER</h1>
<div class="section">
  <h2>Source & Destination</h2>
  <div class="paths">
    <input id="source" value="C:\Users\Alejandro\Downloads" placeholder="Source folder">
    <input id="dest" value="C:\Users\Alejandro\Organized" placeholder="Destination folder">
    <button class="btn" onclick="preview()">Preview</button>
    <button class="btn green" onclick="execute()">Organize</button>
  </div>
</div>
<div class="section">
  <h2>Preview (<span id="count">0</span> files)</h2>
  <table class="table"><thead><tr><th>File</th><th>Type</th><th>Size</th><th>Target Folder</th></tr></thead>
  <tbody id="preview"></tbody></table>
</div>
<div class="section">
  <h2>Recent Activity</h2>
  <div id="log"></div>
</div>
<script>
async function preview(){
  const src=document.getElementById('source').value;
  const r=await(await fetch('/api/organize/preview?source='+encodeURIComponent(src))).json();
  document.getElementById('count').textContent=r.total||0;
  document.getElementById('preview').innerHTML=(r.plan||[]).map(p=>
    '<tr><td>'+p.file+'</td><td>'+p.ext+'</td><td>'+(p.size/1024).toFixed(1)+' KB</td><td>'+p.target+'</td></tr>'
  ).join('');
}
async function execute(){
  const src=document.getElementById('source').value;
  const dst=document.getElementById('dest').value;
  const r=await(await fetch('/api/organize/execute',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:src,base:dst})})).json();
  alert(r.moved+' files organized!');
  preview();loadLog();
}
async function loadLog(){
  const r=await(await fetch('/api/log')).json();
  document.getElementById('log').innerHTML=(r.moves||[]).slice(-10).reverse().map(m=>
    '<div class="log-entry">'+m.file+' -> '+m.to.split('\\').pop()+'</div>'
  ).join('')||'<div style="color:#64748b">No activity yet</div>';
}
preview();loadLog();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 14] AI Auto-Organizer starting on port 5024...")
    app.run(host="0.0.0.0", port=5024, debug=False)
