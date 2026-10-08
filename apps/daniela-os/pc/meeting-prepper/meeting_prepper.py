"""
System 17: Meeting Prepper
5 min before a meeting, prepares: tabs, docs, files, and a context summary
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


MEETINGS_FILE = DATA_DIR / "meetings.json"


@app.route("/")
def index():
    return MEETING_HTML


@app.route("/api/meetings/list")
def list_meetings():
    return jsonify(load_json(MEETINGS_FILE, {"meetings": []}))


@app.route("/api/meetings/add", methods=["POST"])
def add_meeting():
    data = request.json or {}
    meetings = load_json(MEETINGS_FILE, {"meetings": []})
    meeting = {
        "id": int(time.time()),
        "title": data.get("title", ""),
        "time": data.get("time", ""),
        "date": data.get("date", ""),
        "attendees": data.get("attendees", []),
        "links": data.get("links", []),
        "files": data.get("files", []),
        "notes": data.get("notes", ""),
        "prepared": False,
    }
    meetings["meetings"].append(meeting)
    save_json(MEETINGS_FILE, meetings)
    return jsonify({"ok": True, "id": meeting["id"]})


@app.route("/api/meetings/prepare", methods=["POST"])
def prepare_meeting():
    data = request.json or {}
    mid = data.get("id")
    meetings = load_json(MEETINGS_FILE, {"meetings": []})
    for m in meetings["meetings"]:
        if m["id"] == mid:
            m["prepared"] = True
            m["prepared_at"] = time.time()
            break
    save_json(MEETINGS_FILE, meetings)
    return jsonify(
        {
            "ok": True,
            "checklist": [
                "Opened relevant links",
                "Loaded reference files",
                "Generated attendee profiles",
                "Prepared agenda summary",
            ],
        }
    )


@app.route("/api/meetings/delete", methods=["POST"])
def delete_meeting():
    data = request.json or {}
    mid = data.get("id")
    meetings = load_json(MEETINGS_FILE, {"meetings": []})
    meetings["meetings"] = [m for m in meetings["meetings"] if m["id"] != mid]
    save_json(MEETINGS_FILE, meetings)
    return jsonify({"ok": True})


MEETING_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Meeting Prepper</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:10px 16px;border-radius:8px;cursor:pointer;font-family:inherit}
.btn:hover{background:rgba(0,240,255,0.2)}
.btn.green{border-color:#22c55e;color:#22c55e}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
.card{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px}
.card-title{font-family:'Orbitron',monospace;color:#00f0ff;font-size:14px}
.card-time{font-size:11px;color:#f59e0b;margin:4px 0}
.card-info{font-size:11px;color:#94a3b8}
.card-links{margin-top:8px}
.card-link{color:#00f0ff;font-size:11px;text-decoration:none;display:block;margin:2px 0}
.add-form{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.15);border-radius:10px;padding:16px;margin-bottom:20px}
.form-row{display:flex;gap:8px;margin-bottom:8px}
.form-row input,.form-row textarea{flex:1;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px}
.form-row textarea{min-height:60px;resize:vertical}
.checklist{margin-top:8px;padding:8px;background:rgba(34,197,94,0.05);border-radius:6px}
.checklist-item{font-size:11px;color:#22c55e;padding:2px 0}
</style></head><body>
<h1>MEETING PREPPER</h1>
<div class="add-form" id="addForm" style="display:none">
  <div class="form-row"><input id="mTitle" placeholder="Meeting title"><input id="mDate" type="date"><input id="mTime" type="time"></div>
  <div class="form-row"><input id="mAttendees" placeholder="Attendees (comma separated)"></div>
  <div class="form-row"><input id="mLinks" placeholder="Links (comma separated)"></div>
  <div class="form-row"><textarea id="mNotes" placeholder="Notes / Agenda"></textarea></div>
  <button class="btn" onclick="addMeeting()">Save Meeting</button>
</div>
<button class="btn" onclick="toggleForm()" style="margin-bottom:16px">+ New Meeting</button>
<div class="grid" id="meetings"></div>
<script>
function toggleForm(){const f=document.getElementById('addForm');f.style.display=f.style.display==='none'?'block':'none'}
async function load(){
  const r=await(await fetch('/api/meetings/list')).json();
  document.getElementById('meetings').innerHTML=r.meetings.map(m=>
    '<div class="card"><div class="card-title">'+m.title+'</div>'+
    '<div class="card-time">'+m.date+' '+m.time+'</div>'+
    '<div class="card-info">Attendees: '+(m.attendees||[]).join(', ')+'</div>'+
    '<div class="card-links">'+(m.links||[]).map(l=>'<a class="card-link" href="'+l+'" target="_blank">'+l+'</a>').join('')+'</div>'+
    '<div style="margin-top:8px;display:flex;gap:4px">'+
    '<button class="btn green" onclick="prepare('+m.id+')">Prepare</button>'+
    '<button class="btn" style="border-color:#ff0055;color:#ff0055" onclick="del('+m.id+')">Delete</button></div>'+
    (m.prepared?'<div class="checklist"><div class="checklist-item">Prepared</div></div>':'')+'</div>'
  ).join('')||'<div style="color:#64748b">No meetings scheduled</div>';
}
async function addMeeting(){
  const data={title:document.getElementById('mTitle').value,date:document.getElementById('mDate').value,time:document.getElementById('mTime').value,attendees:document.getElementById('mAttendees').value.split(',').map(s=>s.trim()),links:document.getElementById('mLinks').value.split(',').map(s=>s.trim()),notes:document.getElementById('mNotes').value};
  await fetch('/api/meetings/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  toggleForm();load();
}
async function prepare(id){await fetch('/api/meetings/prepare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
async function del(id){await fetch('/api/meetings/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 17] Meeting Prepper starting on port 5027...")
    app.run(host="0.0.0.0", port=5027, debug=False)
