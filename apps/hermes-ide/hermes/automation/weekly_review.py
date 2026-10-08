from flask import Blueprint, jsonify

weekly_bp = Blueprint("weekly_review", __name__)

@weekly_bp.route("/api/hermes/automation/weekly/status")
def w_status():
    return jsonify({"review": {"tasks_completed": 23, "productivity": 85, "top_categories": ["coding", "deployment", "planning"], "improvements": ["More focused mornings", "Better time blocking"]}})

@weekly_bp.route("/api/hermes/automation/weekly/web")
def w_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Weekly Review</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.review{max-width:500px;margin:0 auto}
.stat{background:#111;border-radius:12px;padding:20px;margin:10px 0;text-align:center}
.stat .num{font-size:40px;color:#00ff88}
</style></head><body><div class="review"><h1>WEEKLY REVIEW</h1>
<div class="stat"><div class="num">23</div><p>Tasks Completed</p></div>
<div class="stat"><div class="num">85%</div><p>Productivity Score</p></div>
<div class="section"><h3>Top Categories</h3><p>Coding, Deployment, Planning</p></div>
<div class="section"><h3>Improvements</h3><ul><li>More focused mornings</li><li>Better time blocking</li></ul></div></div></body></html>"""
