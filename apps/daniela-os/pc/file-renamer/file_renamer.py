"""
System 33: Batch File Renamer AI
Smart batch renaming by content, date, EXIF, or pattern
"""

import os
import re
import time
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def index():
    return RENAMER_HTML


@app.route("/api/renamer/preview", methods=["POST"])
def preview():
    data = request.json or {}
    folder = data.get("folder", "")
    pattern = data.get("pattern", "")
    mode = data.get("mode", "sequential")
    if not folder or not os.path.exists(folder):
        return jsonify({"error": "Folder not found"}), 400
    files = sorted([f for f in Path(folder).iterdir() if f.is_file()])
    plan = []
    for i, f in enumerate(files[:100]):
        ext = f.suffix
        if mode == "sequential":
            new_name = (
                f"{pattern}_{str(i + 1).zfill(4)}{ext}"
                if pattern
                else f"{f.stem}_{str(i + 1).zfill(4)}{ext}"
            )
        elif mode == "date":
            mtime = time.strftime("%Y%m%d_%H%M%S", time.localtime(f.stat().st_mtime))
            new_name = f"{mtime}_{f.stem}{ext}"
        elif mode == "lowercase":
            new_name = f"{f.stem.lower()}{ext}"
        elif mode == "replace":
            find = data.get("find", "")
            replace = data.get("replace", "")
            new_name = f"{f.stem.replace(find, replace)}{ext}" if find else f.name
        elif mode == "clean":
            new_name = re.sub(r"[^a-zA-Z0-9._-]", "_", f.stem).strip("_") + ext
        else:
            new_name = f.name
        plan.append({"old": f.name, "new": new_name, "size": f.stat().st_size})
    return jsonify({"plan": plan, "total": len(plan)})


@app.route("/api/renamer/execute", methods=["POST"])
def execute():
    data = request.json or {}
    folder = data.get("folder", "")
    renames = data.get("renames", [])
    count = 0
    for r in renames:
        old = Path(folder) / r["old"]
        new = Path(folder) / r["new"]
        if old.exists() and not new.exists():
            old.rename(new)
            count += 1
    return jsonify({"ok": True, "renamed": count})


RENAMER_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Batch File Renamer AI</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:16px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px}
.btn:hover{background:rgba(0,240,255,0.2)}
.btn.green{border-color:#22c55e;color:#22c55e}
.input{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px}
.controls{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center}
select{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px;border-radius:6px;font-family:inherit}
.table{width:100%;border-collapse:collapse;font-size:11px}
.table th{text-align:left;color:#00f0ff;padding:6px 8px;border-bottom:1px solid rgba(0,240,255,0.15);font-family:'Share Tech Mono',monospace}
.table td{padding:6px 8px;border-bottom:1px solid rgba(0,240,255,0.05);color:#94a3b8}
.table tr:hover td{background:rgba(0,240,255,0.03)}
.new-name{color:#22c55e}
</style></head><body>
<h1>BATCH FILE RENAMER AI</h1>
<div class="controls">
  <input class="input" id="folder" placeholder="Folder path" style="width:300px" value="C:\Users\Alejandro\Downloads">
  <select id="mode"><option value="sequential">Sequential</option><option value="date">By Date</option><option value="lowercase">Lowercase</option><option value="replace">Find/Replace</option><option value="clean">Clean Names</option></select>
  <input class="input" id="pattern" placeholder="Prefix (e.g. vacation)">
  <input class="input" id="findText" placeholder="Find" style="display:none">
  <input class="input" id="replaceText" placeholder="Replace" style="display:none">
  <button class="btn" onclick="preview()">Preview</button>
  <button class="btn green" onclick="execute()">Rename</button>
</div>
<table class="table"><thead><tr><th>Current Name</th><th>New Name</th><th>Size</th></tr></thead><tbody id="plan"></tbody></table>
<div style="margin-top:8px;font-size:10px;color:#64748b" id="count"></div>
<script>
document.getElementById('mode').onchange=function(){const m=this.value;document.getElementById('findText').style.display=m==='replace'?'inline-block':'none';document.getElementById('replaceText').style.display=m==='replace'?'inline-block':'none'};
let renames=[];
async function preview(){
  const data={folder:document.getElementById('folder').value,mode:document.getElementById('mode').value,pattern:document.getElementById('pattern').value,find:document.getElementById('findText').value,replace:document.getElementById('replaceText').value};
  const r=await(await fetch('/api/renamer/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})).json();
  renames=r.plan||[];
  document.getElementById('count').textContent=renames.length+' files to rename';
  document.getElementById('plan').innerHTML=renames.map(r=>
    '<tr><td>'+r.old+'</td><td class="new-name">'+r.new+'</td><td>'+(r.size/1024).toFixed(1)+' KB</td></tr>'
  ).join('');
}
async function execute(){
  const folder=document.getElementById('folder').value;
  const r=await(await fetch('/api/renamer/execute',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({folder,renames})})).json();
  alert(r.renamed+' files renamed!');preview();
}
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 33] Batch File Renamer AI starting on port 5043...")
    app.run(host="0.0.0.0", port=5043, debug=False)
