"""
System 57: Parental Controls
Screen time and content controls
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


@app.route("/")
def index():
    return PARENT_HTML


@app.route("/api/parental/settings")
def settings():
    return jsonify(
        load_json(
            DATA_DIR / "parental.json",
            {
                "screen_time_limit": 120,
                "bedtime": "22:00",
                "wake_time": "07:00",
                "blocked_sites": ["facebook.com", "tiktok.com"],
                "web_filter": True,
                "app_lock": True,
                "time_alerts": True,
                "daily_reset": True,
            },
        )
    )


@app.route("/api/parental/update", methods=["POST"])
def update():
    data = request.json or {}
    settings = load_json(DATA_DIR / "parental.json", {"screen_time_limit": 120})
    settings.update(data)
    save_json(DATA_DIR / "parental.json", settings)
    return jsonify({"ok": True})


@app.route("/api/parental/logs")
def logs():
    return jsonify(
        {
            "logs": [
                {"time": "14:30", "event": "Screen time alert: 2 hours used", "type": "alert"},
                {"time": "13:15", "event": "Blocked site attempted: facebook.com", "type": "block"},
                {"time": "12:00", "event": "Session started", "type": "info"},
                {"time": "09:30", "event": "Daily timer reset", "type": "info"},
            ]
        }
    )


PARENT_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Parental Controls</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px}
.stat-box{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;text-align:center}
.stat-val{font-family:'Orbitron',monospace;font-size:22px;color:#00f0ff}
.stat-label{font-size:9px;color:#64748b;letter-spacing:1px;margin-top:4px}
.controls{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px;margin-bottom:20px}
.control{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px}
.control-title{font-family:'Orbitron',monospace;font-size:11px;color:#00f0ff;margin-bottom:8px}
.switch{width:44px;height:24px;background:rgba(0,240,255,0.1);border:1px solid rgba(0,240,255,0.2);border-radius:12px;cursor:pointer;position:relative;display:inline-block}
.switch.on{background:rgba(0,240,255,0.2);border-color:#00f0ff}
.switch::after{content:'';position:absolute;top:2px;left:2px;width:18px;height:18px;background:#00f0ff;border-radius:50%;transition:0.3s}
.switch.on::after{left:22px}
.input{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:6px 10px;border-radius:6px;font-family:inherit;font-size:12px;width:100%;margin-top:6px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:10px;font-family:inherit;margin-top:6px}
.blocked{margin-top:10px}
.blocked-tag{display:inline-block;background:rgba(255,0,85,0.1);border:1px solid rgba(255,0,85,0.2);color:#ff0055;padding:2px 8px;border-radius:4px;font-size:10px;margin:2px}
.log{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px}
.log-entry{font-size:10px;padding:4px 0;border-bottom:1px solid rgba(0,240,255,0.05);display:flex;gap:8px}
.log-time{color:#00f0ff;font-family:'Share Tech Mono',monospace;width:40px}
.log-alert{color:#ff0055}.log-block{color:#f59e0b}.log-info{color:#22c55e}
</style></head><body>
<h1>PARENTAL CONTROLS</h1>
<div class="stats">
  <div class="stat-box"><div class="stat-val" id="screenTime">0h</div><div class="stat-label">TODAY</div></div>
  <div class="stat-box"><div class="stat-val" id="limit">2h</div><div class="stat-label">LIMIT</div></div>
  <div class="stat-box"><div class="stat-val" id="blocked">2</div><div class="stat-label">BLOCKED</div></div>
  <div class="stat-box"><div class="stat-val" id="remaining">2h</div><div class="stat-label">REMAINING</div></div>
</div>
<div class="controls">
  <div class="control"><div class="control-title">Web Filter</div><div class="switch on" onclick="this.classList.toggle('on')"></div>
    <div class="blocked"><span class="blocked-tag">facebook.com</span><span class="blocked-tag">tiktok.com</span></div></div>
  <div class="control"><div class="control-title">App Lock</div><div class="switch on" onclick="this.classList.toggle('on')"></div>
    <input class="input" placeholder="Add app to block..."></div>
  <div class="control"><div class="control-title">Screen Time Limit</div>
    <input class="input" type="time" value="02:00" id="timeLimit"></div>
  <div class="control"><div class="control-title">Bedtime</div>
    <input class="input" type="time" value="22:00" id="bedtime"></div>
  <div class="control"><div class="control-title">Time Alerts</div><div class="switch on" onclick="this.classList.toggle('on')"></div></div>
  <div class="control"><div class="control-title">Daily Reset</div><div class="switch on" onclick="this.classList.toggle('on')"></div></div>
</div>
<div class="log"><div style="font-size:12px;color:#00f0ff;font-family:'Orbitron',monospace;margin-bottom:8px">ACTIVITY LOG</div>
  <div class="log-entry"><span class="log-time log-alert">14:30</span>Screen time alert: 2 hours used</div>
  <div class="log-entry"><span class="log-time log-block">13:15</span>Blocked site attempted: facebook.com</div>
  <div class="log-entry"><span class="log-time log-info">12:00</span>Session started</div>
  <div class="log-entry"><span class="log-time log-info">09:30</span>Daily timer reset</div>
</div>
<script>
document.getElementById('screenTime').textContent='1h 45m';
document.getElementById('remaining').textContent='15m';
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 57] Parental Controls starting on port 5067...")
    app.run(host="0.0.0.0", port=5067, debug=False)
