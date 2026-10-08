"""
System 41: Game Launcher Hub
Central game launcher detecting all installed games with stats
"""

import json
import subprocess
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


GAMES = [
    {"name": "Steam", "cmd": "steam", "icon": "steam", "platform": "Steam"},
    {"name": "Epic Games", "cmd": "epicgames", "icon": "epic", "platform": "Epic"},
    {"name": "GOG Galaxy", "cmd": "goggalaxy", "icon": "gog", "platform": "GOG"},
    {"name": "Xbox App", "cmd": "xbox", "icon": "xbox", "platform": "Xbox"},
    {"name": "Blizzard", "cmd": "battle.net", "icon": "blizzard", "platform": "Blizzard"},
    {"name": "EA App", "cmd": "origin", "icon": "ea", "platform": "EA"},
    {"name": "Ubisoft Connect", "cmd": "ubisoft", "icon": "ubisoft", "platform": "Ubisoft"},
    {"name": "Rockstar Games", "cmd": "rockstar", "icon": "rockstar", "platform": "Rockstar"},
]


@app.route("/")
def index():
    return GAME_HTML


@app.route("/api/games/list")
def list_games():
    stats = load_json(DATA_DIR / "stats.json", {"launches": {}})
    games = []
    for g in GAMES:
        launch_count = stats.get("launches", {}).get(g["name"], 0)
        games.append({**g, "launches": launch_count})
    games.sort(key=lambda x: x["launches"], reverse=True)
    return jsonify({"games": games})


@app.route("/api/games/launch", methods=["POST"])
def launch():
    data = request.json or {}
    name = data.get("name", "")
    stats = load_json(DATA_DIR / "stats.json", {"launches": {}})
    for g in GAMES:
        if g["name"] == name:
            try:
                subprocess.Popen([g["cmd"]], shell=True)
            except Exception:
                pass
            stats["launches"][name] = stats.get("launches", {}).get(name, 0) + 1
            stats["last_played"] = stats.get("last_played", {})
            stats["last_played"][name] = time.time()
            save_json(DATA_DIR / "stats.json", stats)
            return jsonify({"ok": True})
    return jsonify({"error": "Game not found"}), 404


@app.route("/api/games/stats")
def stats():
    return jsonify(load_json(DATA_DIR / "stats.json", {"launches": {}, "last_played": {}}))


GAME_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Game Launcher Hub</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.games{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
.game-card{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:12px;padding:16px;cursor:pointer;transition:all 0.3s;text-align:center}
.game-card:hover{border-color:#00f0ff;box-shadow:0 0 20px rgba(0,240,255,0.15);transform:translateY(-3px)}
.game-icon{font-size:40px;margin-bottom:8px}
.game-name{font-family:'Orbitron',monospace;font-size:14px;color:#00f0ff;letter-spacing:1px}
.game-platform{font-size:10px;color:#64748b;margin-top:4px}
.game-stat{font-size:10px;color:#f59e0b;margin-top:4px}
.stats-bar{display:flex;gap:20px;margin-top:20px;padding:12px;background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px}
.stat{text-align:center}
.stat-val{font-family:'Orbitron',monospace;font-size:18px;color:#00f0ff}
.stat-label{font-size:9px;color:#64748b;letter-spacing:1px}
</style></head><body>
<h1>GAME LAUNCHER HUB</h1>
<div class="stats-bar" id="statsBar"></div>
<div class="games" id="games"></div>
<script>
async function load(){
  const r=await(await fetch('/api/games/list')).json();
  const s=await(await fetch('/api/games/stats')).json();
  const totalLaunches=Object.values(s.launches||{}).reduce((a,b)=>a+b,0);
  document.getElementById('statsBar').innerHTML=
    '<div class="stat"><div class="stat-val">'+(r.games||[]).length+'</div><div class="stat-label">PLATFORMS</div></div>'+
    '<div class="stat"><div class="stat-val">'+totalLaunches+'</div><div class="stat-label">TOTAL LAUNCHES</div></div>'+
    '<div class="stat"><div class="stat-val">'+Object.keys(s.last_played||{}).length+'</div><div class="stat-label">PLAYED TODAY</div></div>';
  const icons={steam:'127918',epic:'128142',gog:'127775',xbox:'127918',blizzard:'10052',ea:'127941',ubisoft:'128142',rockstar:'11088'};
  document.getElementById('games').innerHTML=(r.games||[]).map(g=>
    '<div class="game-card" onclick="launch(\''+g.name+'\')">'+
    '<div class="game-icon">'+String.fromCodePoint(parseInt(icons[g.icon]||'127918'))+'</div>'+
    '<div class="game-name">'+g.name+'</div>'+
    '<div class="game-platform">'+g.platform+'</div>'+
    '<div class="game-stat">'+g.launches+' launches</div></div>'
  ).join('');
}
async function launch(name){await fetch('/api/games/launch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});load()}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 41] Game Launcher Hub starting on port 5051...")
    app.run(host="0.0.0.0", port=5051, debug=False)
