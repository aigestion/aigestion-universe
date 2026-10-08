import time

from flask import Blueprint, jsonify, request

device_handoff_bp = Blueprint("device_handoff", __name__)
_pending = []


@device_handoff_bp.route("/api/consciousness/device-handoff/status")
def dh_status():
    return jsonify({"pending": len(_pending), "items": _pending})


@device_handoff_bp.route("/api/consciousness/device-handoff/send", methods=["POST"])
def dh_send():
    data = request.json or {}
    _pending.append(
        {
            "content": data.get("content", ""),
            "from": data.get("from", "pc"),
            "to": data.get("to", "phone"),
            "type": data.get("type", "text"),
            "time": time.time(),
        }
    )
    return jsonify({"ok": True})


@device_handoff_bp.route("/api/consciousness/device-handoff/web")
def dh_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Device Handoff</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.handoff{display:flex;gap:40px;justify-content:center;margin-top:40px}
.device-box{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:30px;width:300px;text-align:center}
input,textarea{width:100%;background:#0a0a0f;border:1px solid #333;color:#00f0ff;padding:8px;border-radius:6px;margin:5px 0;font-family:monospace}
.btn{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:10px 20px;border-radius:6px;cursor:pointer;margin:5px}
</style></head><body>
<h1 style="text-align:center">DEVICE HANDOFF</h1>
<div class="handoff">
<div class="device-box"><h3>From PC</h3><textarea id="pc-content" placeholder="Content to send..."></textarea><button class="btn" onclick="send('pc')">Send to Phone</button></div>
<div class="device-box"><h3>From Phone</h3><textarea id="ph-content" placeholder="Content to send..."></textarea><button class="btn" onclick="send('phone')">Send to PC</button></div>
</div>
<script>function send(from){const to=from==='pc'?'phone':'pc';const c=document.getElementById(from==='pc'?'pc-content':'ph-content').value;fetch('/api/consciousness/device-handoff/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:c,from,to})}).then(()=>{alert('Sent!');document.getElementById(from==='pc'?'pc-content':'ph-content').value=''})}</script>
</body></html>"""
