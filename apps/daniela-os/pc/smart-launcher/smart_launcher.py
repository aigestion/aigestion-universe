"""
System 38: Smart App Launcher 2.0
Fuzzy search launcher for apps, files, folders, URLs, commands
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


APPS = [
    {"name": "Chrome", "cmd": "chrome", "icon": "globe", "cat": "browser"},
    {"name": "VS Code", "cmd": "code", "icon": "code", "cat": "editor"},
    {"name": "Windsurf", "cmd": "windsurf", "icon": "code", "cat": "editor"},
    {"name": "Terminal", "cmd": "wt", "icon": "terminal", "cat": "system"},
    {"name": "Explorer", "cmd": "explorer", "icon": "folder", "cat": "system"},
    {"name": "Calculator", "cmd": "calc", "icon": "calc", "cat": "tools"},
    {"name": "Notepad", "cmd": "notepad", "icon": "notepad", "cat": "editor"},
    {"name": "Spotify", "cmd": "spotify", "icon": "music", "cat": "media"},
    {"name": "Discord", "cmd": "discord", "icon": "chat", "cat": "social"},
    {"name": "Slack", "cmd": "slack", "icon": "chat", "cat": "social"},
    {"name": "Blender", "cmd": "blender", "icon": "cube", "cat": "creative"},
    {"name": "OBS", "cmd": "obs", "icon": "video", "cat": "media"},
    {"name": "Steam", "cmd": "steam", "icon": "game", "cat": "gaming"},
    {"name": "Photoshop", "cmd": "photoshop", "icon": "image", "cat": "creative"},
]


@app.route("/")
def index():
    return LAUNCHER_HTML


@app.route("/api/launcher/search")
def search():
    q = request.args.get("q", "").lower()
    results = []
    for app in APPS:
        score = 0
        if q in app["name"].lower():
            score += 5
        if q in app.get("cat", "").lower():
            score += 2
        words = q.split()
        for w in words:
            if w in app["name"].lower():
                score += 3
        if not q:
            score = 1
        if score > 0:
            app["score"] = score
            results.append(app)
    results.sort(key=lambda x: x["score"], reverse=True)
    return jsonify({"results": results[:10]})


@app.route("/api/launcher/launch", methods=["POST"])
def launch():
    data = request.json or {}
    cmd = data.get("cmd", "")
    try:
        subprocess.Popen([cmd], shell=True)
    except Exception:
        pass
    log = load_json(DATA_DIR / "launch_log.json", {"launches": []})
    log["launches"].append({"cmd": cmd, "time": time.time()})
    log["launches"] = log["launches"][-100:]
    save_json(DATA_DIR / "launch_log.json", log)
    return jsonify({"ok": True})


LAUNCHER_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Smart App Launcher 2.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
.launcher{width:500px;background:rgba(3,8,20,0.95);border:1px solid rgba(0,240,255,0.2);border-radius:16px;padding:20px;backdrop-filter:blur(20px)}
input{width:100%;background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.2);color:#e2e8f0;padding:14px 18px;border-radius:10px;font-size:18px;font-family:inherit;margin-bottom:12px}
input:focus{outline:none;border-color:#00f0ff}
.result{display:flex;align-items:center;gap:12px;padding:10px;border-radius:8px;cursor:pointer;transition:all 0.2s}
.result:hover,.result.selected{background:rgba(0,240,255,0.1);border-color:#00f0ff}
.result-icon{font-size:24px;width:36px;text-align:center}
.result-name{font-size:14px;color:#e2e8f0}
.result-cmd{font-size:10px;color:#64748b;font-family:'Share Tech Mono',monospace}
.result-cat{font-size:9px;color:#00f0ff;background:rgba(0,240,255,0.08);padding:1px 6px;border-radius:3px}
.hint{font-size:10px;color:#475569;text-align:center;margin-top:12px}
</style></head><body>
<div class="launcher">
  <input id="search" placeholder="Search apps, files, commands..." autofocus oninput="search()" onkeydown="handleKey(event)">
  <div id="results"></div>
  <div class="hint">Type to search | Enter to launch | Arrow keys to navigate</div>
</div>
<script>
let selected=0;let results=[];
const iconMap={globe:'127760',code:'128187',terminal:'128187',folder:'128194',calc:'128290',notepad:'128221',music:'127925',chat:'128172',cube:'129513',video:'127909',game:'127918',image:'127748'};
function getIcon(name){return String.fromCodePoint(parseInt(iconMap[name]||'128375'))}
async function search(){
  const q=document.getElementById('search').value;
  const r=await(await fetch('/api/launcher/search?q='+encodeURIComponent(q))).json();
  results=r.results||[];
  selected=0;
  render();
}
function render(){
  document.getElementById('results').innerHTML=results.map((r,i)=>
    '<div class="result'+(i===selected?' selected':'')+'" onclick="launch(\''+r.cmd+'\')">'+
    '<div class="result-icon">'+getIcon(r.icon)+'</div>'+
    '<div><div class="result-name">'+r.name+'</div><div class="result-cmd">'+r.cmd+'</div></div>'+
    '<div class="result-cat">'+r.cat+'</div></div>'
  ).join('');
}
function handleKey(e){
  if(e.key==='ArrowDown'){selected=Math.min(selected+1,results.length-1);render()}
  else if(e.key==='ArrowUp'){selected=Math.max(selected-1,0);render()}
  else if(e.key==='Enter'&&results[selected]){launch(results[selected].cmd)}
}
async function launch(cmd){await fetch('/api/launcher/launch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd})})}
search();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 38] Smart App Launcher 2.0 starting on port 5048...")
    app.run(host="0.0.0.0", port=5048, debug=False)
