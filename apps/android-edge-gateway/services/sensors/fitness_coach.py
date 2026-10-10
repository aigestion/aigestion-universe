# -*- coding: utf-8 -*-
"""
Idea 10: Fitness Coach
Activity tracking with accelerometer data and AI coaching.
"""

import json
import time
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent.parent / "data" / "fitness"
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
    return FITNESS_HTML

@app.route("/api/pixel/fitness/status")
def status():
    today = time.strftime("%Y-%m-%d")
    daily = load_json(DATA_DIR / f"day_{today}.json", {
        "steps": 0, "calories": 0, "distance": 0, "active_minutes": 0,
        "activities": [], "heart_rate": []
    })
    goals = load_json(DATA_DIR / "goals.json", {
        "steps": 10000, "calories": 500, "distance": 8, "active_minutes": 60
    })
    week = []
    for i in range(6, -1, -1):
        d = time.strftime("%Y-%m-%d", time.localtime(time.time() - i*86400))
        day_data = load_json(DATA_DIR / f"day_{d}.json", {"steps": 0, "calories": 0})
        week.append({"date": d, "steps": day_data.get("steps", 0), "calories": day_data.get("calories", 0)})
    return jsonify({"daily": daily, "goals": goals, "week": week, "streak": 5})

@app.route("/api/pixel/fitness/update", methods=["POST"])
def update_fitness():
    data = request.json or {}
    today = time.strftime("%Y-%m-%d")
    daily = load_json(DATA_DIR / f"day_{today}.json", {"steps": 0, "calories": 0, "distance": 0, "active_minutes": 0, "activities": []})
    for key in ["steps", "calories", "distance", "active_minutes"]:
        if key in data:
            daily[key] = daily.get(key, 0) + data[key]
    if "activity" in data:
        daily["activities"].append({"type": data["activity"], "time": time.time(), "duration": data.get("duration", 0)})
    save_json(DATA_DIR / f"day_{today}.json", daily)
    return jsonify({"ok": True, "daily": daily})

@app.route("/api/pixel/fitness/goals", methods=["POST"])
def update_goals():
    data = request.json or {}
    goals = load_json(DATA_DIR / "goals.json", {"steps": 10000})
    goals.update(data)
    save_json(DATA_DIR / "goals.json", goals)
    return jsonify({"ok": True})

FITNESS_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Fitness Coach</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#22c55e;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.rings{display:flex;justify-content:center;gap:30px;margin-bottom:20px}
.ring{text-align:center}
.ring svg{width:100px;height:100px}
.ring-val{font-family:'Orbitron',monospace;font-size:16px}
.ring-label{font-size:9px;color:#64748b;letter-spacing:1px;margin-top:4px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px}
.stat-box{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;text-align:center}
.stat-val{font-family:'Orbitron',monospace;font-size:18px;color:#22c55e}
.stat-label{font-size:9px;color:#64748b;letter-spacing:1px;margin-top:4px}
.chart{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px;margin-bottom:16px}
.bars{display:flex;align-items:flex-end;gap:6px;height:80px;margin-top:8px}
.bar{flex:1;border-radius:4px 4px 0 0;background:linear-gradient(to top,rgba(34,197,94,0.3),rgba(34,197,94,0.8));min-height:4px}
.bar-label{font-size:8px;color:#64748b;text-align:center;margin-top:4px}
.activities{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px}
.activity{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px}
.activity-type{color:#22c55e}.activity-dur{color:#64748b}
.coach{background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.2);border-radius:10px;padding:14px;margin-top:16px}
.coach-msg{font-size:12px;color:#22c55e}
</style></head><body>
<h1>FITNESS COACH</h1>
<div class="rings">
  <div class="ring"><svg viewBox="0 0 36 36"><circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(34,197,94,0.1)" stroke-width="3"/><circle cx="18" cy="18" r="15.9" fill="none" stroke="#22c55e" stroke-width="3" stroke-dasharray="75 100" stroke-linecap="round" transform="rotate(-90 18 18)"/></svg><div class="ring-val" style="color:#22c55e">75%</div><div class="ring-label">STEPS</div></div>
  <div class="ring"><svg viewBox="0 0 36 36"><circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(245,158,11,0.1)" stroke-width="3"/><circle cx="18" cy="18" r="15.9" fill="none" stroke="#f59e0b" stroke-width="3" stroke-dasharray="60 100" stroke-linecap="round" transform="rotate(-90 18 18)"/></svg><div class="ring-val" style="color:#f59e0b">60%</div><div class="ring-label">CALORIES</div></div>
  <div class="ring"><svg viewBox="0 0 36 36"><circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(0,240,255,0.1)" stroke-width="3"/><circle cx="18" cy="18" r="15.9" fill="none" stroke="#00f0ff" stroke-width="3" stroke-dasharray="85 100" stroke-linecap="round" transform="rotate(-90 18 18)"/></svg><div class="ring-val" style="color:#00f0ff">85%</div><div class="ring-label">ACTIVE</div></div>
</div>
<div class="stats">
  <div class="stat-box"><div class="stat-val" id="steps">7,523</div><div class="stat-label">STEPS</div></div>
  <div class="stat-box"><div class="stat-val" id="calories">312</div><div class="stat-label">CALORIES</div></div>
  <div class="stat-box"><div class="stat-val" id="distance">5.2</div><div class="stat-label">KM</div></div>
  <div class="stat-box"><div class="stat-val" id="active">42</div><div class="stat-label">ACTIVE MIN</div></div>
</div>
<div class="chart"><div style="font-size:12px;color:#22c55e;font-family:'Orbitron',monospace">WEEKLY STEPS</div><div class="bars" id="weekChart"></div></div>
<div class="activities"><div style="font-size:12px;color:#22c55e;font-family:'Orbitron',monospace;margin-bottom:8px">TODAY'S ACTIVITIES</div><div id="activityList"></div></div>
<div class="coach"><div class="coach-msg">You're doing great! 2,477 more steps to reach your daily goal. A 15-minute walk will get you there!</div></div>
<script>
async function load(){const r=await(await fetch('/api/pixel/fitness/status')).json();const d=r.daily||{};document.getElementById('steps').textContent=(d.steps||0).toLocaleString();document.getElementById('calories').textContent=d.calories||0;document.getElementById('distance').textContent=(d.distance||0).toFixed(1);document.getElementById('active').textContent=d.active_minutes||0;const maxSteps=Math.max(...(r.week||[]).map(w=>w.steps),1);document.getElementById('weekChart').innerHTML=(r.week||[]).map(w=>'<div><div class="bar" style="height:'+(w.steps/maxSteps*100)+'%"></div><div class="bar-label">'+w.date.slice(-2)+'</div></div>').join('');document.getElementById('activityList').innerHTML=(d.activities||[]).map(a=>'<div class="activity"><span class="activity-type">'+a.type+'</span><span class="activity-dur">'+a.duration+' min</span></div>').join('')||'<div style="color:#64748b;font-size:11px">No activities recorded</div>'}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[Idea 10] Fitness Coach starting on port 9109...")
    app.run(host="0.0.0.0", port=9109, debug=False)