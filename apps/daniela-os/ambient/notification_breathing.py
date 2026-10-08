import time

from flask import Blueprint, jsonify, request

noti_breath_bp = Blueprint("notification_breathing", __name__)
_state = {"active": True, "notifications": [], "intensity": 0}


@noti_breath_bp.route("/api/ambient/noti-breath/status")
def nb_status():
    return jsonify(_state)


@noti_breath_bp.route("/api/ambient/noti-breath/notify", methods=["POST"])
def nb_notify():
    data = request.json or {}
    notif = {
        "title": data.get("title", "Notification"),
        "priority": data.get("priority", "normal"),
        "time": time.time(),
    }
    _state["notifications"].append(notif)
    _state["intensity"] = min(
        100, _state["intensity"] + (20 if notif["priority"] == "urgent" else 10)
    )
    return jsonify({"ok": True})


@noti_breath_bp.route("/api/ambient/noti-breath/web")
def nb_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Notification Breathing</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.breath{width:300px;height:300px;border-radius:50%;border:3px solid #00f0ff;display:flex;align-items:center;justify-content:center;font-size:20px;text-align:center;transition:all 1s}
</style></head><body>
<div class="breath" id="breath">Waiting...</div>
<script>setInterval(()=>{fetch('/api/ambient/noti-breath/status').then(r=>r.json()).then(d=>{const b=document.getElementById('breath');const i=d.intensity;b.style.boxShadow='0 0 '+i*2+'px #00f0ff';b.style.transform='scale('+(1+i/200)+')';b.textContent=i>50?'URGENT':'Calm'})},2000)</script>
</body></html>"""
