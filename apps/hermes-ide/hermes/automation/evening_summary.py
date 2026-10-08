from flask import Blueprint, jsonify

evening_bp = Blueprint("evening_summary", __name__)

@evening_bp.route("/api/hermes/automation/evening/status")
def e_status():
    return jsonify({"summary": {"completed": 5, "pending": 2, "highlights": ["Deployed 114 systems", "Fixed port 9222 bug"], "tomorrow": ["Morning meeting", "Code review"]}})

@evening_bp.route("/api/hermes/automation/evening/web")
def e_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Evening Summary</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.summary{max-width:500px;margin:0 auto}
.section{background:#111;border-radius:12px;padding:15px;margin:10px 0}
.section h3{color:#ff8800;margin-top:0}
.item{padding:5px;border-bottom:1px solid #222}
</style></head><body><div class="summary"><h1>EVENING SUMMARY</h1>
<div class="section"><h3>Today</h3><div class="item">Completed: 5 tasks</div><div class="item">Pending: 2 tasks</div></div>
<div class="section"><h3>Highlights</h3><div class="item">Deployed 114 systems</div><div class="item">Fixed port 9222 bug</div></div>
<div class="section"><h3>Tomorrow</h3><div class="item">Morning meeting</div><div class="item">Code review</div></div></div></body></html>"""
