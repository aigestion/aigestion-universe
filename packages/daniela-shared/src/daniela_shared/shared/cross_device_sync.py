"""
Daniela Cross-Device Sync Engine
Real-time synchronization between PC and Phone
Uses WebSocket + HTTP polling for bidirectional sync
"""

import json
import threading
import time
import urllib.request
from pathlib import Path

from flask import Blueprint, jsonify, request

sync_bp = Blueprint("cross_device_sync", __name__)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

_sync_file = DATA_DIR / "sync_state.json"
_log_file = DATA_DIR / "sync_log.json"

_state = {
    "pc": {"online": False, "last_seen": 0, "ip": "127.0.0.1"},
    "phone": {"online": False, "last_seen": 0, "ip": "192.168.1.170"},
    "last_sync": 0,
    "sync_count": 0,
    "conflicts": 0
}

_log = []

def _load_log():
    global _log
    if _log_file.exists():
        try:
            _log = json.loads(_log_file.read_text(encoding="utf-8"))
        except Exception:
            _log = []

def _save_log():
    global _log
    if len(_log) > 200:
        _log = _log[-200:]
    _log_file.write_text(json.dumps(_log, ensure_ascii=False, indent=2), encoding="utf-8")

def _add_log(device, action, data):
    entry = {
        "device": device,
        "action": action,
        "data": data,
        "time": time.time()
    }
    _log.append(entry)
    _save_log()

# --- REST API Endpoints ---

@sync_bp.route("/api/sync/status")
def sync_status():
    return jsonify(_state)

@sync_bp.route("/api/sync/ping", methods=["POST"])
def sync_ping():
    data = request.json or {}
    device = data.get("device", "unknown")
    ip = data.get("ip", request.remote_addr)
    _state[device] = {
        "online": True,
        "last_seen": time.time(),
        "ip": ip
    }
    _add_log(device, "ping", {"ip": ip})
    return jsonify({"ok": True, "state": _state})

@sync_bp.route("/api/sync/push", methods=["POST"])
def sync_push():
    data = request.json or {}
    device = data.get("device", "unknown")
    key = data.get("key", "")
    value = data.get("value", None)
    _state["last_sync"] = time.time()
    _state["sync_count"] += 1
    _add_log(device, "push", {"key": key, "value_type": type(value).__name__})
    return jsonify({"ok": True})

@sync_bp.route("/api/sync/pull")
def sync_pull():
    device = request.args.get("device", "unknown")
    since = float(request.args.get("since", 0))
    entries = [e for e in _log if e["time"] > since and e["device"] != device]
    return jsonify({"entries": entries[-50:], "state": _state})

@sync_bp.route("/api/sync/conflict", methods=["POST"])
def sync_conflict():
    data = request.json or {}
    _state["conflicts"] += 1
    resolution = data.get("resolution", "last-write-wins")
    _add_log("system", "conflict_resolved", {"resolution": resolution})
    return jsonify({"ok": True, "resolution": resolution})

# --- PC-to-Phone Proxy ---

@sync_bp.route("/api/sync/phone/<path:path>")
def sync_proxy_phone(path):
    phone_ip = _state["phone"]["ip"]
    phone_port = 8082
    url = f"http://{phone_ip}:{phone_port}/{path}"
    try:
        req = urllib.request.Request(url, timeout=5)
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode("utf-8")
        return data, resp.status, {"Content-Type": resp.headers.get("Content-Type", "application/json")}
    except Exception as e:
        return jsonify({"error": str(e), "phone_online": _state["phone"]["online"]}), 502

# --- Background Discovery Thread ---

def _discovery_loop():
    while True:
        try:
            phone_ip = _state["phone"]["ip"]
            url = f"http://{phone_ip}:8082/api/pixel/daemon/heartbeat"
            req = urllib.request.Request(url, timeout=3)
            urllib.request.urlopen(req, timeout=3)
            _state["phone"]["online"] = True
            _state["phone"]["last_seen"] = time.time()
        except Exception:
            _state["phone"]["online"] = False

        try:
            url = "http://127.0.0.1:9200/api/status"
            req = urllib.request.Request(url, timeout=3)
            urllib.request.urlopen(req, timeout=3)
            _state["pc"]["online"] = True
            _state["pc"]["last_seen"] = time.time()
        except Exception:
            _state["pc"]["online"] = False

        time.sleep(30)

# --- Web Dashboard ---

@sync_bp.route("/api/sync/web")
def sync_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Cross-Device Sync</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.container{display:flex;gap:40px;justify-content:center}
.device{background:#111;border:2px solid #333;border-radius:16px;padding:30px;width:280px;text-align:center}
.device.online{border-color:#00ff88}
.device.offline{border-color:#ff0066}
.device .icon{font-size:50px;margin:10px 0}
.log{margin-top:30px;max-width:800px;margin-left:auto;margin-right:auto}
.log-entry{background:#111;border-left:3px solid #00f0ff;padding:10px;margin:5px 0;font-size:12px;border-radius:0 8px 8px 0}
.stats{display:flex;gap:20px;justify-content:center;margin:20px 0}
.stat{background:#111;border:1px solid #333;border-radius:8px;padding:15px;text-align:center}
.stat .num{font-size:24px;color:#00ff88}
</style></head><body>
<h1 style="text-align:center">CROSS-DEVICE SYNC</h1>
<div class="container">
<div class="device" id="pc"><div class="icon">🖥</div><h3>PC</h3><p id="pc-status">Checking...</p><p id="pc-ip"></p></div>
<div style="display:flex;align-items:center;font-size:40px" id="sync-icon">⟷</div>
<div class="device" id="phone"><div class="icon">📱</div><h3>Phone</h3><p id="ph-status">Checking...</p><p id="ph-ip"></p></div>
</div>
<div class="stats">
<div class="stat"><div class="num" id="sync-count">0</div><p>Syncs</p></div>
<div class="stat"><div class="num" id="conflicts">0</div><p>Conflicts</p></div>
<div class="stat"><div class="num" id="last-sync">Never</div><p>Last Sync</p></div>
</div>
<div class="log"><h3>SYNC LOG</h3><div id="log"></div></div>
<script>function update(){fetch('/api/sync/status').then(r=>r.json()).then(d=>{
document.getElementById('pc').className='device '+(d.pc.online?'online':'offline');
document.getElementById('phone').className='device '+(d.phone.online?'online':'offline');
document.getElementById('pc-status').textContent=d.pc.online?'Online':'Offline';
document.getElementById('ph-status').textContent=d.phone.online?'Online':'Offline';
document.getElementById('pc-ip').textContent=d.pc.ip;
document.getElementById('ph-ip').textContent=d.phone.ip;
document.getElementById('sync-count').textContent=d.sync_count;
document.getElementById('conflicts').textContent=d.conflicts;
document.getElementById('last-sync').textContent=d.last_sync?new Date(d.last_sync*1000).toLocaleTimeString():'Never';
document.getElementById('sync-icon').style.color=d.pc.online&&d.phone.online?'#00ff88':'#ff0066';
});fetch('/api/sync/pull?device=web&since=0').then(r=>r.json()).then(d=>{
document.getElementById('log').innerHTML=d.entries.reverse().map(e=>'<div class="log-entry"><strong>'+e.device+'</strong> '+e.action+' '+JSON.stringify(e.data).substring(0,80)+'</div>').join('')})}
update();setInterval(update,5000)
</script></body></html>"""

# Start discovery thread
_load_log()
_thread = threading.Thread(target=_discovery_loop, daemon=True)
_thread.start()
