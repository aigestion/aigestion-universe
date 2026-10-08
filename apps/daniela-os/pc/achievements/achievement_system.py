"""
System 50: Achievement System
Gamification with achievements, XP, levels, and challenges
"""

import json
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


ACHIEVEMENTS = [
    {
        "id": "first_boot",
        "name": "First Boot",
        "desc": "Start your PC for the first time",
        "xp": 50,
        "icon": "128187",
        "category": "system",
    },
    {
        "id": "night_owl",
        "name": "Night Owl",
        "desc": "Use PC past midnight",
        "xp": 30,
        "icon": "127769",
        "category": "time",
    },
    {
        "id": "early_bird",
        "name": "Early Bird",
        "desc": "Use PC before 7 AM",
        "xp": 30,
        "icon": "128038",
        "category": "time",
    },
    {
        "id": "file_master",
        "name": "File Master",
        "desc": "Create 100 files",
        "xp": 100,
        "icon": "128193",
        "category": "files",
    },
    {
        "id": "speed_demon",
        "name": "Speed Demon",
        "desc": "Type over 100 WPM",
        "xp": 200,
        "icon": "128168",
        "category": "typing",
    },
    {
        "id": "marathon",
        "name": "Marathon",
        "desc": "Use PC for 8 hours straight",
        "xp": 150,
        "icon": "127939",
        "category": "time",
    },
    {
        "id": "multitask",
        "name": "Multitasker",
        "desc": "Open 10 apps at once",
        "xp": 80,
        "icon": "128187",
        "category": "productivity",
    },
    {
        "id": "customizer",
        "name": "Customizer",
        "desc": "Change theme 5 times",
        "xp": 60,
        "icon": "127912",
        "category": "desktop",
    },
    {
        "id": "keyboard_warrior",
        "name": "Keyboard Warrior",
        "desc": "Type 10000 keys",
        "xp": 120,
        "icon": "128187",
        "category": "typing",
    },
    {
        "id": "gamer",
        "name": "Gamer",
        "desc": "Launch 5 games",
        "xp": 70,
        "icon": "127918",
        "category": "gaming",
    },
    {
        "id": "clean_desk",
        "name": "Clean Desktop",
        "desc": "Organize all desktop files",
        "xp": 90,
        "icon": "128188",
        "category": "files",
    },
    {
        "id": "night_mode",
        "name": "Night Shift",
        "desc": "Enable night mode",
        "xp": 25,
        "icon": "127769",
        "category": "desktop",
    },
    {
        "id": "social",
        "name": "Social Butterfly",
        "desc": "Share 10 files",
        "xp": 60,
        "icon": "128142",
        "category": "social",
    },
    {
        "id": "backup",
        "name": "Backup Pro",
        "desc": "Create first backup",
        "xp": 100,
        "icon": "128190",
        "category": "files",
    },
    {
        "id": "voice",
        "name": "Voice Commander",
        "desc": "Use voice commands 50 times",
        "xp": 80,
        "icon": "127908",
        "category": "voice",
    },
    {
        "id": "macro",
        "name": "Macro Master",
        "desc": "Create 10 macros",
        "xp": 110,
        "icon": "127918",
        "category": "automation",
    },
    {
        "id": "music",
        "name": "Music Lover",
        "desc": "Listen to music for 2 hours",
        "xp": 50,
        "icon": "127925",
        "category": "media",
    },
    {
        "id": "screenshot",
        "name": "Screenshot King",
        "desc": "Take 50 screenshots",
        "xp": 40,
        "icon": "128247",
        "category": "media",
    },
    {
        "id": "memes",
        "name": "Meme Lord",
        "desc": "Create 10 memes",
        "xp": 70,
        "icon": "128516",
        "category": "creative",
    },
    {
        "id": "streamer",
        "name": "Streamer",
        "desc": "Use stream overlay for 1 hour",
        "xp": 80,
        "icon": "127909",
        "category": "streaming",
    },
]


@app.route("/")
def index():
    return ACH_HTML


@app.route("/api/achievements/list")
def list_achievements():
    state = load_json(
        DATA_DIR / "achievements.json", {"unlocked": [], "xp": 0, "level": 1, "streak": 0}
    )
    result = []
    for a in ACHIEVEMENTS:
        result.append({**a, "unlocked": a["id"] in state.get("unlocked", [])})
    return jsonify(
        {
            "achievements": result,
            "xp": state.get("xp", 0),
            "level": state.get("level", 1),
            "streak": state.get("streak", 0),
        }
    )


