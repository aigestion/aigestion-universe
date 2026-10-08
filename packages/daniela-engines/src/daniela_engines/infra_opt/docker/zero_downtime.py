from flask import Blueprint, jsonify

ztd_bp = Blueprint("zero_downtime", __name__)

@ztd_bp.route("/api/infra/ztd/status")
def z_status():
    return jsonify({"strategy": "blue_green", "active": "green", "standby": "blue", "switch_time": "0.5s"})

@ztd_bp.route("/api/infra/ztd/web")
def z_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Zero-Downtime Deploy</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.blue{background:#0066cc} .green{background:#00ff88}
.zones{display:flex;gap:20px;margin:20px 0;justify-content:center}
.zone{background:#111;border:2px solid #333;border-radius:12px;padding:30px;text-align:center;min-width:200px}
.zone.active{border-color:#00ff88} .zone.standby{border-color:#ff8800}
</style></head><body><h1 style="text-align:center">ZERO-DOWNTIME DEPLOY</h1>
<div class="zones"><div class="zone active"><h2 style="color:#00ff88">GREEN</h2><p>Active</p><p>Traffic: 100%</p></div><div class="zone standby"><h2 style="color:#ff8800">BLUE</h2><p>Standby</p><p>Ready</p></div></div><p>Switch time: 0.5s | Strategy: Blue/Green</p></body></html>"""
