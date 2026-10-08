"""
System 58: Privacy Dashboard
Privacy controls and data tracking
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
    return PRIVACY_HTML


@app.route("/api/privacy/scan")
def scan():
    trackers = [
        {"name": "Google Analytics", "type": "tracker", "blocked": True, "count": 1247},
        {"name": "Facebook Pixel", "type": "tracker", "blocked": True, "count": 892},
        {"name": "Hotjar", "type": "analytics", "blocked": False, "count": 456},
        {"name": "Segment", "type": "analytics", "blocked": False, "count": 234},
        {"name": "Doubleclick", "type": "ad", "blocked": True, "count": 2103},
        {"name": "TikTok Pixel", "type": "tracker", "blocked": True, "count": 567},
    ]
    permissions = [
        {"app": "Chrome", "camera": True, "mic": True, "location": True, "notifications": True},
        {"app": "Discord", "camera": True, "mic": True, "location": False, "notifications": True},
        {"app": "VS Code", "camera": False, "mic": False, "location": False, "notifications": True},
    ]
    return jsonify({"trackers": trackers, "permissions": permissions, "score": 87})


PRIVACY_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Privacy Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.score-card{background:rgba(3,8,20,0.8);border:1px solid rgba(34,197,94,0.3);border-radius:12px;padding:20px;text-align:center;margin-bottom:20px}
.score-val{font-family:'Orbitron',monospace;font-size:48px;color:#22c55e}
.score-label{font-size:12px;color:#64748b;letter-spacing:2px}
.sections{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:12px}
.section{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px}
.section-title{font-family:'Orbitron',monospace;font-size:12px;color:#00f0ff;margin-bottom:10px;letter-spacing:1px}
.tracker{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px}
.tracker-name{flex:1}
.tracker-type{font-size:9px;padding:2px 6px;border-radius:4px;margin:0 8px}
.type-tracker{background:rgba(255,0,85,0.1);color:#ff0055}
.type-analytics{background:rgba(245,158,11,0.1);color:#f59e0b}
.type-ad{background:rgba(139,92,246,0.1);color:#8b5cf6}
.tracker-count{color:#64748b;font-family:'Share Tech Mono',monospace;font-size:10px;width:60px;text-align:right}
.switch{width:32px;height:18px;background:rgba(0,240,255,0.1);border:1px solid rgba(0,240,255,0.2);border-radius:9px;cursor:pointer;position:relative;display:inline-block}
.switch.on{background:rgba(34,197,94,0.2);border-color:#22c55e}
.switch::after{content:'';position:absolute;top:2px;left:2px;width:12px;height:12px;background:#22c55e;border-radius:50%;transition:0.3s}
.switch.on::after{left:16px}
.perm{display:flex;gap:8px;padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px}
.perm-app{width:80px;color:#00f0ff;font-family:'Orbitron',monospace;font-size:10px}
.perm-tag{font-size:9px;padding:2px 6px;border-radius:4px}
.perm-yes{background:rgba(34,197,94,0.1);color:#22c55e}
.perm-no{background:rgba(100,116,139,0.1);color:#64748b}
</style></head><body>
<h1>PRIVACY DASHBOARD</h1>
<div class="score-card"><div class="score-val" id="score">87</div><div class="score-label">PRIVACY SCORE</div></div>
<div class="sections">
  <div class="section"><div class="section-title">TRACKERS DETECTED</div><div id="trackers"></div></div>
  <div class="section"><div class="section-title">APP PERMISSIONS</div><div id="permissions"></div></div>
</div>
<script>
async function load(){
  const r=await(await fetch('/api/privacy/scan')).json();
  document.getElementById('score').textContent=r.score;
  document.getElementById('trackers').innerHTML=(r.trackers||[]).map(t=>
    '<div class="tracker"><span class="tracker-name">'+t.name+'</span>'+
    '<span class="tracker-type type-'+t.type+'">'+t.type+'</span>'+
    '<span class="tracker-count">'+t.count.toLocaleString()+'</span>'+
    '<div class="switch'+(t.blocked?' on':'')+'" onclick="this.classList.toggle(\'on\')"></div></div>'
  ).join('');
  document.getElementById('permissions').innerHTML=(r.permissions||[]).map(p=>
    '<div class="perm"><span class="perm-app">'+p.app+'</span>'+
    '<span class="perm-tag '+(p.camera?'perm-yes':'perm-no')+'">Cam</span>'+
    '<span class="perm-tag '+(p.mic?'perm-yes':'perm-no')+'">Mic</span>'+
    '<span class="perm-tag '+(p.location?'perm-yes':'perm-no')+'">Loc</span>'+
    '<span class="perm-tag '+(p.notifications?'perm-yes':'perm-no')+'">Noti</span></div>'
  ).join('');
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 58] Privacy Dashboard starting on port 5068...")
    app.run(host="0.0.0.0", port=5068, debug=False)
