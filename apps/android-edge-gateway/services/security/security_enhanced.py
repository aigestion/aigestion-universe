# -*- coding: utf-8 -*-
"""
Idea 7: Security Enhanced
Advanced security camera with cloud sync and smart alerts.
"""

import os
import json
import time
import subprocess
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent.parent / "data" / "security"
DATA_DIR.mkdir(parents=True, exist_ok=True)

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
    return SECURITY_HTML

@app.route("/api/pixel/security2/status")
def status():
    settings = load_json(DATA_DIR / "settings.json", {
        "enabled": False, "motion_sensitivity": 30, "night_mode": True,
        "alert_on_motion": True, "max_photos": 500
    })
    events = load_json(DATA_DIR / "events.json", {"events": []})
    stats = {"total_events": len(events["events"]), "today_events": 0}
    today = time.strftime("%Y-%m-%d")
    for e in events["events"]:
        if time.strftime("%Y-%m-%d", time.localtime(e.get("time", 0))) == today:
            stats["today_events"] += 1
    return jsonify({"settings": settings, "stats": stats, "events": events["events"][-20:]})

@app.route("/api/pixel/security2/start", methods=["POST"])
def start():
    settings = load_json(DATA_DIR / "settings.json", {"enabled": False})
    settings["enabled"] = True
    save_json(DATA_DIR / "settings.json", settings)
    return jsonify({"ok": True})

@app.route("/api/pixel/security2/stop", methods=["POST"])
def stop():
    settings = load_json(DATA_DIR / "settings.json", {"enabled": False})
    settings["enabled"] = False
    save_json(DATA_DIR / "settings.json", settings)
    return jsonify({"ok": True})

@app.route("/api/pixel/security2/trigger", methods=["POST"])
def trigger():
    data = request.json or {}
    event = {"time": time.time(), "type": data.get("type", "motion"), "status": "captured"}
    photo_path = str(DATA_DIR / f"sec_{int(time.time())}.jpg")
    try: subprocess.run(["termux-camera-photo", photo_path], timeout=10)
    except Exception:
        pass
    event["photo"] = photo_path
    events = load_json(DATA_DIR / "events.json", {"events": []})
    events["events"].append(event)
    if len(events["events"]) > 500: events["events"] = events["events"][-500:]
    save_json(DATA_DIR / "events.json", events)
    return jsonify({"ok": True, "event": event})

SECURITY_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Security Enhanced</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#22c55e;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.stats{display:flex;gap:12px;margin-bottom:16px}
.stat-box{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px 20px;text-align:center}
.stat-val{font-family:'Orbitron',monospace;font-size:22px;color:#00f0ff}
.stat-label{font-size:9px;color:#64748b;letter-spacing:1px;margin-top:4px}
.controls{display:flex;gap:10px;margin-bottom:16px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:10px 18px;border-radius:8px;cursor:pointer;font-size:12px}
.btn-green{border-color:#22c55e;color:#22c55e}
.btn-red{border-color:#ff0055;color:#ff0055}
.settings{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px}
.setting{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;display:flex;justify-content:space-between;align-items:center}
.switch{width:44px;height:24px;background:rgba(0,240,255,0.1);border:1px solid rgba(0,240,255,0.2);border-radius:12px;cursor:pointer;position:relative}
.switch.on{background:rgba(34,197,94,0.2);border-color:#22c55e}
.switch::after{content:'';position:absolute;top:2px;left:2px;width:18px;height:18px;background:#22c55e;border-radius:50%;transition:0.3s}
.switch.on::after{left:22px}
.events{background:rgba(3,8,20,0.8);border:1px solid rgba(34,197,94,0.2);border-radius:10px;padding:12px}
.event{padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px;display:flex;justify-content:space-between}
.event-time{color:#22c55e;font-family:'Share Tech Mono',monospace}
</style></head><body>
<h1>SECURITY ENHANCED</h1>
<div class="stats">
  <div class="stat-box"><div class="stat-val" id="total">0</div><div class="stat-label">TOTAL EVENTS</div></div>
  <div class="stat-box"><div class="stat-val" id="today">0</div><div class="stat-label">TODAY</div></div>
  <div class="stat-box"><div class="stat-val" id="status" style="color:#22c55e">DISARMED</div><div class="stat-label">STATUS</div></div>
</div>
<div class="controls">
  <button class="btn btn-green" onclick="startCam()">Arm System</button>
  <button class="btn btn-red" onclick="stopCam()">Disarm</button>
  <button class="btn" onclick="testTrigger()">Test Trigger</button>
</div>
<div class="settings">
  <div class="setting"><span>Motion Detection</span><div class="switch on" onclick="this.classList.toggle('on')"></div></div>
  <div class="setting"><span>Night Mode</span><div class="switch on" onclick="this.classList.toggle('on')"></div></div>
  <div class="setting"><span>Alert on Motion</span><div class="switch on" onclick="this.classList.toggle('on')"></div></div>
  <div class="setting"><span>Cloud Sync</span><div class="switch" onclick="this.classList.toggle('on')"></div></div>
</div>
<div class="events"><div style="font-size:12px;color:#22c55e;font-family:'Orbitron',monospace;margin-bottom:8px">EVENTS</div><div id="eventList"></div></div>
<script>
async function load(){const r=await(await fetch('/api/pixel/security2/status')).json();document.getElementById('total').textContent=r.stats.total_events;document.getElementById('today').textContent=r.stats.today_events;document.getElementById('status').textContent=r.settings.enabled?'ARMED':'DISARMED';document.getElementById('status').style.color=r.settings.enabled?'#ff0055':'#22c55e';document.getElementById('eventList').innerHTML=(r.events||[]).reverse().map(e=>'<div class="event"><span class="event-time">'+new Date(e.time*1000).toLocaleString()+'</span><span>'+e.type+'</span><span>'+e.status+'</span></div>').join('')||'<div style="color:#64748b;font-size:11px">No events</div>'}
async function startCam(){await fetch('/api/pixel/security2/start',{method:'POST'});load()}
async function stopCam(){await fetch('/api/pixel/security2/stop',{method:'POST'});load()}
async function testTrigger(){await fetch('/api/pixel/security2/trigger',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'manual'})});load()}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[Idea 7] Security Enhanced starting on port 9106...")
    app.run(host="0.0.0.0", port=9106, debug=False)