from flask import Blueprint, jsonify, request

parallel_bp = Blueprint("parallel_processing", __name__)
_state = {"pc": {"load": 15, "tasks": []}, "phone": {"load": 5, "tasks": []}, "total": 20}


@parallel_bp.route("/api/consciousness/parallel/status")
def p_status():
    return jsonify(_state)


@parallel_bp.route("/api/consciousness/parallel/distribute", methods=["POST"])
def p_distribute():
    data = request.json or {}
    task = data.get("task", "unknown")
    if _state["pc"]["load"] <= _state["phone"]["load"]:
        _state["pc"]["tasks"].append(task)
        _state["pc"]["load"] = min(100, _state["pc"]["load"] + 20)
    else:
        _state["phone"]["tasks"].append(task)
        _state["phone"]["load"] = min(100, _state["phone"]["load"] + 20)
    return jsonify({"ok": True})


@parallel_bp.route("/api/consciousness/parallel/web")
def p_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Parallel Processing</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.container{display:flex;gap:40px;justify-content:center}
.device{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:30px;width:300px}
.load-bar{height:20px;background:#222;border-radius:10px;margin:10px 0}
.load-fill{height:100%;border-radius:10px;transition:width .5s}
.tasks{margin-top:10px;font-size:12px}
.task{background:#00f0ff11;padding:5px 10px;border-radius:4px;margin:3px 0}
</style></head><body>
<h1 style="text-align:center">PARALLEL PROCESSING</h1>
<div class="container">
<div class="device"><h3>PC</h3><div class="load-bar"><div class="load-fill" id="pc-load" style="width:15%;background:#00f0ff"></div></div><p id="pc-pct">15%</p><div class="tasks" id="pc-tasks"></div></div>
<div class="device"><h3>Phone</h3><div class="load-bar"><div class="load-fill" id="ph-load" style="width:5%;background:#00ff88"></div></div><p id="ph-pct">5%</p><div class="tasks" id="ph-tasks"></div></div>
</div>
<script>setInterval(()=>{fetch('/api/consciousness/parallel/status').then(r=>r.json()).then(d=>{document.getElementById('pc-load').style.width=d.pc.load+'%';document.getElementById('pc-pct').textContent=d.pc.load+'%';document.getElementById('ph-load').style.width=d.phone.load+'%';document.getElementById('ph-pct').textContent=d.phone.load+'%';document.getElementById('pc-tasks').innerHTML=d.pc.tasks.map(t=>'<div class="task">'+t+'</div>').join('');document.getElementById('ph-tasks').innerHTML=d.phone.tasks.map(t=>'<div class="task">'+t+'</div>').join('')})},3000)</script>
</body></html>"""
