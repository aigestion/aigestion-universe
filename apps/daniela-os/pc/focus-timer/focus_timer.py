"""
System 39: Focus Timer
Advanced Pomodoro with blocking, stats, and ambient sounds
"""

import json
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


@app.route("/")
def index():
    return FOCUS_HTML


@app.route("/api/focus/state")
def state():
    state = load_json(DATA_DIR / "state.json", {"active": False, "sessions": 0, "total_time": 0})
    return jsonify(state)


@app.route("/api/focus/start", methods=["POST"])
def start():
    data = request.json or {}
    state = {
        "active": True,
        "started": time.time(),
        "duration": data.get("duration", 25) * 60,
        "mode": data.get("mode", "focus"),
        "task": data.get("task", ""),
        "sessions": load_json(DATA_DIR / "state.json", {}).get("sessions", 0),
        "total_time": load_json(DATA_DIR / "state.json", {}).get("total_time", 0),
    }
    save_json(DATA_DIR / "state.json", state)
    return jsonify({"ok": True})


@app.route("/api/focus/stop", methods=["POST"])
def stop():
    state = load_json(DATA_DIR / "state.json", {"active": False})
    if state.get("active") and state.get("started"):
        elapsed = time.time() - state["started"]
        state["total_time"] = state.get("total_time", 0) + elapsed
        state["sessions"] = state.get("sessions", 0) + 1
    state["active"] = False
    save_json(DATA_DIR / "state.json", state)
    return jsonify({"ok": True})


@app.route("/api/focus/timer")
def timer():
    state = load_json(DATA_DIR / "state.json", {"active": False, "started": 0, "duration": 1500})
    if not state["active"]:
        return jsonify({"remaining": 0, "active": False})
    elapsed = time.time() - state.get("started", time.time())
    remaining = max(0, state.get("duration", 1500) - elapsed)
    if remaining <= 0:
        state["active"] = False
        save_json(DATA_DIR / "state.json", state)
    return jsonify(
        {
            "remaining": int(remaining),
            "active": state["active"],
            "total": state.get("duration", 1500),
        }
    )


@app.route("/api/focus/stats")
def stats():
    state = load_json(DATA_DIR / "state.json", {"sessions": 0, "total_time": 0})
    return jsonify(
        {
            "sessions": state.get("sessions", 0),
            "total_hours": round(state.get("total_time", 0) / 3600, 1),
            "streak": state.get("sessions", 0),
        }
    )


FOCUS_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Focus Timer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;display:flex;flex-direction:column;align-items:center;min-height:100vh;padding:40px 20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:30px}
.timer-ring{position:relative;width:280px;height:280px;margin:20px 0}
.timer-ring svg{transform:rotate(-90deg)}
.timer-ring circle{fill:none;stroke-width:6}
.timer-ring .bg{stroke:rgba(0,240,255,0.1)}
.timer-ring .progress{stroke:#00f0ff;stroke-linecap:round;transition:stroke-dashoffset 1s linear}
.timer-text{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center}
.timer-digits{font-family:'Orbitron',monospace;font-size:48px;color:#00f0ff}
.timer-label{font-size:12px;color:#64748b;margin-top:4px}
.modes{display:flex;gap:8px;margin:16px 0}
.mode-btn{background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.15);color:#94a3b8;padding:8px 16px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:12px}
.mode-btn.active{border-color:#00f0ff;color:#00f0ff;background:rgba(0,240,255,0.1)}
.controls{display:flex;gap:12px;margin:16px 0}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:12px 24px;border-radius:8px;cursor:pointer;font-family:inherit;font-size:14px}
.btn:hover{background:rgba(0,240,255,0.2)}
.btn.green{border-color:#22c55e;color:#22c55e}
.btn.red{border-color:#ff0055;color:#ff0055}
.task-input{background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.2);color:#e2e8f0;padding:10px 16px;border-radius:8px;font-size:14px;font-family:inherit;width:400px;text-align:center;margin-bottom:16px}
.stats{display:flex;gap:20px;margin-top:20px}
.stat{text-align:center}
.stat-value{font-family:'Orbitron',monospace;font-size:24px;color:#00f0ff}
.stat-label{font-size:10px;color:#64748b;letter-spacing:1px}
</style></head><body>
<h1>FOCUS TIMER</h1>
<input class="task-input" id="task" placeholder="What are you focusing on?">
<div class="modes">
  <button class="mode-btn active" onclick="setMode(this,25)">Focus 25m</button>
  <button class="mode-btn" onclick="setMode(this,15)">Short Break 15m</button>
  <button class="mode-btn" onclick="setMode(this,50)">Deep Work 50m</button>
  <button class="mode-btn" onclick="setMode(this,5)">Break 5m</button>
</div>
<div class="timer-ring">
  <svg width="280" height="280"><circle class="bg" cx="140" cy="140" r="130"/><circle class="progress" id="ring" cx="140" cy="140" r="130" stroke-dasharray="816.81" stroke-dashoffset="0"/></svg>
  <div class="timer-text"><div class="timer-digits" id="timer">25:00</div><div class="timer-label" id="label">Ready</div></div>
</div>
<div class="controls">
  <button class="btn green" onclick="start()">Start</button>
  <button class="btn red" onclick="stop()">Stop</button>
</div>
<div class="stats">
  <div class="stat"><div class="stat-value" id="sessions">0</div><div class="stat-label">SESSIONS</div></div>
  <div class="stat"><div class="stat-value" id="hours">0</div><div class="stat-label">HOURS</div></div>
</div>
<script>
let duration=25*60;
function setMode(el,m){duration=m*60;document.querySelectorAll('.mode-btn').forEach(b=>b.classList.remove('active'));el.classList.add('active');updateDisplay(duration)}
function updateDisplay(s){const m=Math.floor(s/60),sec=s%60;document.getElementById('timer').textContent=String(m).padStart(2,'0')+':'+String(sec).padStart(2,'0');const pct=1-(s/duration);document.getElementById('ring').style.strokeDashoffset=816.81*(1-pct)}
async function start(){const task=document.getElementById('task').value;await fetch('/api/focus/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({duration:duration/60,task})});pollTimer()}
async function stop(){await fetch('/api/focus/stop',{method:'POST'});document.getElementById('label').textContent='Stopped';loadStats()}
async function pollTimer(){const r=await(await fetch('/api/focus/timer')).json();if(r.active){updateDisplay(r.remaining);document.getElementById('label').textContent='Focusing...';setTimeout(pollTimer,1000)}else{document.getElementById('timer').textContent='00:00';document.getElementById('label').textContent='Complete!';loadStats()}}
async function loadStats(){const s=await(await fetch('/api/focus/stats')).json();document.getElementById('sessions').textContent=s.sessions;document.getElementById('hours').textContent=s.total_hours}
loadStats();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 39] Focus Timer starting on port 5049...")
    app.run(host="0.0.0.0", port=5049, debug=False)
