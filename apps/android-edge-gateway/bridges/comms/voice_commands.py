# -*- coding: utf-8 -*-
"""
Idea 5: Voice Commands
Natural voice commands for phone control.
"""

import json
import time
import subprocess
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent.parent / "data" / "voice_cmds"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

COMMANDS = {
    "open": lambda arg: subprocess.run(["am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER", "-n", arg], capture_output=True) if "@" in arg else subprocess.run(["am", "start", "-a", "android.intent.action.VIEW", "-d", f"market://details?id={arg}"], capture_output=True),
    "call": lambda arg: subprocess.run(["termux-call", arg], capture_output=True),
    "sms": lambda arg: subprocess.run(["termux-sms-send", "-n", arg.split()[0], " ".join(arg.split()[1:])], capture_output=True),
    "photo": lambda arg: subprocess.run(["termux-camera-photo", f"data/photo_{int(time.time())}.jpg"], capture_output=True),
    "record": lambda arg: subprocess.run(["termux-microphone-record", "-l", arg or "10"], capture_output=True),
    "volume": lambda arg: subprocess.run(["termux-volume", "media", str(min(15, max(0, int(arg))))], capture_output=True),
    "brightness": lambda arg: subprocess.run(["termux-brightness", str(min(255, max(0, int(arg))))], capture_output=True),
    "wifi": lambda arg: subprocess.run(["svc", "wifi", "enable" if "on" in arg.lower() else "disable"], capture_output=True),
    "bluetooth": lambda arg: subprocess.run(["svc", "bluetooth", "enable" if "on" in arg.lower() else "disable"], capture_output=True),
    "flashlight": lambda arg: subprocess.run(["termux-torch", "on" if "on" in arg.lower() else "off"], capture_output=True),
    "timer": lambda arg: subprocess.run(["termux-notification", "-t", "Timer", "-c", f"{arg}s timer"], capture_output=True),
    "weather": lambda arg: "Check weather API",
    "help": lambda arg: "Available: open, call, sms, photo, record, volume, brightness, wifi, bluetooth, flashlight, timer, weather",
}

@app.route("/")
def index():
    return VOICE_HTML

@app.route("/api/pixel/voice/status")
def status():
    return jsonify({"ready": True, "commands": list(COMMANDS.keys())})

@app.route("/api/pixel/voice/command", methods=["POST"])
def execute_command():
    data = request.json or {}
    text = data.get("text", "").strip().lower()
    parts = text.split(" ", 1)
    cmd = parts[0]
    arg = parts[1] if len(parts) > 1 else ""
    if cmd in COMMANDS:
        try:
            COMMANDS[cmd](arg)
            event = {"time": time.time(), "command": cmd, "arg": arg, "status": "executed"}
        except Exception as e:
            event = {"time": time.time(), "command": cmd, "arg": arg, "status": "error", "error": str(e)}
    else:
        event = {"time": time.time(), "command": cmd, "arg": arg, "status": "unknown"}
    history = load_json(DATA_DIR / "history.json", {"events": []})
    history["events"].append(event)
    if len(history["events"]) > 100:
        history["events"] = history["events"][-100:]
    save_json(DATA_DIR / "history.json", history)
    return jsonify({"ok": True, "event": event})

@app.route("/api/pixel/voice/history")
def history():
    return jsonify(load_json(DATA_DIR / "history.json", {"events": []}))

VOICE_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Voice Commands</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.mic-btn{width:100px;height:100px;border-radius:50%;background:rgba(0,240,255,0.1);border:3px solid #00f0ff;display:flex;align-items:center;justify-content:center;cursor:pointer;margin:20px auto;font-size:36px;transition:all 0.3s}
.mic-btn:hover{background:rgba(0,240,255,0.2);box-shadow:0 0 30px rgba(0,240,255,0.3)}
.mic-btn.active{background:rgba(34,197,94,0.2);border-color:#22c55e;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,0.4)}50%{box-shadow:0 0 0 15px rgba(34,197,94,0)}}
.cmd-input{display:flex;gap:8px;margin:20px 0}
.input{flex:1;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:10px 14px;border-radius:8px;font-size:14px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:10px 18px;border-radius:8px;cursor:pointer;font-size:12px}
.commands{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:6px;margin:16px 0}
.cmd-tag{background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.12);border-radius:6px;padding:6px;text-align:center;font-size:11px;color:#00f0ff;cursor:pointer}
.cmd-tag:hover{border-color:#00f0ff;background:rgba(0,240,255,0.1)}
.history{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;margin-top:16px}
.event{padding:4px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px;display:flex;gap:8px}
.event-time{color:#00f0ff;font-family:'Share Tech Mono',monospace;width:60px}
.event-cmd{color:#22c55e}.event-arg{color:#94a3b8}.event-status{color:#64748b}
</style></head><body>
<h1>VOICE COMMANDS</h1>
<div class="mic-btn" id="micBtn" onclick="startListening()">127908</div>
<div class="cmd-input"><input class="input" id="cmdInput" placeholder="Type command: open com.whatsapp, call 555-1234, volume 10..." onkeydown="if(event.key==='Enter')execCmd()"><button class="btn" onclick="execCmd()">Execute</button></div>
<div style="font-size:11px;color:#64748b;margin-bottom:8px">COMMANDS:</div>
<div class="commands" id="commands"></div>
<div class="history"><div style="font-size:12px;color:#00f0ff;font-family:'Orbitron',monospace;margin-bottom:8px">HISTORY</div><div id="history"></div></div>
<script>
let listening=false;
async function load(){const r=await(await fetch('/api/pixel/voice/status')).json();document.getElementById('commands').innerHTML=(r.commands||[]).map(c=>'<div class="cmd-tag" onclick="document.getElementById(\'cmdInput\').value=\''+c+' \'">'+c+'</div>').join('');const h=await(await fetch('/api/pixel/voice/history')).json();document.getElementById('history').innerHTML=(h.events||[]).reverse().slice(0,20).map(e=>'<div class="event"><span class="event-time">'+new Date(e.time*1000).toLocaleTimeString()+'</span><span class="event-cmd">'+e.command+'</span><span class="event-arg">'+e.arg+'</span><span class="event-status">'+e.status+'</span></div>').join('')||'<div style="color:#64748b;font-size:11px">No history</div>'}
function startListening(){listening=!listening;document.getElementById('micBtn').classList.toggle('active',listening);if(listening){document.getElementById('cmdInput').placeholder='Listening...'}}else{document.getElementById('cmdInput').placeholder='Type command...'}}
async function execCmd(){const text=document.getElementById('cmdInput').value;if(!text)return;await fetch('/api/pixel/voice/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});document.getElementById('cmdInput').value='';load()}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[Idea 5] Voice Commands starting on port 9104...")
    app.run(host="0.0.0.0", port=9104, debug=False)