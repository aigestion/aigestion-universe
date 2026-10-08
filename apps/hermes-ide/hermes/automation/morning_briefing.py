from flask import Blueprint, jsonify

morning_bp = Blueprint("morning_briefing", __name__)

@morning_bp.route("/api/hermes/automation/morning/status")
def m_status():
    return jsonify({"briefing": {"weather": "Sunny 22C", "calendar": ["Standup 9am", "Review 2pm"], "emails": 3, "tasks": ["Deploy feature", "Review PR"], "mood": "ready"}})

@morning_bp.route("/api/hermes/automation/morning/web")
def m_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Morning Briefing</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.briefing{max-width:500px;margin:0 auto}
.section{background:#111;border-radius:12px;padding:15px;margin:10px 0}
.section h3{color:#00f0ff;margin-top:0}
.item{padding:5px;border-bottom:1px solid #222}
</style></head><body><div class="briefing"><h1>MORNING BRIEFING</h1>
<div class="section"><h3>Weather</h3><div class="item">Sunny 22C</div></div>
<div class="section"><h3>Calendar</h3><div class="item">Standup 9am</div><div class="item">Review 2pm</div></div>
<div class="section"><h3>Emails</h3><div class="item">3 unread</div></div>
<div class="section"><h3>Tasks</h3><div class="item">Deploy feature</div><div class="item">Review PR</div></div></div></body></html>"""
