from flask import Blueprint, jsonify

growth_track_bp = Blueprint("growth_tracking", __name__)
_metrics = {"skills_learned": 12, "tasks_completed": 156, "memories_formed": 89, "improvements": 23}

@growth_track_bp.route("/api/hermes/personality/growth/status")
def g_status():
    return jsonify(_metrics)

@growth_track_bp.route("/api/hermes/personality/growth/web")
def g_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Growth Tracking</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.metrics{display:grid;grid-template-columns:repeat(2,1fr);gap:15px;max-width:500px;margin:0 auto}
.metric{background:#111;border-radius:12px;padding:20px;text-align:center}
.metric .num{font-size:30px;color:#00ff88}
</style></head><body><h1 style="text-align:center">GROWTH TRACKING</h1>
<div class="metrics">
<div class="metric"><div class="num" id="skills">12</div><p>Skills Learned</p></div>
<div class="metric"><div class="num" id="tasks">156</div><p>Tasks Completed</p></div>
<div class="metric"><div class="num" id="memories">89</div><p>Memories Formed</p></div>
<div class="metric"><div class="num" id="improvements">23</div><p>Improvements</p></div>
</div>
<script>fetch('/api/hermes/personality/growth/status').then(r=>r.json()).then(d=>{document.getElementById('skills').textContent=d.skills_learned;document.getElementById('tasks').textContent=d.tasks_completed;document.getElementById('memories').textContent=d.memories_formed;document.getElementById('improvements').textContent=d.improvements})</script></body></html>"""
