from flask import Blueprint, jsonify, request

meeting_bp = Blueprint("meeting_predictor", __name__)
_meetings = [
    {
        "id": 1,
        "name": "Standup",
        "time": "09:00",
        "prep": ["calendar", "yesterday_summary"],
        "auto_prepare": True,
    },
    {
        "id": 2,
        "name": "Sprint Review",
        "time": "15:00",
        "prep": ["jira_board", "demo_links"],
        "auto_prepare": True,
    },
]


@meeting_bp.route("/api/proactive/meetings/status")
def m_status():
    return jsonify({"meetings": _meetings})


@meeting_bp.route("/api/proactive/meetings/add", methods=["POST"])
def m_add():
    data = request.json or {}
    _meetings.append(
        {
            "id": len(_meetings) + 1,
            "name": data.get("name", "New Meeting"),
            "time": data.get("time", "00:00"),
            "prep": data.get("prep", []),
            "auto_prepare": data.get("auto_prepare", True),
        }
    )
    return jsonify({"ok": True})


@meeting_bp.route("/api/proactive/meetings/web")
def m_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Meeting Predictor</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.meeting{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;margin:10px 0}
.meeting h3{margin-top:0;color:#00f0ff}
.prep{display:flex;gap:8px;flex-wrap:wrap}
.prep-item{background:#00f0ff11;padding:4px 10px;border-radius:12px;font-size:12px}
</style></head><body>
<h1>MEETING PREDICTOR</h1>
<div id="list"></div>
<script>fetch('/api/proactive/meetings/status').then(r=>r.json()).then(d=>{document.getElementById('list').innerHTML=d.meetings.map(m=>'<div class="meeting"><h3>'+m.name+'</h3><p>Time: '+m.time+'</p><div class="prep">'+m.prep.map(p=>'<span class="prep-item">'+p+'</span>').join('')+'</div></div>').join('')})</script>
</body></html>"""
