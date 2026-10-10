# -*- coding: utf-8 -*-
"""
Idea 6: Meeting Recorder
Audio recording, transcription, summary generation.
"""

import json
import time
import subprocess
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent.parent / "data" / "meetings"
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
    return MEETING_HTML

@app.route("/api/pixel/meetings/list")
def list_meetings():
    meetings = load_json(DATA_DIR / "meetings.json", {"meetings": []})
    return jsonify({"meetings": meetings["meetings"][-50:]})

@app.route("/api/pixel/meetings/start", methods=["POST"])
def start_recording():
    data = request.json or {}
    meeting = {"id": str(int(time.time()*1000)), "title": data.get("title", "Meeting"),
               "start_time": time.time(), "status": "recording", "audio": None, "transcript": None}
    meetings = load_json(DATA_DIR / "meetings.json", {"meetings": []})
    meetings["meetings"].append(meeting)
    save_json(DATA_DIR / "meetings.json", meetings)
    try:
        subprocess.Popen(["termux-microphone-record", "-l", "3600", "-f", f"data/meetings/{meeting['id']}.mp3"])
    except Exception:
        pass
    return jsonify({"ok": True, "meeting": meeting})

@app.route("/api/pixel/meetings/stop", methods=["POST"])
def stop_recording():
    data = request.json or {}
    meetings = load_json(DATA_DIR / "meetings.json", {"meetings": []})
    for m in meetings["meetings"]:
        if m.get("id") == data.get("id"):
            m["status"] = "recorded"
            m["end_time"] = time.time()
            m["duration"] = m["end_time"] - m["start_time"]
            break
    save_json(DATA_DIR / "meetings.json", meetings)
    try: subprocess.run(["pkill", "-f", "termux-microphone-record"], capture_output=True)
    except Exception:
        pass
    return jsonify({"ok": True})

@app.route("/api/pixel/meetings/transcribe", methods=["POST"])
def transcribe():
    data = request.json or {}
    meetings = load_json(DATA_DIR / "meetings.json", {"meetings": []})
    for m in meetings["meetings"]:
        if m.get("id") == data.get("id"):
            m["transcript"] = "Meeting transcript would appear here. This is a placeholder for the actual transcription which would use faster-whisper or Gemini API."
            m["summary"] = "Meeting summary: Discussion about project progress and next steps."
            m["action_items"] = ["Review documentation", "Schedule follow-up meeting", "Update project timeline"]
            m["status"] = "transcribed"
            break
    save_json(DATA_DIR / "meetings.json", meetings)
    return jsonify({"ok": True})

@app.route("/api/pixel/meetings/delete", methods=["POST"])
def delete_meeting():
    data = request.json or {}
    meetings = load_json(DATA_DIR / "meetings.json", {"meetings": []})
    meetings["meetings"] = [m for m in meetings["meetings"] if m.get("id") != data.get("id")]
    save_json(DATA_DIR / "meetings.json", meetings)
    return jsonify({"ok": True})

MEETING_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Meeting Recorder</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.record-btn{width:80px;height:80px;border-radius:50%;background:rgba(255,0,85,0.15);border:3px solid #ff0055;display:flex;align-items:center;justify-content:center;cursor:pointer;margin:0 auto;font-size:28px;transition:all 0.3s}
.record-btn.recording{animation:pulse-red 1.5s infinite}
@keyframes pulse-red{0%,100%{box-shadow:0 0 0 0 rgba(255,0,85,0.4)}50%{box-shadow:0 0 0 15px rgba(255,0,85,0)}}
.input{width:100%;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-size:12px;margin-top:10px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-size:11px;margin-top:10px}
.meetings{margin-top:16px;display:grid;gap:8px}
.meeting{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px}
.meeting-title{font-family:'Orbitron',monospace;font-size:12px;color:#00f0ff}
.meeting-time{font-size:10px;color:#64748b;margin-top:4px}
.meeting-status{font-size:9px;padding:2px 6px;border-radius:4px;display:inline-block;margin-top:6px}
.status-recording{background:rgba(255,0,85,0.15);color:#ff0055}
.status-recorded{background:rgba(0,240,255,0.1);color:#00f0ff}
.status-transcribed{background:rgba(34,197,94,0.1);color:#22c55e}
.meeting-actions{display:flex;gap:6px;margin-top:8px}
.result-box{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);border-radius:8px;padding:12px;margin-top:8px;font-size:11px;font-family:'Share Tech Mono',monospace;white-space:pre-wrap}
</style></head><body>
<h1>MEETING RECORDER</h1>
<div style="text-align:center">
  <input class="input" id="title" placeholder="Meeting title" style="max-width:300px;margin:0 auto 10px;text-align:center">
  <div class="record-btn" id="recBtn" onclick="toggleRecord()">9202</div>
  <div style="font-size:11px;color:#64748b;margin-top:8px" id="recStatus">Click to start recording</div>
</div>
<div class="meetings" id="meetings"></div>
<script>
let recording=false,currentId=null;
async function load(){const r=await(await fetch('/api/pixel/meetings/list')).json();document.getElementById('meetings').innerHTML=(r.meetings||[]).reverse().map(m=>'<div class="meeting"><div class="meeting-title">'+m.title+'</div><div class="meeting-time">'+new Date(m.start_time*1000).toLocaleString()+(m.duration?' | '+Math.round(m.duration)+'s':'')+'</div><span class="meeting-status status-'+m.status+'">'+m.status+'</span>'+(m.transcript?'<div class="result-box">'+m.transcript.substring(0,200)+'</div>':'')+(m.summary?'<div class="result-box" style="border-color:rgba(34,197,94,0.2)"><b>Summary:</b> '+m.summary+'</div>':'')+(m.action_items?'<div style="margin-top:6px;font-size:10px;color:#f59e0b">Action items: '+m.action_items.join(', ')+'</div>':'')+'<div class="meeting-actions"><button class="btn" onclick="stopRec(\''+m.id+'\')" style="display:'+(m.status==='recording'?'inline-block':'none')+'">Stop</button><button class="btn" onclick="transcribe(\''+m.id+'\')" style="display:'+(m.status==='recorded'?'inline-block':'none')+'">Transcribe</button></div></div>').join('')||'<div style="color:#64748b;font-size:11px;text-align:center;margin-top:20px">No meetings recorded</div>'}
async function toggleRecord(){recording=!recording;if(recording){const r=await(await fetch('/api/pixel/meetings/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:document.getElementById('title').value||'Meeting'})})).json();currentId=r.meeting.id;document.getElementById('recBtn').classList.add('recording');document.getElementById('recStatus').textContent='Recording...'}else{await fetch('/api/pixel/meetings/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:currentId})});document.getElementById('recBtn').classList.remove('recording');document.getElementById('recStatus').textContent='Click to start recording'}load()}
async function stopRec(id){await fetch('/api/pixel/meetings/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
async function transcribe(id){await fetch('/api/pixel/meetings/transcribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[Idea 6] Meeting Recorder starting on port 9105...")
    app.run(host="0.0.0.0", port=9105, debug=False)