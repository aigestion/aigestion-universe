"""
Daniela Unified Bridge
Connects Omnipresente (52) + Epic PC (62) = 114 total systems
Single API to access everything
"""

import urllib.request

from flask import Blueprint, jsonify, request

unified_bp = Blueprint("unified_bridge", __name__)

EPIC_PC_BASE = "http://localhost"
EPIC_PC_SYSTEMS = {
    "voice": {"port": 5010, "name": "Voice AI Desktop"},
    "wallpaper": {"port": 5011, "name": "Neural Wallpaper"},
    "files": {"port": 5012, "name": "3D File Galaxy"},
    "notifications": {"port": 5013, "name": "Notification Brain"},
    "health": {"port": 5014, "name": "System Hologram"},
    "code": {"port": 5015, "name": "Code Copilot"},
    "cross_device": {"port": 5016, "name": "Cross-Device Telepathy"},
    "launcher": {"port": 5017, "name": "Predictive Launcher"},
    "ar": {"port": 5018, "name": "AR Desktop"},
    "organism": {"port": 5019, "name": "Living Organism"},
    "web_launcher": {"port": 5020, "name": "Web Launcher"},
    "memory": {"port": 5021, "name": "AI Memory Palace"},
    "dream": {"port": 5022, "name": "Dream Logger"},
    "context": {"port": 5023, "name": "Context Switcher"},
    "organizer": {"port": 5024, "name": "AI Auto-Organizer"},
    "focus": {"port": 5025, "name": "Focus Mode"},
    "typing": {"port": 5026, "name": "Typing Predictor"},
    "meeting": {"port": 5027, "name": "Meeting Prepper"},
    "digest": {"port": 5028, "name": "Post-Meeting Digest"},
    "email": {"port": 5029, "name": "Email Priority Brain"},
    "knowledge": {"port": 5030, "name": "Knowledge Weaver"},
    "ambient_wp": {"port": 5031, "name": "Ambient Wallpaper"},
    "zen": {"port": 5032, "name": "Desktop Zen Garden"},
    "wiki": {"port": 5033, "name": "Floating Wiki"},
    "theme": {"port": 5034, "name": "Theme Time Machine"},
    "pets": {"port": 5035, "name": "Desktop Pets 2.0"},
    "matrix": {"port": 5036, "name": "Code Rain Matrix"},
    "pixel": {"port": 5037, "name": "Pixel Art Dashboard"},
    "calendar": {"port": 5038, "name": "Holographic Calendar"},
    "sound": {"port": 5039, "name": "Sound Visualizer Pro"},
    "night": {"port": 5040, "name": "Night Mode Orchestrator"},
    "clipboard": {"port": 5041, "name": "Smart Clipboard History"},
    "screenshot": {"port": 5042, "name": "Auto-Screenshot Context"},
    "renamer": {"port": 5043, "name": "Batch File Renamer AI"},
    "watcher": {"port": 5044, "name": "Smart File Watcher"},
    "actions": {"port": 5045, "name": "Quick Actions Bar"},
    "macros": {"port": 5046, "name": "Desktop Macros AI"},
    "translator": {"port": 5047, "name": "Clipboard Translator"},
    "smart_launch": {"port": 5048, "name": "Smart App Launcher 2.0"},
    "timer": {"port": 5049, "name": "Focus Timer"},
    "backup": {"port": 5050, "name": "Auto-Backup Brain"},
    "game": {"port": 5051, "name": "Game Launcher Hub"},
    "music": {"port": 5052, "name": "Music Reactive Desktop"},
    "retro": {"port": 5053, "name": "Retro Emulator Hub"},
    "dj": {"port": 5054, "name": "Desktop DJ"},
    "meme": {"port": 5055, "name": "Meme Generator"},
    "stream": {"port": 5056, "name": "Stream Overlay"},
    "vr": {"port": 5057, "name": "VR Desktop"},
    "keyboard": {"port": 5058, "name": "Keyboard Sound Engine"},
    "karaoke": {"port": 5059, "name": "Desktop Karaoke"},
    "achievements": {"port": 5060, "name": "Achievement System"},
    "usb": {"port": 5061, "name": "USB Guardian"},
    "privacy": {"port": 5062, "name": "Screen Privacy"},
    "vault": {"port": 5063, "name": "Password Vault"},
    "network": {"port": 5064, "name": "Network Sentinel"},
    "integrity": {"port": 5065, "name": "File Integrity"},
    "notes": {"port": 5066, "name": "Encrypted Notes"},
    "parental": {"port": 5067, "name": "Parental Controls"},
    "privacy_dash": {"port": 5068, "name": "Privacy Dashboard"},
    "firewall": {"port": 5069, "name": "Firewall Monitor"},
    "threat": {"port": 5070, "name": "Threat Dashboard"},
    "flow": {"port": 9090, "name": "Flow Builder"},
    "multimodal": {"port": 9091, "name": "Multi-Modal"}
}

