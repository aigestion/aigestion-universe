# -*- coding: utf-8 -*-
"""
Idea 3: Geofence Enhanced
Smart geofencing with customizable zones and alerts.
"""

import json
import time
import math
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent.parent / "data" / "geofence"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@app.route("/")
def index():
    return GEOFENCE_HTML

@app.route("/api/pixel/geofence/status")
def status():
    settings = load_json(DATA_DIR / "settings.json", {"enabled": True, "zones": [
        {"id": "home", "name": "Home", "lat": 0, "lon": 0, "radius": 100, "alert_on_exit": True, "color": "#22c55e"},
        {"id": "work", "name": "Work", "lat": 0, "lon": 0, "radius": 150, "alert_on_exit": True, "color": "#00f0ff"}
    ]})
    current = load_json(DATA_DIR / "current.json", {"lat": 0, "lon": 0, "zone": "unknown"})
    events = load_json(DATA_DIR / "events.json", {"events": []})
    return jsonify({"settings": settings, "current": current, "events": events["events"][-10:]})

@app.route("/api/pixel/geofence/location", methods=["POST"])
def update_location():
    data = request.json or {}
    lat = data.get("lat", 0)
    lon = data.get("lon", 0)
    settings = load_json(DATA_DIR / "settings.json", {"zones": []})
    current_zone = "outside"
    for zone in settings.get("zones", []):
        dist = haversine(lat, lon, zone["lat"], zone["lon"])
        if dist <= zone["radius"]:
            current_zone = zone["id"]
            break
    current = {"lat": lat, "lon": lon, "zone": current_zone, "time": time.time()}
    save_json(DATA_DIR / "current.json", current)
    prev = load_json(DATA_DIR / "prev_location.json", {"zone": ""})
    if prev.get("zone") != current_zone:
        events = load_json(DATA_DIR / "events.json", {"events": []})
        events["events"].append({"time": time.time(), "from": prev.get("zone", "unknown"), "to": current_zone})
        if len(events["events"]) > 100:
            events["events"] = events["events"][-100:]
        save_json(DATA_DIR / "events.json", events)
    save_json(DATA_DIR / "prev_location.json", {"zone": current_zone})
    return jsonify({"ok": True, "zone": current_zone})

@app.route("/api/pixel/geofence/zones", methods=["POST"])
def update_zones():
    data = request.json or {}
    settings = load_json(DATA_DIR / "settings.json", {"zones": []})
    settings.update(data)
    save_json(DATA_DIR / "settings.json", settings)
    return jsonify({"ok": True})

GEOFENCE_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Geofence</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#22c55e;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.current{background:rgba(3,8,20,0.8);border:1px solid rgba(34,197,94,0.3);border-radius:12px;padding:16px;text-align:center;margin-bottom:16px}
.zone-name{font-family:'Orbitron',monospace;font-size:24px;color:#22c55e}
.coords{font-size:11px;color:#64748b;margin-top:4px;font-family:'Share Tech Mono',monospace}
.zones{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px}
.zone{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;border-left:4px solid var(--color)}
.zone-name-label{font-family:'Orbitron',monospace;font-size:12px;color:var(--color)}
.zone-radius{font-size:10px;color:#64748b;margin-top:4px}
.events{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px}
.event{padding:4px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px}
.event-time{color:#00f0ff;font-family:'Share Tech Mono',monospace}
</style></head><body>
<h1>GEOFENCE</h1>
<div class="current"><div class="zone-name" id="currentZone">UNKNOWN</div><div class="coords" id="coords">--</div></div>
<div class="zones" id="zones"></div>
<div class="events"><div style="font-size:12px;color:#00f0ff;font-family:'Orbitron',monospace;margin-bottom:8px">ZONE HISTORY</div><div id="eventList"></div></div>
<script>
async function load(){const r=await(await fetch('/api/pixel/geofence/status')).json();document.getElementById('currentZone').textContent=r.current.zone.toUpperCase();document.getElementById('coords').textContent=r.current.lat.toFixed(6)+', '+r.current.lon.toFixed(6);document.getElementById('zones').innerHTML=(r.settings.zones||[]).map(z=>'<div class="zone" style="--color:'+z.color+'"><div class="zone-name-label">'+z.name+'</div><div class="zone-radius">Radius: '+z.radius+'m</div></div>').join('');document.getElementById('eventList').innerHTML=(r.events||[]).reverse().map(e=>'<div class="event"><span class="event-time">'+new Date(e.time*1000).toLocaleString()+'</span> '+e.from+' -> '+e.to+'</div>').join('')||'<div style="color:#64748b;font-size:11px">No events</div>'}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[Idea 3] Geofence Enhanced starting on port 9102...")
    app.run(host="0.0.0.0", port=9102, debug=False)