"""
System 7: Cross-Device Telepathy
Seamless phone-PC handoff: clipboard, files, notifications, continue reading
"""

import json
import time
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

SYNC_DIR = Path(__file__).parent / "sync_data"
SYNC_DIR.mkdir(exist_ok=True)

CLIPBOARD_FILE = SYNC_DIR / "clipboard.json"
FILES_DIR = SYNC_DIR / "files"
FILES_DIR.mkdir(exist_ok=True)
HISTORY_FILE = SYNC_DIR / "history.json"


def load_json(path, default=None):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


@app.route("/")
def index():
    return TELEPATHY_HTML


@app.route("/api/sync/clipboard", methods=["POST"])
def sync_clipboard():
    data = request.json or {}
    save_json(
        CLIPBOARD_FILE,
        {
            "text": data.get("text", ""),
            "source": data.get("source", "unknown"),
            "timestamp": time.time(),
        },
    )
    return jsonify({"ok": True})


@app.route("/api/sync/clipboard")
def get_clipboard():
    return jsonify(load_json(CLIPBOARD_FILE, {"text": "", "source": "", "timestamp": 0}))


@app.route("/api/sync/file", methods=["POST"])
def sync_file():
    if "file" in request.files:
        f = request.files["file"]
        filepath = FILES_DIR / f.filename
        f.save(filepath)
        return jsonify({"ok": True, "filename": f.filename, "size": filepath.stat().st_size})
    return jsonify({"error": "No file"}), 400


@app.route("/api/sync/files")
def list_files():
    files = []
    for f in FILES_DIR.iterdir():
        if f.is_file():
            files.append({"name": f.name, "size": f.stat().st_size, "modified": f.stat().st_mtime})
    files.sort(key=lambda x: x["modified"], reverse=True)
    return jsonify({"files": files[:20]})


@app.route("/api/sync/history", methods=["POST"])
def add_history():
    data = request.json or {}
    history = load_json(HISTORY_FILE, {"items": []})
    history["items"].append(
        {
            "type": data.get("type", "text"),
            "content": data.get("content", ""),
            "source": data.get("source", "unknown"),
            "timestamp": time.time(),
        }
    )
    history["items"] = history["items"][-100:]  # Keep last 100
    save_json(HISTORY_FILE, history)
    return jsonify({"ok": True})


@app.route("/api/sync/history")
def get_history():
    return jsonify(load_json(HISTORY_FILE, {"items": []}))


TELEPATHY_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Cross-Device Telepathy</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#030814; color:#e2e8f0; font-family:'Rajdhani',sans-serif; padding:30px; }
h1 { font-family:'Orbitron',monospace; color:#00f0ff; font-size:20px; letter-spacing:3px; margin-bottom:20px; }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
.card { background:rgba(3,8,20,0.8); border:1px solid rgba(0,240,255,0.15); border-radius:12px; padding:16px; }
.card h2 { font-size:13px; color:#00f0ff; margin-bottom:12px; font-family:'Orbitron',monospace; letter-spacing:1px; }
.clipboard-input { width:100%; background:rgba(0,240,255,0.03); border:1px solid rgba(0,240,255,0.15); color:#e2e8f0; padding:10px; border-radius:6px; font-family:inherit; font-size:13px; resize:vertical; min-height:80px; }
.clipboard-input:focus { outline:none; border-color:#00f0ff; }
.btn { background:rgba(0,240,255,0.1); border:1px solid #00f0ff; color:#00f0ff; padding:8px 16px; border-radius:6px; cursor:pointer; font-family:inherit; margin-top:8px; }
.btn:hover { background:rgba(0,240,255,0.2); }
.file-drop { border:2px dashed rgba(0,240,255,0.2); border-radius:10px; padding:30px; text-align:center; color:#64748b; font-size:12px; cursor:pointer; transition:all 0.3s; }
.file-drop:hover { border-color:#00f0ff; color:#00f0ff; }
.file-list { max-height:200px; overflow-y:auto; }
.file-item { display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(0,240,255,0.05); font-size:11px; }
.history-item { padding:6px 0; border-bottom:1px solid rgba(0,240,255,0.05); font-size:11px; color:#94a3b8; }
.history-source { color:#00f0ff; font-size:9px; }
.qr-section { text-align:center; padding:20px; }
.qr-section img { width:150px; height:150px; background:white; padding:10px; border-radius:8px; }
.status-dot { display:inline-block; width:6px; height:6px; border-radius:50%; background:#22c55e; margin-right:6px; }
</style></head><body>
<h1>🔗 CROSS-DEVICE TELEPATHY</h1>
<div class="grid">
  <div class="card">
    <h2>📋 CLIPBOARD SYNC</h2>
    <textarea class="clipboard-input" id="clipText" placeholder="Type or paste text to sync..."></textarea>
    <button class="btn" onclick="syncClip()">Sync to Phone →</button>
    <div id="clipStatus" style="font-size:10px;color:#64748b;margin-top:8px"></div>
  </div>
  <div class="card">
    <h2>📁 FILE SYNC</h2>
    <div class="file-drop" id="dropZone" onclick="document.getElementById('fileInput').click()">
      Drop files here or click to upload
      <input id="fileInput" type="file" multiple style="display:none" onchange="uploadFiles(this.files)">
    </div>
    <div class="file-list" id="fileList"></div>
  </div>
  <div class="card" style="grid-column:span 2">
    <h2>📜 SYNC HISTORY</h2>
    <div id="history"></div>
  </div>
</div>
<script>
async function syncClip() {
  const text = document.getElementById('clipText').value;
  await fetch('/api/sync/clipboard', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text, source:'pc'})});
  document.getElementById('clipStatus').textContent = 'Synced! ' + new Date().toLocaleTimeString();
  await fetch('/api/sync/history', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({type:'clipboard', content:text.substring(0,100), source:'pc'})});
  loadHistory();
}

async function uploadFiles(files) {
  for(const f of files) {
    const fd = new FormData(); fd.append('file', f);
    await fetch('/api/sync/file', {method:'POST', body:fd});
  }
  loadFiles();
}

async function loadFiles() {
  const r = await (await fetch('/api/sync/files')).json();
  document.getElementById('fileList').innerHTML = r.files.map(f =>
    '<div class="file-item"><span>' + f.name + '</span><span>' + (f.size/1024).toFixed(1) + ' KB</span></div>'
  ).join('');
}

async function loadHistory() {
  const r = await (await fetch('/api/sync/history')).json();
  document.getElementById('history').innerHTML = r.items.slice(-10).reverse().map(h =>
    '<div class="history-item"><span class="history-source">' + h.source + '</span> ' + h.content.substring(0,60) + '</div>'
  ).join('');
}

// Drag and drop
const dz = document.getElementById('dropZone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.style.borderColor = '#00f0ff'; });
dz.addEventListener('dragleave', () => { dz.style.borderColor = 'rgba(0,240,255,0.2)'; });
dz.addEventListener('drop', e => { e.preventDefault(); dz.style.borderColor = 'rgba(0,240,255,0.2)'; uploadFiles(e.dataTransfer.files); });

loadFiles(); loadHistory();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 7] Cross-Device Telepathy starting on port 5016...")
    app.run(host="0.0.0.0", port=5016, debug=False)
