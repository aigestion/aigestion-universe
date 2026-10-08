"""
System 12: Dream Logger
Automatic visual diary - screenshots + context every 30 minutes
"""

import hashlib
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "dreams"
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


@app.route("/")
def index():
    return DREAM_HTML


@app.route("/api/dream/capture", methods=["POST"])
def capture_dream():
    try:
        ts = time.time()
        filename = f"dream_{int(ts)}.png"
        filepath = SCREENSHOTS_DIR / filename
        subprocess.run(
            [
                "powershell",
                "-Command",
                f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen | ForEach-Object {{ $bmp = New-Object System.Drawing.Bitmap($_.Bounds.Width, $_.Bounds.Height); $gfx = [System.Drawing.Graphics]::FromImage($bmp); $gfx.CopyFromScreen($_.Bounds.Location, [System.Drawing.Point]::Empty, $_.Bounds.Size); $bmp.Save('{filepath}') }}",
            ],
            timeout=10,
        )
        entry = {
            "id": hashlib.md5(str(ts).encode()).hexdigest()[:8],
            "timestamp": ts,
            "datetime": datetime.now().isoformat(),
            "filename": filename,
            "note": request.json.get("note", "") if request.json else "",
            "mood": request.json.get("mood", "neutral") if request.json else "neutral",
        }
        day = datetime.now().strftime("%Y-%m-%d")
        day_file = DATA_DIR / f"{day}.json"
        dreams = load_json(day_file, {"entries": []})
        dreams["entries"].append(entry)
        save_json(day_file, dreams)
        return jsonify({"ok": True, "filename": filename})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/dream/list")
def list_dreams():
    days = int(request.args.get("days", 7))
    all_dreams = []
    for i in range(days):
        day = (datetime.now() - __import__("datetime").timedelta(days=i)).strftime("%Y-%m-%d")
        day_file = DATA_DIR / f"{day}.json"
        if day_file.exists():
            data = load_json(day_file, {"entries": []})
            for e in data.get("entries", []):
                e["day"] = day
                all_dreams.append(e)
    all_dreams.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return jsonify({"dreams": all_dreams[:50]})


@app.route("/api/dream/<filename>")
def serve_screenshot(filename):
    return send_from_directory(str(SCREENSHOTS_DIR), filename)


DREAM_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Dream Logger</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:10px 16px;border-radius:8px;cursor:pointer;font-family:inherit}
.btn:hover{background:rgba(0,240,255,0.2)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
.card{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;overflow:hidden}
.card img{width:100%;height:180px;object-fit:cover;border-bottom:1px solid rgba(0,240,255,0.1)}
.card-body{padding:12px}
.card-time{font-size:10px;color:#64748b;font-family:'Share Tech Mono',monospace}
.card-note{font-size:12px;color:#94a3b8;margin-top:4px}
.capture-area{display:flex;gap:12px;align-items:center;margin-bottom:20px;padding:16px;background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.15);border-radius:10px}
.capture-area input{flex:1;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:10px 14px;border-radius:6px;font-family:inherit}
.capture-area select{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:10px;border-radius:6px;font-family:inherit}
.stats{position:fixed;bottom:20px;right:20px;font-size:10px;color:#64748b;font-family:'Share Tech Mono',monospace}
</style></head><body>
<h1>DREAM LOGGER</h1>
<div class="capture-area">
  <input id="note" placeholder="What's happening?">
  <select id="mood"><option value="neutral">Neutral</option><option value="happy">Happy</option><option value="focused">Focused</option><option value="tired">Tired</option><option value="creative">Creative</option></select>
  <button class="btn" onclick="capture()">Capture Moment</button>
  <button class="btn" onclick="autoCapture()" id="autoBtn">Auto: OFF</button>
</div>
<div class="grid" id="dreams"></div>
<div class="stats" id="stats"></div>
<script>
let autoInterval=null;
async function capture(){
  const note=document.getElementById('note').value;
  const mood=document.getElementById('mood').value;
  await fetch('/api/dream/capture',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({note,mood})});
  document.getElementById('note').value='';
  load();
}
function autoCapture(){
  const btn=document.getElementById('autoBtn');
  if(autoInterval){clearInterval(autoInterval);autoInterval=null;btn.textContent='Auto: OFF';return}
  autoInterval=setInterval(capture,1800000);
  btn.textContent='Auto: ON (30m)';
  capture();
}
async function load(){
  const r=await(await fetch('/api/dream/list')).json();
  document.getElementById('dreams').innerHTML=r.dreams.map(d=>
    '<div class="card"><img src="/api/dream/'+d.filename+'" onerror="this.style.display=\'none\'">'+
    '<div class="card-body"><div class="card-time">'+new Date(d.timestamp*1000).toLocaleString()+' | '+d.mood+'</div>'+
    '<div class="card-note">'+(d.note||'No note')+'</div></div></div>'
  ).join('')||'<div style="color:#64748b">No dreams captured yet</div>';
  document.getElementById('stats').textContent=r.dreams.length+' moments captured';
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 12] Dream Logger starting on port 5022...")
    app.run(host="0.0.0.0", port=5022, debug=False)
