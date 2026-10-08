import time

from flask import Blueprint, jsonify, request

delegation_bp = Blueprint("cross_agent_delegation", __name__)
_tasks = []

@delegation_bp.route("/api/hermes/delegation/status")
def cd_status():
    return jsonify({"tasks": _tasks[-20:], "total": len(_tasks)})

@delegation_bp.route("/api/hermes/delegation/delegate", methods=["POST"])
def cd_delegate():
    data = request.json or {}
    task = {
        "id": len(_tasks) + 1,
        "from": data.get("from", "hermes"),
        "to": data.get("to", "daniela"),
        "action": data.get("action", ""),
        "params": data.get("params", {}),
        "status": "pending",
        "time": time.time()
    }
    _tasks.append(task)
    return jsonify({"ok": True, "task": task})

@delegation_bp.route("/api/hermes/delegation/complete", methods=["POST"])
def cd_complete():
    data = request.json or {}
    task_id = data.get("id")
    for t in _tasks:
        if t["id"] == task_id:
            t["status"] = "completed"
            t["result"] = data.get("result")
    return jsonify({"ok": True})

@delegation_bp.route("/api/hermes/delegation/web")
def cd_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Cross-Agent Delegation</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.task{background:#111;border:1px solid #333;border-radius:8px;padding:10px;margin:5px 0}
.pending{border-left:3px solid #ff8800} .completed{border-left:3px solid #00ff88}
</style></head><body>
<h1>CROSS-AGENT DELEGATION</h1>
<div id="tasks"></div>
<script>setInterval(()=>{fetch('/api/hermes/delegation/status').then(r=>r.json()).then(d=>{document.getElementById('tasks').innerHTML=d.tasks.reverse().map(t=>'<div class="'+t.status+'"><strong>'+t.from+' -> '+t.to+'</strong>: '+t.action+' ['+t.status+']</div>').join('')})},5000)</script></body></html>"""
