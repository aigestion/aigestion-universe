"""
System 60: Threat Dashboard
Threat detection and security overview
"""

import json
from pathlib import Path

from flask import Flask, jsonify

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
    return THREAT_HTML


@app.route("/api/threats/scan")
def scan():
    return jsonify(
        {
            "score": 92,
            "threats": [
                {
                    "name": "Suspicious download detected",
                    "severity": "medium",
                    "time": "14:32",
                    "action": "quarantined",
                },
                {
                    "name": "Brute force attempt from 103.224.182.250",
                    "severity": "high",
                    "time": "14:15",
                    "action": "blocked",
                },
                {
                    "name": "Outdated software: Chrome 120.0",
                    "severity": "low",
                    "time": "12:00",
                    "action": "alert",
                },
                {
                    "name": "Unusual network traffic pattern",
                    "severity": "medium",
                    "time": "11:30",
                    "action": "investigating",
                },
            ],
            "stats": {
                "scanned": 1247,
                "infected": 0,
                "quarantined": 1,
                "blocked": 156,
                "last_scan": "14:35",
            },
        }
    )


THREAT_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Threat Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.score-card{background:rgba(3,8,20,0.8);border:1px solid rgba(34,197,94,0.3);border-radius:12px;padding:20px;display:flex;align-items:center;gap:20px;margin-bottom:20px}
.score-circle{width:80px;height:80px;border-radius:50%;border:4px solid #22c55e;display:flex;align-items:center;justify-content:center;font-family:'Orbitron',monospace;font-size:28px;color:#22c55e}
.score-info{flex:1}
.score-label{font-size:14px;color:#64748b;letter-spacing:2px}
.score-desc{font-size:11px;color:#94a3b8;margin-top:4px}
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:20px}
.stat-box{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;text-align:center}
.stat-val{font-family:'Orbitron',monospace;font-size:18px;color:#00f0ff}
.stat-label{font-size:9px;color:#64748b;letter-spacing:1px;margin-top:4px}
.threats{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px}
.threat-title{font-family:'Orbitron',monospace;font-size:12px;color:#00f0ff;margin-bottom:10px;letter-spacing:1px}
.threat{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(0,240,255,0.05)}
.threat-name{flex:1;font-size:11px}
.severity{padding:2px 8px;border-radius:4px;font-size:9px;font-family:'Orbitron',monospace;letter-spacing:1px}
.sev-high{background:rgba(255,0,85,0.15);color:#ff0055}
.sev-medium{background:rgba(245,158,11,0.15);color:#f59e0b}
.sev-low{background:rgba(34,197,94,0.15);color:#22c55e}
.threat-time{color:#64748b;font-size:10px;font-family:'Share Tech Mono',monospace;margin:0 12px}
.threat-action{font-size:9px;padding:2px 6px;border-radius:4px;background:rgba(0,240,255,0.08);color:#00f0ff}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-size:11px;font-family:inherit;margin-top:12px}
.chart{display:flex;align-items:flex-end;gap:3px;height:60px;margin-top:12px}
.bar{flex:1;border-radius:2px 2px 0 0;min-height:4px;background:linear-gradient(to top,rgba(0,240,255,0.2),rgba(0,240,255,0.6))}
</style></head><body>
<h1>THREAT DASHBOARD</h1>
<div class="score-card">
  <div class="score-circle" id="score">92</div>
  <div class="score-info"><div class="score-label">SECURITY SCORE</div><div class="score-desc">System is well protected. 1 medium threat quarantined.</div></div>
  <button class="btn" onclick="load()">Scan Now</button>
</div>
<div class="stats">
  <div class="stat-box"><div class="stat-val" id="scanned">1,247</div><div class="stat-label">SCANNED</div></div>
  <div class="stat-box"><div class="stat-val" id="infected" style="color:#22c55e">0</div><div class="stat-label">INFECTED</div></div>
  <div class="stat-box"><div class="stat-val" id="quarantined" style="color:#f59e0b">1</div><div class="stat-label">QUARANTINED</div></div>
  <div class="stat-box"><div class="stat-val" id="blocked" style="color:#ff0055">156</div><div class="stat-label">BLOCKED</div></div>
  <div class="stat-box"><div class="stat-val" id="lastScan">14:35</div><div class="stat-label">LAST SCAN</div></div>
</div>
<div class="threats"><div class="threat-title">RECENT THREATS</div><div id="threatList"></div>
  <div style="font-size:10px;color:#64748b;margin-top:8px">ACTIVITY (24h)</div>
  <div class="chart" id="chart"></div>
</div>
<script>
async function load(){
  const r=await(await fetch('/api/threats/scan')).json();
  document.getElementById('score').textContent=r.score;
  document.getElementById('scanned').textContent=r.stats.scanned.toLocaleString();
  document.getElementById('quarantined').textContent=r.stats.quarantined;
  document.getElementById('blocked').textContent=r.stats.blocked;
  document.getElementById('lastScan').textContent=r.stats.last_scan;
  document.getElementById('threatList').innerHTML=(r.threats||[]).map(t=>
    '<div class="threat"><span class="threat-name">'+t.name+'</span>'+
    '<span class="severity sev-'+t.severity+'">'+t.severity.toUpperCase()+'</span>'+
    '<span class="threat-time">'+t.time+'</span>'+
    '<span class="threat-action">'+t.action+'</span></div>'
  ).join('');
  const bars=Array(24).fill(0).map(()=>Math.floor(Math.random()*50)+5);
  document.getElementById('chart').innerHTML=bars.map(v=>'<div class="bar" style="height:'+v+'%"></div>').join('');
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 60] Threat Dashboard starting on port 5070...")
    app.run(host="0.0.0.0", port=5070, debug=False)
