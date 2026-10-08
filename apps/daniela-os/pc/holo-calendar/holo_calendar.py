"""
System 28: Holographic Calendar
3D floating calendar that shows your week as a landscape
"""

import json
import time
from datetime import datetime, timedelta
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
    return CALENDAR_HTML


@app.route("/api/calendar/events")
def list_events():
    return jsonify(load_json(DATA_DIR / "events.json", {"events": []}))


@app.route("/api/calendar/add", methods=["POST"])
def add_event():
    data = request.json or {}
    events = load_json(DATA_DIR / "events.json", {"events": []})
    event = {
        "id": int(time.time()),
        "title": data.get("title", ""),
        "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
        "time": data.get("time", ""),
        "color": data.get("color", "#00f0ff"),
        "duration": data.get("duration", 60),
        "description": data.get("description", ""),
    }
    events["events"].append(event)
    save_json(DATA_DIR / "events.json", events)
    return jsonify({"ok": True})


@app.route("/api/calendar/delete", methods=["POST"])
def delete_event():
    data = request.json or {}
    events = load_json(DATA_DIR / "events.json", {"events": []})
    events["events"] = [e for e in events["events"] if e["id"] != data.get("id")]
    save_json(DATA_DIR / "events.json", events)
    return jsonify({"ok": True})


@app.route("/api/calendar/week")
def week_view():
    today = datetime.now()
    start = today - timedelta(days=today.weekday())
    days = []
    for i in range(7):
        d = start + timedelta(days=i)
        days.append(d.strftime("%Y-%m-%d"))
    events = load_json(DATA_DIR / "events.json", {"events": []}).get("events", [])
    week_events = {d: [] for d in days}
    for e in events:
        if e.get("date") in week_events:
            week_events[e["date"]].append(e)
    return jsonify({"days": days, "events": week_events, "today": today.strftime("%Y-%m-%d")})


CALENDAR_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Holographic Calendar</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100vw;height:100vh;overflow:hidden;background:#0a0a2e;font-family:'Rajdhani',sans-serif}
canvas{position:fixed;top:0;left:0;z-index:0}
#ui{position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:10;width:90%;max-width:900px}
.week{display:flex;gap:6px;justify-content:center}
.day-col{flex:1;background:rgba(3,8,20,0.7);border:1px solid rgba(0,240,255,0.15);border-radius:8px;padding:8px;max-height:70vh;overflow-y:auto}
.day-header{font-family:'Orbitron',monospace;font-size:11px;color:#00f0ff;text-align:center;padding:4px;border-bottom:1px solid rgba(0,240,255,0.15);margin-bottom:6px}
.day-header.today{color:#ff0055;border-color:#ff0055}
.event{background:rgba(0,240,255,0.08);border-left:3px solid #00f0ff;border-radius:4px;padding:4px 6px;margin-bottom:4px;font-size:10px;color:#e2e8f0}
.event-time{color:#64748b;font-size:9px}
.add-bar{display:flex;gap:6px;margin-top:10px;justify-content:center}
.add-bar input,.add-bar select{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.2);color:#e2e8f0;padding:6px 10px;border-radius:6px;font-family:inherit;font-size:11px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:6px 12px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px}
.btn:hover{background:rgba(0,240,255,0.2)}
</style></head><body>
<canvas id="c"></canvas>
<div id="ui">
  <div class="week" id="week"></div>
  <div class="add-bar">
    <input id="eventTitle" placeholder="Event title">
    <input id="eventDate" type="date">
    <input id="eventTime" type="time">
    <select id="eventColor"><option value="#00f0ff">Cyan</option><option value="#22c55e">Green</option><option value="#f59e0b">Yellow</option><option value="#ef4444">Red</option><option value="#8b5cf6">Purple</option></select>
    <button class="btn" onclick="addEvent()">Add</button>
  </div>
</div>
<script>
const canvas=document.getElementById('c');const ctx=canvas.getContext('2d');
canvas.width=innerWidth;canvas.height=innerHeight;
window.onresize=()=>{canvas.width=innerWidth;canvas.height=innerHeight};

function drawBg(){
  ctx.fillStyle='#0a0a2e';ctx.fillRect(0,0,canvas.width,canvas.height);
  for(let i=0;i<50;i++){ctx.beginPath();ctx.arc(Math.random()*canvas.width,Math.random()*canvas.height,Math.random()*1.5,0,Math.PI*2);ctx.fillStyle=`rgba(0,240,255,${Math.random()*0.3})`;ctx.fill()}
  ctx.strokeStyle='rgba(0,240,255,0.05)';ctx.lineWidth=1;
  for(let i=0;i<10;i++){const y=canvas.height*0.3+i*20;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(canvas.width,y);ctx.stroke()}
}
drawBg();

async function load(){
  const r=await(await fetch('/api/calendar/week')).json();
  const dayNames=['MON','TUE','WED','THU','FRI','SAT','SUN'];
  document.getElementById('week').innerHTML=r.days.map((d,i)=>{
    const isToday=d===r.today;
    const events=(r.events[d]||[]).sort((a,b)=>(a.time||'').localeCompare(b.time||''));
    return '<div class="day-col"><div class="day-header'+(isToday?' today':'')+'">'+dayNames[i]+'<br>'+d.substring(5)+'</div>'+
    events.map(e=>'<div class="event" style="border-color:'+e.color+'"><div>'+e.title+'</div><div class="event-time">'+(e.time||'')+'</div></div>').join('')+'</div>';
  }).join('');
  document.getElementById('eventDate').value=r.today;
}
async function addEvent(){
  const data={title:document.getElementById('eventTitle').value,date:document.getElementById('eventDate').value,time:document.getElementById('eventTime').value,color:document.getElementById('eventColor').value};
  if(!data.title)return;
  await fetch('/api/calendar/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  document.getElementById('eventTitle').value='';load();
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 28] Holographic Calendar starting on port 5038...")
    app.run(host="0.0.0.0", port=5038, debug=False)