@app.route("/api/achievements/unlock", methods=["POST"])
def unlock():
    data = request.json or {}
    ach_id = data.get("id", "")
    state = load_json(
        DATA_DIR / "achievements.json", {"unlocked": [], "xp": 0, "level": 1, "streak": 0}
    )
    if ach_id not in state["unlocked"]:
        state["unlocked"].append(ach_id)
        for a in ACHIEVEMENTS:
            if a["id"] == ach_id:
                state["xp"] += a["xp"]
                state["level"] = 1 + state["xp"] // 500
                break
        save_json(DATA_DIR / "achievements.json", state)
        return jsonify({"ok": True, "xp": state["xp"], "level": state["level"]})
    return jsonify({"ok": False, "msg": "Already unlocked"})


ACH_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Achievement System</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.stats{display:flex;gap:16px;margin-bottom:20px}
.stat-box{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px 20px;text-align:center;min-width:100px}
.stat-val{font-family:'Orbitron',monospace;font-size:22px;color:#00f0ff}
.stat-label{font-size:9px;color:#64748b;letter-spacing:1px;margin-top:4px}
.level-bar{height:6px;background:rgba(0,240,255,0.1);border-radius:3px;margin-top:8px;overflow:hidden}
.level-fill{height:100%;background:linear-gradient(90deg,#00f0ff,#ff0055);border-radius:3px;transition:width 0.5s}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.ach{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;display:flex;gap:10px;align-items:center;transition:all 0.3s}
.ach:hover{border-color:#00f0ff}
.ach.unlocked{border-color:#22c55e;box-shadow:0 0 10px rgba(34,197,94,0.15)}
.ach.locked{opacity:0.4}
.ach-icon{font-size:28px;min-width:36px;text-align:center}
.ach-info{flex:1}
.ach-name{font-family:'Orbitron',monospace;font-size:11px;color:#00f0ff}
.ach-desc{font-size:10px;color:#64748b;margin-top:2px}
.ach-xp{font-size:10px;color:#f59e0b;margin-top:4px}
.ach-badge{font-size:9px;padding:2px 6px;border-radius:4px;background:rgba(34,197,94,0.15);color:#22c55e}
</style></head><body>
<h1>ACHIEVEMENT SYSTEM</h1>
<div class="stats">
  <div class="stat-box"><div class="stat-val" id="level">1</div><div class="stat-label">LEVEL</div><div class="level-bar"><div class="level-fill" id="levelFill" style="width:0%"></div></div></div>
  <div class="stat-box"><div class="stat-val" id="xp">0</div><div class="stat-label">XP</div></div>
  <div class="stat-box"><div class="stat-val" id="unlocked">0</div><div class="stat-label">UNLOCKED</div></div>
  <div class="stat-box"><div class="stat-val" id="total">0</div><div class="stat-label">TOTAL</div></div>
</div>
<div class="grid" id="achs"></div>
<script>
async function load(){
  const r=await(await fetch('/api/achievements/list')).json();
  document.getElementById('level').textContent=r.level;
  document.getElementById('xp').textContent=r.xp;
  document.getElementById('unlocked').textContent=(r.achievements||[]).filter(a=>a.unlocked).length;
  document.getElementById('total').textContent=(r.achievements||[]).length;
  document.getElementById('levelFill').style.width=((r.xp%500)/5)+'%';
  document.getElementById('achs').innerHTML=(r.achievements||[]).map(a=>
    '<div class="ach '+(a.unlocked?'unlocked':'locked')+'" onclick="unlock(\''+a.id+'\')">'+
    '<div class="ach-icon">'+String.fromCodePoint(parseInt(a.icon||'127918'))+'</div>'+
    '<div class="ach-info"><div class="ach-name">'+a.name+'</div><div class="ach-desc">'+a.desc+'</div>'+
    '<div class="ach-xp">'+a.xp+' XP</div></div>'+
    (a.unlocked?'<div class="ach-badge">UNLOCKED</div>':'')+'</div>'
  ).join('');
}
async function unlock(id){await fetch('/api/achievements/unlock',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 50] Achievement System starting on port 5060...")
    app.run(host="0.0.0.0", port=5060, debug=False)
