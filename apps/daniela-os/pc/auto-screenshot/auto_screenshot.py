"""
System 32: Auto-Screenshot Context
Screenshots with automatic context - what app was active, searchable
"""

import hashlib
import json
import subprocess
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_active_window():
    try:
        result = subprocess.run(
            [
                "powershell",
                "-Command",
                "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object -First 1 ProcessName, MainWindowTitle | ConvertTo-Json",
            ],
            capture_output=True,
            text=True,
            timeout=3,
        )
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        return {"app": data.get("ProcessName", "Unknown"), "title": data.get("MainWindowTitle", "")}
    except Exception:
        return {"app": "Unknown", "title": ""}


@app.route("/")
def index():
    return SCREENSHOT_HTML


@app.route("/api/screenshot/capture", methods=["POST"])
def capture():
    ts = int(time.time())
    filename = f"screenshot_{ts}.png"
    filepath = SCREENSHOTS_DIR / filename
    try:
        subprocess.run(
            [
                "powershell",
                "-Command",
                f"Add-Type -AssemblyName System.Windows.Forms; $bmp = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); $gfx = [System.Windows.Forms.Graphics]::FromImage($bmp); $gfx.CopyFromScreen([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Location, [System.Drawing.Point]::Empty, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Size); $bmp.Save('{filepath}')",
            ],
            timeout=10,
        )
        context = get_active_window()
        note = request.json.get("note", "") if request.json else ""
        entry = {
            "id": hashlib.md5(str(ts).encode()).hexdigest()[:8],
            "filename": filename,
            "timestamp": ts,
            "date": time.strftime("%Y-%m-%d %H:%M"),
            "app": context["app"],
            "window_title": context["title"],
            "note": note,
            "tags": [],
        }
        shots = load_json(DATA_DIR / "screenshots.json", {"items": []})
        shots["items"].append(entry)
        save_json(DATA_DIR / "screenshots.json", shots)
        return jsonify({"ok": True, "filename": filename})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/screenshot/list")
def list_shots():
    shots = load_json(DATA_DIR / "screenshots.json", {"items": []})
    q = request.args.get("q", "").lower()
    items = shots.get("items", [])
    if q:
        items = [
            s
            for s in items
            if q in s.get("app", "").lower()
            or q in s.get("window_title", "").lower()
            or q in s.get("note", "").lower()
        ]
    items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return jsonify({"items": items[:50]})


@app.route("/api/screenshot/<filename>")
def serve(filename):
    return send_from_directory(str(SCREENSHOTS_DIR), filename)


@app.route("/api/screenshot/delete", methods=["POST"])
def delete():
    data = request.json or {}
    shots = load_json(DATA_DIR / "screenshots.json", {"items": []})
    shots["items"] = [s for s in shots["items"] if s["id"] != data.get("id")]
    save_json(DATA_DIR / "screenshots.json", shots)
    return jsonify({"ok": True})


SCREENSHOT_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Auto-Screenshot Context</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:16px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:10px 16px;border-radius:8px;cursor:pointer;font-family:inherit}
.btn:hover{background:rgba(0,240,255,0.2)}
.search{width:100%;background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.2);color:#e2e8f0;padding:10px 16px;border-radius:8px;font-size:14px;font-family:inherit;margin-bottom:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.card{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;overflow:hidden;cursor:pointer}
.card img{width:100%;height:160px;object-fit:cover}
.card-body{padding:10px}
.card-app{font-size:11px;color:#00f0ff;font-family:'Share Tech Mono',monospace}
.card-title{font-size:10px;color:#94a3b8;margin:2px 0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.card-date{font-size:9px;color:#64748b}
</style></head><body>
<h1>AUTO-SCREENSHOT CONTEXT</h1>
<div style="display:flex;gap:8px;margin-bottom:12px">
  <button class="btn" onclick="capture()">Capture Screenshot</button>
  <input class="search" id="search" placeholder="Search by app, title, or note..." onkeyup="load()" style="flex:1">
</div>
<div class="grid" id="shots"></div>
<script>
async function capture(){
  const note=prompt('Optional note:')||'';
  await fetch('/api/screenshot/capture',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({note})});
  load();
}
async function load(){
  const q=document.getElementById('search').value;
  const r=await(await fetch('/api/screenshot/list?q='+encodeURIComponent(q))).json();
  document.getElementById('shots').innerHTML=(r.items||[]).map(s=>
    '<div class="card" onclick="window.open(\'/api/screenshot/'+s.filename+'\')">'+
    '<img src="/api/screenshot/'+s.filename+'" onerror="this.style.display=\'none\'">'+
    '<div class="card-body"><div class="card-app">'+s.app+'</div>'+
    '<div class="card-title">'+(s.window_title||s.note||'')+'</div>'+
    '<div class="card-date">'+s.date+'</div></div></div>'
  ).join('')||'<div style="color:#64748b">No screenshots yet</div>';
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 32] Auto-Screenshot Context starting on port 5042...")
    app.run(host="0.0.0.0", port=5042, debug=False)
