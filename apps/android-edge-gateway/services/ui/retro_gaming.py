# -*- coding: utf-8 -*-
"""
Idea 9: Retro Gaming Hub
Emulator launcher with BT controller support.
"""

import json
import subprocess
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent.parent / "data" / "gaming"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

EMULATORS = [
    {"id": "retroarch", "name": "RetroArch", "platforms": ["NES", "SNES", "GBA", "N64", "Genesis"], "icon": "127918", "pkg": "com.retroarch"},
    {"id": "ppsspp", "name": "PPSSPP", "platforms": ["PSP"], "icon": "127917", "pkg": "org.ppsspp.ppsspp"},
    {"id": "dolphin", "name": "Dolphin", "platforms": ["GameCube", "Wii"], "icon": "128011", "pkg": "org.dolphinemu.dolphin"},
    {"id": "aether", "name": "AetherSX2", "platforms": ["PS2"], "icon": "128195", "pkg": "xyz.aethersx2.android"},
    {"id": "citra", "name": "Citra", "platforms": ["3DS"], "icon": "128241", "pkg": "org.citra.citra_emu"},
    {"id": "yuzu", "name": "Yuzu", "platforms": ["Switch"], "icon": "127918", "pkg": "org.yuzu.yuzu_emu"},
]

@app.route("/")
def index():
    return GAMING_HTML

@app.route("/api/pixel/gaming/status")
def status():
    stats = load_json(DATA_DIR / "stats.json", {"playtime": {}, "launches": 0})
    controllers = [{"name": "Xbox Controller", "connected": True, "type": "Xbox"}, {"name": "PS5 DualSense", "connected": False, "type": "PS5"}]
    return jsonify({"emulators": EMULATORS, "stats": stats, "controllers": controllers})

@app.route("/api/pixel/gaming/launch", methods=["POST"])
def launch():
    data = request.json or {}
    pkg = data.get("pkg", "")
    try: subprocess.run(["am", "start", "-n", f"{pkg}/.ui.mainActivity"], capture_output=True, timeout=5)
    except Exception:
        pass
    stats = load_json(DATA_DIR / "stats.json", {"playtime": {}, "launches": 0})
    stats["launches"] = stats.get("launches", 0) + 1
    save_json(DATA_DIR / "stats.json", stats)
    return jsonify({"ok": True})

GAMING_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Retro Gaming Hub</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#f59e0b;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.stats{display:flex;gap:12px;margin-bottom:16px}
.stat-box{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px 20px;text-align:center}
.stat-val{font-family:'Orbitron',monospace;font-size:22px;color:#f59e0b}
.stat-label{font-size:9px;color:#64748b;letter-spacing:1px;margin-top:4px}
.emus{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-bottom:16px}
.emu{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:12px;padding:16px;cursor:pointer;transition:all 0.3s;text-align:center}
.emu:hover{border-color:#f59e0b;box-shadow:0 0 15px rgba(245,158,11,0.2)}
.emu-icon{font-size:36px;margin-bottom:8px}
.emu-name{font-family:'Orbitron',monospace;font-size:13px;color:#f59e0b}
.emu-platforms{display:flex;flex-wrap:wrap;gap:4px;justify-content:center;margin-top:8px}
.platform-tag{background:rgba(245,158,11,0.08);color:#94a3b8;padding:2px 6px;border-radius:4px;font-size:9px}
.controllers{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px}
.ctrl{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px}
.ctrl-status{padding:2px 6px;border-radius:4px;font-size:9px}
.ctrl-on{background:rgba(34,197,94,0.1);color:#22c55e}
.ctrl-off{background:rgba(100,116,139,0.1);color:#64748b}
</style></head><body>
<h1>RETRO GAMING HUB</h1>
<div class="stats">
  <div class="stat-box"><div class="stat-val" id="launches">0</div><div class="stat-label">TOTAL LAUNCHES</div></div>
  <div class="stat-box"><div class="stat-val" id="emulators">6</div><div class="stat-label">EMULATORS</div></div>
  <div class="stat-box"><div class="stat-val" id="controllers">1</div><div class="stat-label">CONTROLLERS</div></div>
</div>
<div class="emus" id="emus"></div>
<div class="controllers"><div style="font-size:12px;color:#f59e0b;font-family:'Orbitron',monospace;margin-bottom:8px">CONTROLLERS</div><div id="ctrlList"></div></div>
<script>
async function load(){const r=await(await fetch('/api/pixel/gaming/status')).json();document.getElementById('launches').textContent=r.stats.launches||0;document.getElementById('controllers').textContent=(r.controllers||[]).filter(c=>c.connected).length;document.getElementById('emus').innerHTML=(r.emulators||[]).map(e=>'<div class="emu" onclick="launch(\''+e.pkg+'\')"><div class="emu-icon">'+String.fromCodePoint(parseInt(e.icon))+'</div><div class="emu-name">'+e.name+'</div><div class="emu-platforms">'+e.platforms.map(p=>'<span class="platform-tag">'+p+'</span>').join('')+'</div></div>').join('');document.getElementById('ctrlList').innerHTML=(r.controllers||[]).map(c=>'<div class="ctrl"><span>'+c.name+'</span><span class="ctrl-status '+(c.connected?'ctrl-on':'ctrl-off')+'">'+(c.connected?'Connected':'Disconnected')+'</span></div>').join('')}
async function launch(pkg){await fetch('/api/pixel/gaming/launch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pkg})});load()}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[Idea 9] Retro Gaming Hub starting on port 9108...")
    app.run(host="0.0.0.0", port=9108, debug=False)