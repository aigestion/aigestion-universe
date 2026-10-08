import time

from flask import Blueprint, jsonify, request

anomaly_bp = Blueprint("anomaly_alerts", __name__)
_alerts = [
    {
        "id": 1,
        "type": "warning",
        "message": "RAM usage increased 300% this week",
        "time": time.time() - 3600,
        "acknowledged": False,
    },
    {
        "id": 2,
        "type": "info",
        "message": "Only 4h sleep in last 3 days",
        "time": time.time() - 7200,
        "acknowledged": False,
    },
]


@anomaly_bp.route("/api/proactive/anomaly/status")
def a_status():
    return jsonify({"alerts": _alerts})


@anomaly_bp.route("/api/proactive/anomaly/acknowledge", methods=["POST"])
def a_ack():
    data = request.json or {}
    for a in _alerts:
        if a["id"] == data.get("id"):
            a["acknowledged"] = True
    return jsonify({"ok": True})


@anomaly_bp.route("/api/proactive/anomaly/web")
def a_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Anomaly Alerts</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.alert{background:#111;border-left:4px solid #ff8800;border-radius:0 12px 12px 0;padding:20px;margin:10px 0;display:flex;justify-content:space-between;align-items:center}
.alert.warning{border-color:#ff8800} .alert.info{border-color:#00f0ff}
.ack-btn{background:#00ff8822;border:1px solid #00ff88;color:#00ff88;padding:6px 12px;border-radius:6px;cursor:pointer}
</style></head><body>
<h1>ANOMALY ALERTS</h1>
<div id="list"></div>
<script>function load(){fetch('/api/proactive/anomaly/status').then(r=>r.json()).then(d=>{document.getElementById('list').innerHTML=d.alerts.filter(a=>!a.acknowledged).map(a=>'<div class="alert '+a.type+'"><div><h3>'+a.type.toUpperCase()+'</h3><p>'+a.message+'</p></div><button class="ack-btn" onclick="ack('+a.id+')">Acknowledge</button></div>').join('')||'<p>No anomalies detected</p>'})}
function ack(id){fetch('/api/proactive/anomaly/acknowledge',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})}).then(()=>load())}
load()</script>
</body></html>"""
