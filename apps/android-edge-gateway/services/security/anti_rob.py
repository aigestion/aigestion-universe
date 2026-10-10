# -*- coding: utf-8 -*-
"""
Idea 2: Anti-Rob Inteligente
Motion detection + wrong PIN = automatic recording and alert.
"""

import json
import time
import subprocess
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent.parent / "data" / "anti_rob"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def run_termux(cmd):
    try:
        result = subprocess.run(["termux-" + cmd], capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except Exception:
        return ""

@app.route("/")
def index():
    return ANTI_ROB_HTML

@app.route("/api/pixel/antirob/status")
def status():
    settings = load_json(DATA_DIR / "settings.json", {
        "enabled": True, "sensitivity": "medium", "lock_after": 3,
        "record_on_trigger": True, "photo_on_trigger": True,
        "alert_on_trigger": True
    })
    events = load_json(DATA_DIR / "events.json", {"events": []})
    stats = {"total_triggers": len(events["events"]), "today_triggers": 0}
    today = time.strftime("%Y-%m-%d")
    for e in events["events"]:
        if time.strftime("%Y-%m-%d", time.localtime(e.get("time", 0))) == today:
            stats["today_triggers"] += 1
    return jsonify({"settings": settings, "stats": stats, "events": events["events"][-20:]})

@app.route("/api/pixel/antirob/trigger", methods=["POST"])
def trigger():
    data = request.json or {}
    reason = data.get("reason", "manual")
    event = {"time": time.time(), "reason": reason, "status": "triggered"}
    photo_path = str(DATA_DIR / f"rob_{int(time.time())}.jpg")
    run_termux(f"camera-photo {photo_path}")
    event["photo"] = photo_path
    audio_path = str(DATA_DIR / f"rob_{int(time.time())}.mp3")
    run_termux(f"microphone-record -l 15 -f {audio_path}")
    event["audio"] = audio_path
    event["status"] = "recorded"
    events = load_json(DATA_DIR / "events.json", {"events": []})
    events["events"].append(event)
    if len(events["events"]) > 200: events["events"] = events["events"][-200:]
    save_json(DATA_DIR / "events.json", events)
    return jsonify({"ok": True, "event": event})

@app.route("/api/pixel/antirob/settings", methods=["POST"])
def update_settings():
    data = request.json or {}
    settings = load_json(DATA_DIR / "settings.json", {"enabled": True})
    settings.update(data)
    save_json(DATA_DIR / "settings.json", settings)
    return jsonify({"ok": True})

ANTI_ROB_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Anti-Rob</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#ff0055;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.stats{display:flex;gap:12px;margin-bottom:16px}
.stat-box{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px 20px;text-align:center}
.stat-val{font-family:'Orbitron',monospace;font-size:22px;color:#00f0ff}
.stat-label{font-size:9px;color:#64748b;letter-spacing:1px;margin-top:4px}
.settings{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px}
.setting{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;display:flex;justify-content:space-between;align-items:center}
.switch{width:44px;height:24px;background:rgba(0,240,255,0.1);border:1px solid rgba(0,240,255,0.2);border-radius:12px;cursor:pointer;position:relative}
.switch.on{background:rgba(34,197,94,0.2);border-color:#22c55e}
.switch::after{content:'';position:absolute;top:2px;left:2px;width:18px;height:18px;background:#22c55e;border-radius:50%;transition:0.3s}
.switch.on::after{left:22px}
.events{background:rgba(3,8,20,0.8);border:1px solid rgba(255,0,85,0.2);border-radius:10px;padding:12px}
.event{padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px;display:flex;justify-content:space-between}
.event-time{color:#ff0055;font-family:'Share Tech Mono',monospace}
.event-reason{color:#f59e0b}
.event-status{color:#22c55e}
.btn{background:rgba(255,0,85,0.1);border:1px solid #ff0055;color:#ff0055;padding:8px 14px;border-radius:6px;cursor:pointer;font-size:11px;margin-top:12px}
</style></head><body>
<h1>ANTI-ROB INTELIGENTE</h1>
<div class="stats">
  <div class="stat-box"><div class="stat-val" id="total">0</div><div class="stat-label">TOTAL TRIGGERS</div></div>
  <div class="stat-box"><div class="stat-val" id="today">0</div><div class="stat-label">TODAY</div></div>
  <div class="stat-box"><div class="stat-val" id="status" style="color:#22c55e">ARMED</div><div class="stat-label">STATUS</div></div>
</div>
<div class="settings">
  <div class="setting"><span>Enabled</span><div class="switch on" onclick="this.classList.toggle('on')"></div></div>
  <div class="setting"><span>Auto Photo</span><div class="switch on" onclick="this.classList.toggle('on')"></div></div>
  <div class="setting"><span>Auto Record</span><div class="switch on" onclick="this.classList.toggle('on')"></div></div>
  <div class="setting"><span>Alert PC</span><div class="switch on" onclick="this.classList.toggle('on')"></div></div>
</div>
<button class="btn" onclick="testTrigger()">Test Trigger</button>
<div class="events"><div style="font-size:12px;color:#ff0055;font-family:'Orbitron',monospace;margin-bottom:8px">EVENTS</div><div id="eventList"></div></div>
<script>
async function load(){const r=await(await fetch('/api/pixel/antirob/status')).json();document.getElementById('total').textContent=r.stats.total_triggers;document.getElementById('today').textContent=r.stats.today_triggers;document.getElementById('eventList').innerHTML=(r.events||[]).reverse().map(e=>'<div class="event"><span class="event-time">'+new Date(e.time*1000).toLocaleString()+'</span><span class="event-reason">'+e.reason+'</span><span class="event-status">'+e.status+'</span></div>').join('')||'<div style="color:#64748b;font-size:11px">No events</div>'}
async function testTrigger(){await fetch('/api/pixel/antirob/trigger',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reason:'manual_test'})});load()}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[Idea 2] Anti-Rob starting on port 9101...")
    app.run(host="0.0.0.0", port=9101, debug=False)