def _check_system(port):
    try:
        url = f"{EPIC_PC_BASE}:{port}/"
        req = urllib.request.Request(url, timeout=2)
        urllib.request.urlopen(req, timeout=2)
        return True
    except Exception:
        return False

@unified_bp.route("/api/unified/status")
def unified_status():
    online = 0
    offline = 0
    systems = []
    for key, info in EPIC_PC_SYSTEMS.items():
        is_online = _check_system(info["port"])
        if is_online:
            online += 1
        else:
            offline += 1
        systems.append({
            "id": key,
            "name": info["name"],
            "port": info["port"],
            "status": "online" if is_online else "offline",
            "url": f"{EPIC_PC_BASE}:{info['port']}"
        })
    return jsonify({
        "total": len(EPIC_PC_SYSTEMS),
        "online": online,
        "offline": offline,
        "systems": systems
    })

@unified_bp.route("/api/unified/proxy/<int:port>/<path:path>")
def unified_proxy(port, path):
    url = f"{EPIC_PC_BASE}:{port}/{path}"
    try:
        req = urllib.request.Request(url, timeout=5)
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read()
        return data, resp.status, {"Content-Type": resp.headers.get("Content-Type", "text/html")}
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@unified_bp.route("/api/unified/search")
def unified_search():
    q = request.args.get("q", "").lower()
    results = []
    for key, info in EPIC_PC_SYSTEMS.items():
        if q in info["name"].lower() or q in key.lower():
            results.append({
                "id": key,
                "name": info["name"],
                "port": info["port"],
                "url": f"{EPIC_PC_BASE}:{info['port']}"
            })
    return jsonify({"results": results})

@unified_bp.route("/api/unified/web")
def unified_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Daniela Unified - 114 Systems</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.stats{display:flex;gap:15px;margin:20px 0;flex-wrap:wrap}
.stat{background:#111;border:1px solid #333;border-radius:10px;padding:15px;text-align:center;flex:1;min-width:100px}
.stat .num{font-size:28px;color:#00ff88}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-top:20px}
.sys{background:#111;border:1px solid #333;border-radius:8px;padding:10px;cursor:pointer;transition:all .2s}
.sys:hover{border-color:#00f0ff}
.sys.online{border-left:3px solid #00ff88}
.sys.offline{border-left:3px solid #ff0066}
.sys h4{font-size:11px;margin:0 0 4px}
.sys p{font-size:9px;color:#666;margin:0}
</style></head><body>
<h1>DANIELA UNIFIED</h1>
<p>114 systems across PC + Phone</p>
<div class="stats">
<div class="stat"><div class="num" id="total">114</div><p>Total</p></div>
<div class="stat"><div class="num" id="online" style="color:#00ff88">--</div><p>Online</p></div>
<div class="stat"><div class="num" id="offline" style="color:#ff0066">--</div><p>Offline</p></div>
</div>
<div class="grid" id="grid"></div>
<script>fetch('/api/unified/status').then(r=>r.json()).then(d=>{
document.getElementById('total').textContent=d.total;
document.getElementById('online').textContent=d.online;
document.getElementById('offline').textContent=d.offline;
document.getElementById('grid').innerHTML=d.systems.map(s=>'<div class="sys '+s.status+'" onclick="window.open(\\''+s.url+'\\')"><h4>'+s.name+'</h4><p>:'+s.port+' - '+s.status+'</p></div>').join('')
})</script>
</body></html>"""
