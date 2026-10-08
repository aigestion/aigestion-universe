"""
System 30: Night Mode Orchestrator
Smart night mode: adjusts brightness, color temp, sounds, wallpaper, keyboard
"""

import json
from datetime import datetime
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
    return NIGHT_HTML


@app.route("/api/night/status")
def status():
    hour = datetime.now().hour
    if 6 <= hour < 12:
        period = "morning"
    elif 12 <= hour < 17:
        period = "afternoon"
    elif 17 <= hour < 21:
        period = "evening"
    else:
        period = "night"

    settings = load_json(
        DATA_DIR / "settings.json",
        {"night_start": 21, "night_end": 7, "auto": True, "warmth": 50, "volume": 70},
    )

    is_night = hour >= settings.get("night_start", 21) or hour < settings.get("night_end", 7)

    return jsonify(
        {
            "period": period,
            "hour": hour,
            "is_night": is_night,
            "settings": settings,
            "recommendation": get_recommendation(period, is_night),
        }
    )


def get_recommendation(period, is_night):
    if is_night:
        return {
            "mode": "night",
            "warmth": 80,
            "volume": 40,
            "message": "Activating night mode - warm colors, lower volume",
        }
    elif period == "evening":
        return {
            "mode": "evening",
            "warmth": 60,
            "volume": 60,
            "message": "Evening mode - transitioning to warmer tones",
        }
    else:
        return {
            "mode": "day",
            "warmth": 20,
            "volume": 80,
            "message": "Day mode - full brightness, cool tones",
        }


@app.route("/api/night/settings", methods=["POST"])
def set_settings():
    data = request.json or {}
    save_json(DATA_DIR / "settings.json", data)
    return jsonify({"ok": True})


