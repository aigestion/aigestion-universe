# -*- coding: utf-8 -*-
"""
Idea 8: NFC Quick Actions
NFC tag-based automation with pre-configured scenes.
"""

import json
import time
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent.parent / "data" / "nfc_quick"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

PRESET_SCENES = [
    {"id": "home", "name": "Home", "icon": "127968", "actions": ["wifi on", "bluetooth off", "brightness 50", "volume 8"], "color": "#22c55e"},
    {"id": "work", "name": "Work", "icon": "127970", "actions": ["wifi on", "notifications silent", "brightness 80"], "color": "#00f0ff"},
    {"id": "night", "name": "Night Mode", "icon": "127769", "actions": ["brightness 0", "dark mode on", "volume 3"], "color": "#8b5cf6"},
    {"id": "gym", "name": "Gym", "icon": "127947", "actions": ["bluetooth on", "spotify play", "volume 12"], "color": "#f59e0b"},
    {"id": "drive", "name": "Driving", "icon": "128663", "actions": ["bluetooth on", "dnd on", "navigation start"], "color": "#ff0055"},
    {"id": "emergency", "name": "Emergency", "icon": "128680", "actions": ["flashlight on", "volume 15", "sos mode"], "color": "#ff0055"},
]

@app.route("/")
def index():
    return NFC_HTML

@app.route("/api/pixel/nfc_quick/status")
def status():
    tags = load_json(DATA_DIR / "tags.json", {"tags": []})
    return jsonify({"scenes": PRESET_SCENES, "tags": tags.get("tags", []), "scanning": False})

@app.route("/api/pixel/nfc_quick/scan", methods=["POST"])
def scan_tag():
    tag_id = f"tag_{int(time.time())}"
    return jsonify({"ok": True, "tag_id": tag_id, "msg": "Tag detected - assign a scene"})

@app.route("/api/pixel/nfc_quick/assign", methods=["POST"])
def assign_tag():
    data = request.json or {}
    tags = load_json(DATA_DIR / "tags.json", {"tags": []})
    tag = {"id": data.get("tag_id", ""), "scene": data.get("scene", ""), "assigned": time.time()}
    tags["tags"].append(tag)
    save_json(DATA_DIR / "tags.json", tags)
    return jsonify({"ok": True})

@app.route("/api/pixel/nfc_quick/execute", methods=["POST"])
def execute_scene():
    data = request.json or {}
    scene_id = data.get("scene", "")
    for s in PRESET_SCENES:
        if s["id"] == scene_id:
            return jsonify({"ok": True, "scene": s, "executed": s["actions"]})
    return jsonify({"ok": False, "msg": "Scene not found"})

NFC_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>NFC Quick Actions</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.scenes{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-bottom:20px}
.scene{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:12px;padding:16px;text-align:center;cursor:pointer;transition:all 0.3s}
.scene:hover{border-color:var(--color);box-shadow:0 0 15px rgba(0,240,255,0.1)}
.scene-icon{font-size:32px;margin-bottom:8px}
.scene-name{font-family:'Orbitron',monospace;font-size:12px;color:var(--color)}
.scene-actions{font-size:9px;color:#64748b;margin-top:6px}
.tags{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px}
.tag{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px}
.tag-id{color:#00f0ff;font-family:'Share Tech Mono',monospace}
.tag-scene{color:#22c55e}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-size:11px;margin-top:12px}
</style></head><body>
<h1>NFC QUICK ACTIONS</h1>
<div class="scenes" id="scenes"></div>
<button class="btn" onclick="scanTag()">Scan NFC Tag</button>
<div class="tags" style="margin-top:16px"><div style="font-size:12px;color:#00f0ff;font-family:'Orbitron',monospace;margin-bottom:8px">ASSIGNED TAGS</div><div id="tagList"></div></div>
<script>
async function load(){const r=await(await fetch('/api/pixel/nfc_quick/status')).json();document.getElementById('scenes').innerHTML=(r.scenes||[]).map(s=>'<div class="scene" style="--color:'+s.color+'" onclick="execScene(\''+s.id+'\')"><div class="scene-icon">'+String.fromCodePoint(parseInt(s.icon))+'</div><div class="scene-name">'+s.name+'</div><div class="scene-actions">'+s.actions.length+' actions</div></div>').join('');document.getElementById('tagList').innerHTML=(r.tags||[]).map(t=>'<div class="tag"><span class="tag-id">'+t.id+'</span><span class="tag-scene">'+t.scene+'</span></div>').join('')||'<div style="color:#64748b;font-size:11px">No tags assigned</div>'}
async function scanTag(){const r=await(await fetch('/api/pixel/nfc_quick/scan',{method:'POST'})).json();const scene=prompt('Tag detected! Assign scene:\n'+['home','work','night','gym','drive','emergency'].join(', '));if(scene){await fetch('/api/pixel/nfc_quick/assign',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tag_id:r.tag_id,scene})});load()}}
async function execScene(id){await fetch('/api/pixel/nfc_quick/execute',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene:id})});alert('Scene executed!')}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[Idea 8] NFC Quick Actions starting on port 9107...")
    app.run(host="0.0.0.0", port=9107, debug=False)