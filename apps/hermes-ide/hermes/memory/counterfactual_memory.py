from flask import Blueprint, jsonify, request

counterfactual_bp = Blueprint("counterfactual_memory", __name__)
_reflections = [
    {"actual": "Manual deployment", "alternative": "Automated CI/CD", "lesson": "Automation saves time", "impact": "high"},
    {"actual": "No tests", "alternative": "With tests", "lesson": "Tests prevent bugs", "impact": "critical"}
]

@counterfactual_bp.route("/api/hermes/memory/counterfactual/status")
def cf_status():
    return jsonify({"reflections": _reflections})

@counterfactual_bp.route("/api/hermes/memory/counterfactual/add", methods=["POST"])
def cf_add():
    data = request.json or {}
    _reflections.append({"actual": data.get("actual",""), "alternative": data.get("alternative",""), "lesson": data.get("lesson",""), "impact": data.get("impact","medium")})
    return jsonify({"ok": True})

@counterfactual_bp.route("/api/hermes/memory/counterfactual/web")
def cf_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Counterfactual Memory</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.reflect{background:#111;border:1px solid #333;border-radius:8px;padding:15px;margin:10px 0}
.actual{color:#ff8800} .alt{color:#00ff88} .lesson{color:#00f0ff;font-style:italic}
</style></head><body><h1>COUNTERFACTUAL MEMORY</h1><div id="refs"></div>
<script>fetch('/api/hermes/memory/counterfactual/status').then(r=>r.json()).then(d=>{document.getElementById('refs').innerHTML=d.reflections.map(r=>'<div class="reflect"><p class="actual">Actual: '+r.actual+'</p><p class="alt">Alternative: '+r.alternative+'</p><p class="lesson">Lesson: '+r.lesson+'</p></div>').join('')})</script></body></html>"""
