"""
System 15: Focus Mode
Productivity mode - blocks distractions, plays lo-fi, shows only what you need
"""

import json
import time
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

FOCUS_FILE = DATA_DIR / "focus_state.json"


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


DISTRACTION_APPS = ["chrome", "firefox", "discord", "slack", "spotify", "steam", "epicgames"]
FOCUS_STATES = {}


@app.route("/")
def index():
    return FOCUS_HTML


@app.route("/api/focus/status")
def status():
    state = load_json(FOCUS_FILE, {"active": False, "started": 0, "elapsed": 0})
    if state["active"] and state.get("started"):
        state["elapsed"] = int(time.time() - state["started"])
    return jsonify(state)


@app.route("/api/focus/start", methods=["POST"])
def start_focus():
    data = request.json or {}
    state = {
        "active": True,
        "started": time.time(),
        "duration": data.get("duration", 25) * 60,
        "mode": data.get("mode", "pomodoro"),
        "blocked_apps": data.get("blocked", DISTRACTION_APPS),
        "music": data.get("music", "lofi"),
        "task": data.get("task", ""),
    }
    save_json(FOCUS_FILE, state)
    return jsonify({"ok": True})


@app.route("/api/focus/stop", methods=["POST"])
def stop_focus():
    state = load_json(FOCUS_FILE, {"active": False})
    if state.get("started"):
        state["elapsed"] = int(time.time() - state["started"])
    state["active"] = False
    save_json(FOCUS_FILE, state)
    return jsonify({"ok": True})


@app.route("/api/focus/sessions")
def sessions():
    log = load_json(DATA_DIR / "sessions.json", {"sessions": []})
    return jsonify(log)


@app.route("/api/focus/timer")
def timer():
    state = load_json(FOCUS_FILE, {"active": False, "started": 0, "duration": 1500})
    if not state["active"]:
        return jsonify({"remaining": 0, "active": False})
    elapsed = time.time() - state.get("started", time.time())
    remaining = max(0, state.get("duration", 1500) - elapsed)
    if remaining <= 0:
        state["active"] = False
        save_json(FOCUS_FILE, state)
    return jsonify(
        {
            "remaining": int(remaining),
            "active": state["active"],
            "total": state.get("duration", 1500),
        }
    )


FOCUS_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Focus Mode</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px;display:flex;flex-direction:column;align-items:center;min-height:100vh}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:30px}
.timer{font-family:'Orbitron',monospace;font-size:72px;color:#00f0ff;text-shadow:0 0 40px rgba(0,240,255,0.3);margin:20px 0}
.timer.active{color:#22c55e;text-shadow:0 0 40px rgba(34,197,94,0.3)}
.timer.done{color:#ff0055;text-shadow:0 0 40px rgba(255,0,85,0.3)}
.task-input{background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.2);color:#e2e8f0;padding:12px 20px;border-radius:8px;font-size:16px;font-family:inherit;width:400px;text-align:center;margin-bottom:20px}
.task-input:focus{outline:none;border-color:#00f0ff}
.controls{display:flex;gap:12px;margin:20px 0}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:12px 24px;border-radius:8px;cursor:pointer;font-family:inherit;font-size:14px}
.btn:hover{background:rgba(0,240,255,0.2)}
.btn.green{border-color:#22c55e;color:#22c55e}
.btn.red{border-color:#ff0055;color:#ff0055}
.modes{display:flex;gap:8px;margin:20px 0}
.mode-btn{background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.15);color:#94a3b8;padding:8px 16px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:12px}
.mode-btn.active{border-color:#00f0ff;color:#00f0ff;background:rgba(0,240,255,0.1)}
.stats{position:fixed;bottom:20px;right:20px;font-size:10px;color:#64748b;font-family:'Share Tech Mono',monospace}
.particles{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none}
</style></head><body>
<div class="particles" id="particles"></div>
<h1>FOCUS MODE</h1>
<input class="task-input" id="task" placeholder="What are you working on?">
<div class="modes">
  <button class="mode-btn active" onclick="setMode(this,25)">Pomodoro (25m)</button>
  <button class="mode-btn" onclick="setMode(this,15)">Short (15m)</button>
  <button class="mode-btn" onclick="setMode(this,50)">Deep (50m)</button>
  <button class="mode-btn" onclick="setMode(this,5)">Break (5m)</button>
</div>
<div class="timer" id="timer">25:00</div>
<div class="controls">
  <button class="btn green" onclick="startFocus()">Start Focus</button>
  <button class="btn red" onclick="stopFocus()">Stop</button>
</div>
<div class="stats" id="stats"></div>
<script>
let duration=25*60,mode='pomodoro';
function setMode(el,m){duration=m*60;mode=m<=10?'break':m<=20?'short':m<=30?'pomodoro':'deep';document.querySelectorAll('.mode-btn').forEach(b=>b.classList.remove('active'));el.classList.add('active');updateTimer()}
async function startFocus(){
  const task=document.getElementById('task').value;
  await fetch('/api/focus/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({duration:duration/60,mode,task})});
  pollTimer();
}
async function stopFocus(){await fetch('/api/focus/stop',{method:'POST'})}
async function pollTimer(){
  const r=await(await fetch('/api/focus/timer')).json();
  if(r.active){updateDisplay(r.remaining);setTimeout(pollTimer,1000)}
  else{document.getElementById('timer').textContent='00:00';document.getElementById('timer').className='timer done'}
}
function updateDisplay(s){const m=Math.floor(s/60),sec=s%60;const el=document.getElementById('timer');el.textContent=String(m).padStart(2,'0')+':'+String(sec).padStart(2,'0');el.className='timer active'}
function updateTimer(){const m=Math.floor(duration/60),sec=duration%60;document.getElementById('timer').textContent=String(m).padStart(2,'0')+':'+String(sec).padStart(2,'0')}
updateTimer();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 15] Focus Mode starting on port 5025...")
    app.run(host="0.0.0.0", port=5025, debug=False)