NIGHT_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Night Mode Orchestrator</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.status-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.status-card{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:16px;text-align:center}
.status-card.night{border-color:#8b5cf6;background:rgba(139,92,246,0.05)}
.status-card.evening{border-color:#f59e0b;background:rgba(245,158,11,0.05)}
.status-card.day{border-color:#22c55e;background:rgba(34,197,94,0.05)}
.status-label{font-size:10px;color:#64748b;letter-spacing:2px;text-transform:uppercase}
.status-value{font-size:24px;font-family:'Orbitron',monospace;margin:8px 0}
.status-msg{font-size:11px;color:#94a3b8}
.settings{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:16px}
.settings h2{font-size:13px;color:#00f0ff;font-family:'Orbitron',monospace;letter-spacing:1px;margin-bottom:12px}
.setting-row{display:flex;align-items:center;gap:12px;margin:10px 0}
.setting-label{font-size:12px;color:#94a3b8;width:120px}
.slider{flex:1;-webkit-appearance:none;height:6px;background:#1a1a3e;border-radius:3px;outline:none}
.slider::-webkit-slider-thumb{-webkit-appearance:none;width:16px;height:16px;background:#00f0ff;border-radius:50%;cursor:pointer}
.slider-value{font-family:'Share Tech Mono',monospace;font-size:12px;color:#00f0ff;width:40px;text-align:right}
.toggle{position:relative;width:40px;height:20px;background:#1a1a3e;border-radius:10px;cursor:pointer}
.toggle.active{background:#00f0ff}
.toggle::after{content:'';position:absolute;top:2px;left:2px;width:16px;height:16px;background:#fff;border-radius:50%;transition:0.3s}
.toggle.active::after{left:22px}
</style></head><body>
<h1>NIGHT MODE ORCHESTRATOR</h1>
<div class="status-grid">
  <div class="status-card" id="card1"><div class="status-label">PERIOD</div><div class="status-value" id="period">--</div><div class="status-msg" id="periodMsg">--</div></div>
  <div class="status-card" id="card2"><div class="status-label">HOUR</div><div class="status-value" id="hour">--</div><div class="status-msg" id="hourMsg">--</div></div>
  <div class="status-card" id="card3"><div class="status-label">MODE</div><div class="status-value" id="mode">--</div><div class="status-msg" id="modeMsg">--</div></div>
</div>
<div class="settings">
  <h2>SETTINGS</h2>
  <div class="setting-row"><span class="setting-label">Auto Mode</span><div class="toggle active" id="autoToggle" onclick="toggleAuto()"></div></div>
  <div class="setting-row"><span class="setting-label">Night Start</span><input type="range" class="slider" id="nightStart" min="18" max="23" value="21" oninput="updateSettings()"><span class="slider-value" id="nightStartVal">21:00</span></div>
  <div class="setting-row"><span class="setting-label">Night End</span><input type="range" class="slider" id="nightEnd" min="5" max="10" value="7" oninput="updateSettings()"><span class="slider-value" id="nightEndVal">07:00</span></div>
  <div class="setting-row"><span class="setting-label">Warmth</span><input type="range" class="slider" id="warmth" min="0" max="100" value="50" oninput="updateSettings()"><span class="slider-value" id="warmthVal">50%</span></div>
  <div class="setting-row"><span class="setting-label">Volume</span><input type="range" class="slider" id="volume" min="0" max="100" value="70" oninput="updateSettings()"><span class="slider-value" id="volumeVal">70%</span></div>
</div>
<script>
async function load(){
  const r=await(await fetch('/api/night/status')).json();
  document.getElementById('period').textContent=r.period.toUpperCase();
  document.getElementById('periodMsg').textContent=r.period==='night'?'Time to rest':r.period==='evening':'Winding down':'Full energy';
  document.getElementById('hour').textContent=String(r.hour).padStart(2,'0')+':00';
  document.getElementById('hourMsg').textContent=r.is_night?'Night hours active':'Day hours';
  document.getElementById('mode').textContent=r.recommendation.mode.toUpperCase();
  document.getElementById('modeMsg').textContent=r.recommendation.message;
  const cardClass=r.is_night?'night':r.period==='evening'?'evening':'day';
  document.getElementById('card1').className='status-card '+cardClass;
  document.getElementById('card2').className='status-card '+cardClass;
  document.getElementById('card3').className='status-card '+cardClass;
  const s=r.settings;
  document.getElementById('nightStart').value=s.night_start;document.getElementById('nightStartVal').textContent=String(s.night_start).padStart(2,'0')+':00';
  document.getElementById('nightEnd').value=s.night_end;document.getElementById('nightEndVal').textContent=String(s.night_end).padStart(2,'0')+':00';
  document.getElementById('warmth').value=s.warmth;document.getElementById('warmthVal').textContent=s.warmth+'%';
  document.getElementById('volume').value=s.volume;document.getElementById('volumeVal').textContent=s.volume+'%';
  if(s.auto)document.getElementById('autoToggle').classList.add('active');
  else document.getElementById('autoToggle').classList.remove('active');
}
function toggleAuto(){document.getElementById('autoToggle').classList.toggle('active');updateSettings()}
async function updateSettings(){
  const s={night_start:parseInt(document.getElementById('nightStart').value),night_end:parseInt(document.getElementById('nightEnd').value),warmth:parseInt(document.getElementById('warmth').value),volume:parseInt(document.getElementById('volume').value),auto:document.getElementById('autoToggle').classList.contains('active')};
  document.getElementById('nightStartVal').textContent=String(s.night_start).padStart(2,'0')+':00';
  document.getElementById('nightEndVal').textContent=String(s.night_end).padStart(2,'0')+':00';
  document.getElementById('warmthVal').textContent=s.warmth+'%';
  document.getElementById('volumeVal').textContent=s.volume+'%';
  await fetch('/api/night/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(s)});
}
load();setInterval(load,60000);
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 30] Night Mode Orchestrator starting on port 5040...")
    app.run(host="0.0.0.0", port=5040, debug=False)
