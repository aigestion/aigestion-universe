from flask import Blueprint, jsonify

reporter_bp = Blueprint("auto_reporter", __name__)

@reporter_bp.route("/api/hermes/automation/reporter/status")
def r_status():
    return jsonify({"reports": [{"name": "Daily", "last": "2026-09-13", "status": "generated"}, {"name": "Weekly", "last": "2026-09-08", "status": "generated"}, {"name": "Monthly", "last": "2026-09-01", "status": "pending"}]})

@reporter_bp.route("/api/hermes/automation/reporter/web")
def r_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Auto Reporter</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.report{background:#111;border:1px solid #333;border-radius:8px;padding:15px;margin:10px 0;display:flex;justify-content:space-between}
</style></head><body><h1>AUTO REPORTER</h1><div id="reports"></div>
<script>fetch('/api/hermes/automation/reporter/status').then(r=>r.json()).then(d=>{document.getElementById('reports').innerHTML=d.reports.map(r=>'<div class="report"><span>'+r.name+'</span><span>'+r.last+'</span><span>'+r.status+'</span></div>').join('')})</script></body></html>"""
