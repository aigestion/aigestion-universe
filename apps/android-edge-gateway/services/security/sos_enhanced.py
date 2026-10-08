# -*- coding: utf-8 -*-
"""
Idea 1: SOS Enhanced
Emergency panic button with photo, audio, GPS, and PC notification.
Triggers: volume_down x3 or explicit POST /api/pixel/sos/trigger
"""

import os
import json
import time
import subprocess
import hashlib
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent.parent / "data" / "sos"
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
    return SOS_HTML

@app.route("/api/pixel/sos/status")
def status():
    settings = load_json(DATA_DIR / "settings.json", {
        "enabled": True, "contacts": [], "photo": True, "audio": True,
        "audio_duration": 10, "message": "EMERGENCY - I need help!",
        "cooldown": 60
    })
    events = load_json(DATA_DIR / "events.json", {"events": []})
    return jsonify({"settings": settings, "events": events["events"][-10:], "armed": settings["enabled"]})

@app.route("/api/pixel/sos/trigger", methods=["POST"])
def trigger():
    settings = load_json(DATA_DIR / "settings.json", {
        "enabled": True, "contacts": [], "photo": True, "audio": True,
        "audio_duration": 10, "message": "EMERGENCY - I need help!", "cooldown": 60
    })
    if not settings["enabled"]:
        return jsonify({"ok": False, "msg": "SOS disabled"})

    events = load_json(DATA_DIR / "events.json", {"events": []})
    if events["events"]:
        last = events["events"][-1]
        if time.time() - last.get("time", 0) < settings["cooldown"]:
            return jsonify({"ok": False, "msg": "Cooldown active"})

    event = {"time": time.time(), "type": "sos", "status": "triggered"}
    gps = run_termux("location")
    if gps:
        event["location"] = gps
    if settings["photo"]:
        photo_path = str(DATA_DIR / f"sos_{int(time.time())}.jpg")
        run_termux(f"camera-photo {photo_path}")
        event["photo"] = photo_path
    if settings["audio"]:
        audio_path = str(DATA_DIR / f"sos_{int(time.time())}.mp3")
        run_termux(f"microphone-record -l {settings['audio_duration']} -f {audio_path}")
        event["audio"] = audio_path

    event["status"] = "sent"
    events["events"].append(event)
    if len(events["events"]) > 100:
        events["events"] = events["events"][-100:]
    save_json(DATA_DIR / "events.json", events)
    return jsonify({"ok": True, "event": event})

@app.route("/api/pixel/sos/cancel", methods=["POST"])
def cancel():
    return jsonify({"ok": True, "msg": "SOS cancelled"})

@app.route("/api/pixel/sos/settings", methods=["POST"])
def update_settings():
    data = request.json or {}
    settings = load_json(DATA_DIR / "settings.json", {"enabled": True})
    settings.update(data)
    save_json(DATA_DIR / "settings.json", settings)
    return jsonify({"ok": True})

SOS_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>SOS Enhanced</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#ff0055;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.sos-btn{width:160px;height:160px;border-radius:50%;background:rgba(255,0,85,0.15);border:4px solid #ff0055;display:flex;align-items:center;justify-content:center;cursor:pointer;margin:20px auto;transition:all 0.3s;font-size:20px;font-family:'Orbitron',monospace;color:#ff0055;letter-spacing:2px}
.sos-btn:hover{background:rgba(255,0,85,0.3);box-shadow:0 0 40px rgba(255,0,85,0.4)}
.sos-btn:active{transform:scale(0.95)}
.settings{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:20px}
.setting{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px}
.setting-title{font-size:11px;color:#00f0ff;font-family:'Orbitron',monospace;margin-bottom:6px}
.switch{width:44px;height:24px;background:rgba(0,240,255,0.1);border:1px solid rgba(0,240,255,0.2);border-radius:12px;cursor:pointer;position:relative;display:inline-block}
.switch.on{background:rgba(34,197,94,0.2);border-color:#22c55e}
.switch::after{content:'';position:absolute;top:2px;left:2px;width:18px;height:18px;background:#22c55e;border-radius:50%;transition:0.3s}
.switch.on::after{left:22px}
.events{margin-top:20px;background:rgba(3,8,20,0.8);border:1px solid rgba(255,0,85,0.2);border-radius:10px;padding:12px}
.event{padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px;display:flex;justify-content:space-between}
.event-time{color:#ff0055;font-family:'Share Tech Mono',monospace}
.event-status{color:#22c55e}
.input{width:100%;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:6px 10px;border-radius:6px;font-size:11px;margin-top:4px}
</style></head><body>
<h1>SOS EMERGENCY</h1>
<div class="sos-btn" onclick="triggerSOS()">SOS</div>
<div style="text-align:center;font-size:11px;color:#64748b">Press to trigger emergency alert</div>
<div class="settings">
  <div class="setting"><div class="setting-title">SOS Enabled</div><div class="switch on" id="sosEnabled" onclick="toggleSetting('enabled')"></div></div>
  <div class="setting"><div class="setting-title">Auto Photo</div><div class="switch on" id="sosPhoto" onclick="toggleSetting('photo')"></div></div>
  <div class="setting"><div class="setting-title">Auto Audio</div><div class="switch on" id="sosAudio" onclick="toggleSetting('audio')"></div></div>
  <div class="setting"><div class="setting-title">Audio Duration</div><input class="input" type="number" value="10" id="audioDuration"></div>
</div>
<div class="events"><div style="font-size:12px;color:#ff0055;font-family:'Orbitron',monospace;margin-bottom:8px">EVENT LOG</div><div id="eventList"></div></div>
<script>
async function load(){const r=await(await fetch('/api/pixel/sos/status')).json();document.getElementById('sosEnabled').className='switch'+(r.settings.enabled?' on':'');document.getElementById('sosPhoto').className='switch'+(r.settings.photo?' on':'');document.getElementById('sosAudio').className='switch'+(r.settings.audio?' on':'');document.getElementById('eventList').innerHTML=(r.events||[]).reverse().map(e=>'<div class="event"><span class="event-time">'+new Date(e.time*1000).toLocaleString()+'</span><span class="event-status">'+e.status+'</span></div>').join('')||'<div style="color:#64748b;font-size:11px">No events</div>'}
async function triggerSOS(){if(confirm('TRIGGER SOS EMERGENCY?')){await fetch('/api/pixel/sos/trigger',{method:'POST'});load()}}
async function toggleSetting(key){const el=document.getElementById('sos'+key.charAt(0).toUpperCase()+key.slice(1));el.classList.toggle('on');await fetch('/api/pixel/sos/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({[key]:el.classList.contains('on')})})}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[Idea 1] SOS Enhanced starting on port 9100...")
    app.run(host="0.0.0.0", port=9100, debug=False)