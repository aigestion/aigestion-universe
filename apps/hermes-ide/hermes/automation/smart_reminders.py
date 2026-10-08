from flask import Blueprint, jsonify, request

reminders_bp = Blueprint("smart_reminders", __name__)
_reminders = [{"id": 1, "text": "Water break", "trigger": "every_2h", "active": True}, {"id": 2, "text": "Stand up", "trigger": "every_1h", "active": True}]

@reminders_bp.route("/api/hermes/automation/reminders/status")
def sr_status():
    return jsonify({"reminders": _reminders})

@reminders_bp.route("/api/hermes/automation/reminders/add", methods=["POST"])
def sr_add():
    data = request.json or {}
    _reminders.append({"id": len(_reminders)+1, "text": data.get("text",""), "trigger": data.get("trigger","manual"), "active": True})
    return jsonify({"ok": True})

@reminders_bp.route("/api/hermes/automation/reminders/web")
def sr_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Smart Reminders</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.reminder{background:#111;border:1px solid #333;border-radius:8px;padding:10px;margin:5px 0;display:flex;justify-content:space-between}
input{background:#111;border:1px solid #333;color:#00f0ff;padding:8px;border-radius:6px;font-family:monospace;width:300px}
button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:8px 16px;border-radius:6px;cursor:pointer}
</style></head><body><h1>SMART REMINDERS</h1>
<div><input id="text" placeholder="Reminder..."><button onclick="add()">Add</button></div>
<div id="reminders"></div>
<script>function load(){fetch('/api/hermes/automation/reminders/status').then(r=>r.json()).then(d=>{document.getElementById('reminders').innerHTML=d.reminders.map(r=>'<div class="reminder"><span>'+r.text+'</span><span>'+r.trigger+'</span></div>').join('')})}
function add(){fetch('/api/hermes/automation/reminders/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:document.getElementById('text').value})}).then(()=>{document.getElementById('text').value='';load()})}
load()</script></body></html>"""
