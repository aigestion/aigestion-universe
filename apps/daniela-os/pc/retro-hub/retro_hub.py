"""
System 43: Retro Emulator Hub
Retro game emulator launcher with ROM manager
"""

import json
import os
import subprocess
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


EMULATORS = [
    {
        "name": "RetroArch",
        "cmd": "retroarch",
        "platforms": ["NES", "SNES", "Genesis", "GBA", "N64"],
        "icon": "retro",
    },
    {"name": "Dolphin", "cmd": "dolphin", "platforms": ["GameCube", "Wii"], "icon": "dolphin"},
    {"name": "PCSX2", "cmd": "pcsx2", "platforms": ["PS2"], "icon": "ps2"},
    {"name": "PPSSPP", "cmd": "ppsspp", "platforms": ["PSP"], "icon": "psp"},
    {"name": "Citra", "cmd": "citra", "platforms": ["3DS"], "icon": "3ds"},
    {"name": "yuzu", "cmd": "yuzu", "platforms": ["Switch"], "icon": "switch"},
    {"name": "DeSmuME", "cmd": "desmume", "platforms": ["DS"], "icon": "ds"},
    {"name": "mGBA", "cmd": "mgba", "platforms": ["GBA"], "icon": "gba"},
]


@app.route("/")
def index():
    return RETRO_HTML


@app.route("/api/retro/list")
def list_emus():
    return jsonify({"emulators": EMULATORS})


@app.route("/api/retro/launch", methods=["POST"])
def launch():
    data = request.json or {}
    cmd = data.get("cmd", "")
    try:
        subprocess.Popen([cmd], shell=True)
    except Exception:
        pass
    return jsonify({"ok": True})


@app.route("/api/retro/roms")
def list_roms():
    roms_dir = request.args.get("dir", "")
    if not roms_dir or not os.path.exists(roms_dir):
        return jsonify({"roms": []})
    roms = []
    for f in Path(roms_dir).iterdir():
        if f.suffix.lower() in [
            ".nes",
            ".sfc",
            ".smc",
            ".gb",
            ".gba",
            ".gbc",
            ".n64",
            ".z64",
            ".iso",
            ".bin",
            ".rom",
        ]:
            roms.append({"name": f.stem, "ext": f.suffix, "size": f.stat().st_size, "path": str(f)})
    return jsonify({"roms": roms[:50]})


RETRO_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Retro Emulator Hub</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a2e;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.emu-card{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:12px;padding:16px;text-align:center;cursor:pointer;transition:all 0.3s}
.emu-card:hover{border-color:#00f0ff;box-shadow:0 0 20px rgba(0,240,255,0.15);transform:translateY(-3px)}
.emu-icon{font-size:36px;margin-bottom:8px}
.emu-name{font-family:'Orbitron',monospace;font-size:13px;color:#00f0ff}
.emu-platforms{display:flex;flex-wrap:wrap;gap:4px;justify-content:center;margin-top:8px}
.platform-tag{background:rgba(0,240,255,0.08);color:#94a3b8;padding:2px 6px;border-radius:4px;font-size:9px}
.rom-section{margin-top:20px;padding:16px;background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px}
.input{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px;width:100%}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px}
.rom{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px}
.rom-name{color:#e2e8f0}.rom-ext{color:#64748b}.rom-size{color:#64748b}
</style></head><body>
<h1>RETRO EMULATOR HUB</h1>
<div class="grid" id="emus"></div>
<div class="rom-section">
  <h2 style="font-size:13px;color:#00f0ff;font-family:'Orbitron',monospace;margin-bottom:10px">ROM LIBRARY</h2>
  <div style="display:flex;gap:8px;margin-bottom:10px">
    <input class="input" id="romDir" placeholder="ROM folder path" style="flex:1">
    <button class="btn" onclick="loadRoms()">Scan</button>
  </div>
  <div id="roms"></div>
</div>
<script>
async function load(){
  const r=await(await fetch('/api/retro/list')).json();
  const icons={retro:'127918',dolphin:'128011',ps2:'128195',psp:'127917',ds:'128241',switch:'127918',gba:'128241',3ds:'128241'};
  document.getElementById('emus').innerHTML=(r.emulators||[]).map(e=>
    '<div class="emu-card" onclick="launchEmu(\''+e.cmd+'\')">'+
    '<div class="emu-icon">'+String.fromCodePoint(parseInt(icons[e.icon]||'127918'))+'</div>'+
    '<div class="emu-name">'+e.name+'</div>'+
    '<div class="emu-platforms">'+e.platforms.map(p=>'<span class="platform-tag">'+p+'</span>').join('')+'</div></div>'
  ).join('');
}
async function launchEmu(cmd){await fetch('/api/retro/launch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd})})}
async function loadRoms(){
  const dir=document.getElementById('romDir').value;
  const r=await(await fetch('/api/retro/roms?dir='+encodeURIComponent(dir))).json();
  document.getElementById('roms').innerHTML=(r.roms||[]).map(rom=>
    '<div class="rom"><span class="rom-name">'+rom.name+'</span><span class="rom-ext">'+rom.ext+'</span><span class="rom-size">'+(rom.size/1024).toFixed(1)+' KB</span></div>'
  ).join('')||'<div style="color:#64748b">No ROMs found</div>';
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 43] Retro Emulator Hub starting on port 5053...")
    app.run(host="0.0.0.0", port=5053, debug=False)
