import time

from flask import Blueprint, jsonify, request

handoff_bp = Blueprint("context_handoff", __name__)
_data = {"handoffs": [], "pending": []}


@handoff_bp.route("/api/consciousness/handoff/status")
def ho_status():
    return jsonify(_data)


@handoff_bp.route("/api/consciousness/handoff/send", methods=["POST"])
def ho_send():
    data = request.json or {}
    item = {
        "from": data.get("from", "pc"),
        "to": data.get("to", "phone"),
        "type": data.get("type", "url"),
        "content": data.get("content", ""),
        "context": data.get("context", {}),
        "time": time.time(),
    }
    _data["pending"].append(item)
    return jsonify({"ok": True})


@handoff_bp.route("/api/consciousness/handoff/receive")
def ho_receive():
    if _data["pending"]:
        item = _data["pending"].pop(0)
        _data["handoffs"].append(item)
        return jsonify(item)
    return jsonify({})


@handoff_bp.route("/api/consciousness/handoff/web")
def ho_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Context Handoff</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.container{display:flex;gap:40px;justify-content:center}
.device{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:30px;width:300px}
.device h3{text-align:center;margin-top:0}
.send-btn{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:10px;border-radius:6px;cursor:pointer;width:100%;margin:5px 0}
.history{margin-top:20px;font-size:12px;max-height:300px;overflow-y:auto}
</style></head><body>
<div class="container">
<div class="device"><h3>PC</h3><input id="pc-url" placeholder="URL or text" style="width:100%;background:#0a0a0f;border:1px solid #333;color:#00f0ff;padding:8px;border-radius:6px"><button class="send-btn" onclick="send('pc','phone')">Send to Phone</button></div>
<div style="display:flex;align-items:center;font-size:40px">⟷</div>
<div class="device"><h3>Phone</h3><button class="send-btn" onclick="receive()">Check Pending</button><div class="history" id="hist"></div></div>
</div>
<script>function send(f,t){fetch('/api/consciousness/handoff/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({from:f,to:t,content:document.getElementById('pc-url').value,type:'url'})}).then(()=>alert('Sent!'))}
function receive(){fetch('/api/consciousness/handoff/receive').then(r=>r.json()).then(d=>{if(d.content){document.getElementById('hist').innerHTML='<div style="background:#00f0ff11;padding:10px;border-radius:6px;margin:5px 0">'+d.content+'</div>'+document.getElementById('hist').innerHTML}else{alert('No pending items')}})}
</script></body></html>"""
