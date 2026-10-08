"""
System 8: Predictive App Launcher
AI learns your patterns and suggests apps before you click
"""

import json
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

PATTERNS_FILE = Path(__file__).parent / "patterns.json"
LAUNCH_LOG = Path(__file__).parent / "launch_log.json"


def load_json(path, default=None):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# Default apps
APPS = {
    "chrome": {"name": "Chrome", "cmd": "chrome", "icon": "🌐"},
    "vscode": {"name": "VS Code", "cmd": "code", "icon": "💻"},
    "windsurf": {"name": "Windsurf", "cmd": "windsurf", "icon": "🏄"},
    "slack": {"name": "Slack", "cmd": "slack", "icon": "💬"},
    "discord": {"name": "Discord", "cmd": "discord", "icon": "🎮"},
    "spotify": {"name": "Spotify", "cmd": "spotify", "icon": "🎵"},
    "notepad": {"name": "Notepad", "cmd": "notepad", "icon": "📝"},
    "explorer": {"name": "Explorer", "cmd": "explorer", "icon": "📁"},
    "terminal": {"name": "Terminal", "cmd": "wt", "icon": "⬛"},
    "blender": {"name": "Blender", "cmd": "blender", "icon": "🧊"},
    "obsidian": {"name": "Obsidian", "cmd": "obsidian", "icon": "🔮"},
    "calc": {"name": "Calculator", "cmd": "calc", "icon": "🔢"},
}


def get_time_slot():
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "afternoon"
    if 18 <= hour < 22:
        return "evening"
    return "night"


def get_day_type():
    weekday = datetime.now().weekday()
    return "weekday" if weekday < 5 else "weekend"


@app.route("/")
def index():
    return LAUNCHER_HTML


@app.route("/api/launcher/apps")
def list_apps():
    return jsonify({"apps": APPS})


@app.route("/api/launcher/launch", methods=["POST"])
def launch_app():
    data = request.json or {}
    app_id = data.get("app", "")
    if app_id not in APPS:
        return jsonify({"error": "Unknown app"}), 400

    import subprocess

    try:
        subprocess.Popen([APPS[app_id]["cmd"]], shell=True)
    except Exception:
        pass

    # Log the launch
    log = load_json(LAUNCH_LOG, {"launches": []})
    log["launches"].append(
        {
            "app": app_id,
            "timestamp": time.time(),
            "time_slot": get_time_slot(),
            "day_type": get_day_type(),
            "hour": datetime.now().hour,
        }
    )
    log["launches"] = log["launches"][-500:]
    save_json(LAUNCH_LOG, log)

    return jsonify({"ok": True, "app": APPS[app_id]["name"]})


@app.route("/api/launcher/suggestions")
def suggestions():
    log = load_json(LAUNCH_LOG, {"launches": []})
    time_slot = get_time_slot()
    day_type = get_day_type()
    hour = datetime.now().hour

    # Count app launches by time slot and day type
    app_counts = defaultdict(int)
    for launch in log["launches"]:
        if launch["time_slot"] == time_slot:
            app_counts[launch["app"]] += 2  # Weight by time match
        if launch["day_type"] == day_type:
            app_counts[launch["app"]] += 1  # Weight by day match
        if abs(launch.get("hour", 12) - hour) <= 1:
            app_counts[launch["app"]] += 3  # Weight by hour match

    # Sort by score
    sorted_apps = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)

    # Always include some defaults if no data
    if not sorted_apps:
        sorted_apps = [("chrome", 5), ("vscode", 4), ("slack", 3), ("terminal", 2)]

    suggestions = []
    for app_id, score in sorted_apps[:6]:
        if app_id in APPS:
            suggestions.append(
                {
                    "id": app_id,
                    "name": APPS[app_id]["name"],
                    "icon": APPS[app_id]["icon"],
                    "confidence": min(100, score * 10),
                }
            )

    return jsonify(
        {
            "suggestions": suggestions,
            "time_slot": time_slot,
            "day_type": day_type,
            "total_launches": len(log["launches"]),
        }
    )


LAUNCHER_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Predictive App Launcher</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#030814; color:#e2e8f0; font-family:'Rajdhani',sans-serif; padding:30px; }
h1 { font-family:'Orbitron',monospace; color:#00f0ff; font-size:20px; letter-spacing:3px; margin-bottom:8px; }
.subtitle { font-size:12px; color:#64748b; margin-bottom:24px; }
.section { margin-bottom:24px; }
.section h2 { font-size:13px; color:#00f0ff; font-family:'Orbitron',monospace; letter-spacing:1px; margin-bottom:12px; }
.suggestions { display:flex; gap:12px; flex-wrap:wrap; }
.suggest-card { background:rgba(0,240,255,0.05); border:1px solid rgba(0,240,255,0.2); border-radius:12px; padding:16px; text-align:center; cursor:pointer; transition:all 0.3s; min-width:100px; }
.suggest-card:hover { border-color:#00f0ff; box-shadow:0 0 20px rgba(0,240,255,0.2); transform:translateY(-3px); }
.suggest-icon { font-size:32px; margin-bottom:6px; }
.suggest-name { font-size:11px; font-family:'Share Tech Mono',monospace; }
.suggest-conf { font-size:9px; color:#22c55e; margin-top:4px; }
.all-apps { display:grid; grid-template-columns:repeat(auto-fill, minmax(80px,1fr)); gap:8px; }
.app-card { background:rgba(3,8,20,0.8); border:1px solid rgba(0,240,255,0.1); border-radius:8px; padding:12px 8px; text-align:center; cursor:pointer; transition:all 0.2s; }
.app-card:hover { border-color:#00f0ff; transform:scale(1.05); }
.app-icon { font-size:24px; margin-bottom:4px; }
.app-name { font-size:9px; color:#94a3b8; }
.stats { position:fixed; bottom:20px; right:20px; font-size:10px; color:#64748b; font-family:'Share Tech Mono',monospace; }
</style></head><body>
<h1>🚀 PREDICTIVE LAUNCHER</h1>
<div class="subtitle">AI learns your patterns - apps appear before you need them</div>
<div class="section">
  <h2>💡 SUGGESTED FOR YOU</h2>
  <div class="suggestions" id="suggestions"></div>
</div>
<div class="section">
  <h2>📱 ALL APPS</h2>
  <div class="all-apps" id="allApps"></div>
</div>
<div class="stats" id="stats"></div>
<script>
async function load() {
  const s = await (await fetch('/api/launcher/suggestions')).json();
  document.getElementById('suggestions').innerHTML = s.suggestions.map(a =>
    '<div class="suggest-card" onclick="launch(\'' + a.id + '\')">' +
    '<div class="suggest-icon">' + a.icon + '</div>' +
    '<div class="suggest-name">' + a.name + '</div>' +
    '<div class="suggest-conf">' + a.confidence + '% match</div></div>'
  ).join('');

  const apps = await (await fetch('/api/launcher/apps')).json();
  document.getElementById('allApps').innerHTML = Object.entries(apps.apps).map(([id,a]) =>
    '<div class="app-card" onclick="launch(\'' + id + '\')">' +
    '<div class="app-icon">' + a.icon + '</div>' +
    '<div class="app-name">' + a.name + '</div></div>'
  ).join('');

  document.getElementById('stats').textContent = s.time_slot + ' | ' + s.day_type + ' | ' + s.total_launches + ' launches logged';
}
async function launch(id) {
  await fetch('/api/launcher/launch', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({app:id})});
  load();
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 8] Predictive App Launcher starting on port 5017...")
    app.run(host="0.0.0.0", port=5017, debug=False)
