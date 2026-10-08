"""
System 51: USB Guardian
USB device monitoring and control
"""

import json
import os
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


def get_usb_drives():
    drives = []
    for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        path = f"{letter}:\\"
        if os.path.exists(path):
            try:
                drives.append({"letter": letter, "path": path, "type": "system"})
            except Exception:
                pass
    usb_drives = load_json(DATA_DIR / "usb_devices.json", {"devices": []})
    drives.extend(usb_drives.get("devices", []))
    return drives


@app.route("/")
def index():
    return USB_HTML


@app.route("/api/usb/list")
def list_usb():
    settings = load_json(DATA_DIR / "usb_settings.json", {"blocked": [], "alert_on_new": True})
    devices = [
        {
            "name": "SanDisk Ultra",
            "id": "USB001",
            "size": "64 GB",
            "connected": True,
            "first_seen": "2024-01-15",
        },
        {
            "name": "Kingston DataTraveler",
            "id": "USB002",
            "size": "32 GB",
            "connected": True,
            "first_seen": "2024-02-20",
        },
        {
            "name": "Samsung T7",
            "id": "USB003",
            "size": "500 GB",
            "connected": False,
            "first_seen": "2024-03-10",
        },
    ]
    return jsonify({"devices": devices, "settings": settings})


@app.route("/api/usb/block", methods=["POST"])
def block_device():
    data = request.json or {}
    device_id = data.get("id", "")
    settings = load_json(DATA_DIR / "usb_settings.json", {"blocked": [], "alert_on_new": True})
    if device_id not in settings["blocked"]:
        settings["blocked"].append(device_id)
        save_json(DATA_DIR / "usb_settings.json", settings)
    return jsonify({"ok": True})


@app.route("/api/usb/settings", methods=["POST"])
def update_settings():
    data = request.json or {}
    settings = load_json(DATA_DIR / "usb_settings.json", {"blocked": [], "alert_on_new": True})
    settings.update(data)
    save_json(DATA_DIR / "usb_settings.json", settings)
    return jsonify({"ok": True})


USB_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>USB Guardian</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.stats{display:flex;gap:12px;margin-bottom:20px}
.stat-box{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px 20px;text-align:center}
.stat-val{font-family:'Orbitron',monospace;font-size:22px;color:#00f0ff}
.stat-label{font-size:9px;color:#64748b;letter-spacing:1px;margin-top:4px}
.devices{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.device{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px;transition:all 0.3s}
.device:hover{border-color:#00f0ff}
.device.blocked{border-color:#ff0055}
.device-header{display:flex;justify-content:space-between;align-items:center}
.device-icon{font-size:28px}
.device-name{font-family:'Orbitron',monospace;font-size:13px;color:#00f0ff}
.device-id{font-size:10px;color:#64748b;font-family:'Share Tech Mono',monospace}
.device-info{display:flex;gap:8px;margin-top:8px}
.device-tag{font-size:9px;padding:2px 6px;border-radius:4px;background:rgba(0,240,255,0.08);color:#94a3b8}
.device-tag.danger{background:rgba(255,0,85,0.1);color:#ff0055}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:6px 10px;border-radius:6px;cursor:pointer;font-size:10px;font-family:inherit}
.btn-danger{border-color:#ff0055;color:#ff0055;background:rgba(255,0,85,0.1)}
.settings{background:rgba(3,8,20,0.8);border:1px solid rgba(255,0,85,0.2);border-radius:10px;padding:14px;margin-top:16px}
.toggle{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:12px}
.switch{width:36px;height:20px;background:rgba(0,240,255,0.1);border:1px solid rgba(0,240,255,0.2);border-radius:10px;cursor:pointer;position:relative}
.switch.on{background:rgba(0,240,255,0.2);border-color:#00f0ff}
.switch::after{content:'';position:absolute;top:2px;left:2px;width:14px;height:14px;background:#00f0ff;border-radius:50%;transition:0.3s}
.switch.on::after{left:18px}
</style></head><body>
<h1>USB GUARDIAN</h1>
<div class="stats">
  <div class="stat-box"><div class="stat-val" id="connected">2</div><div class="stat-label">CONNECTED</div></div>
  <div class="stat-box"><div class="stat-val" id="blocked">0</div><div class="stat-label">BLOCKED</div></div>
  <div class="stat-box"><div class="stat-val" id="known">3</div><div class="stat-label">KNOWN</div></div>
</div>
<div class="devices" id="devices"></div>
<div class="settings">
  <h3 style="font-size:13px;color:#00f0ff;font-family:'Orbitron',monospace;margin-bottom:10px">SETTINGS</h3>
  <div class="toggle"><span>Alert on new USB device</span><div class="switch on" onclick="this.classList.toggle('on')"></div></div>
  <div class="toggle"><span>Block unknown devices</span><div class="switch" onclick="this.classList.toggle('on')"></div></div>
  <div class="toggle"><span>Log all USB activity</span><div class="switch on" onclick="this.classList.toggle('on')"></div></div>
  <div class="toggle"><span>Auto-scan for malware</span><div class="switch on" onclick="this.classList.toggle('on')"></div></div>
</div>
<script>
async function load(){
  const r=await(await fetch('/api/usb/list')).json();
  document.getElementById('connected').textContent=(r.devices||[]).filter(d=>d.connected).length;
  document.getElementById('blocked').textContent=(r.settings?.blocked||[]).length;
  document.getElementById('known').textContent=(r.devices||[]).length;
  document.getElementById('devices').innerHTML=(r.devices||[]).map(d=>
    '<div class="device'+((r.settings?.blocked||[]).includes(d.id)?' blocked':'')+'">'+
    '<div class="device-header"><div><div class="device-icon">128301</div><div class="device-name">'+d.name+'</div>'+
    '<div class="device-id">'+d.id+'</div></div>'+
    '<button class="btn'+((r.settings?.blocked||[]).includes(d.id)?'':' btn-danger')+'" onclick="block(\''+d.id+'\')">'+
    ((r.settings?.blocked||[]).includes(d.id)?'Unblock':'Block')+'</button></div>'+
    '<div class="device-info"><span class="device-tag">'+d.size+'</span>'+
    '<span class="device-tag'+(d.connected?'':' danger')+'">'+(d.connected?'Connected':'Disconnected')+'</span>'+
    '<span class="device-tag">'+d.first_seen+'</span></div></div>'
  ).join('');
}
async function block(id){await fetch('/api/usb/block',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 51] USB Guardian starting on port 5061...")
    app.run(host="0.0.0.0", port=5061, debug=False)
