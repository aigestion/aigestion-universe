from flask import Blueprint, jsonify, request

meeting_prep_bp = Blueprint("meeting_prep", __name__)

SKILL = {"name": "Meeting Prep", "description": "Prepare meeting context, agenda, and talking points"}

@meeting_prep_bp.route("/api/hermes/skills/meeting/status")
def m_status():
    return jsonify(SKILL)

@meeting_prep_bp.route("/api/hermes/skills/meeting/prepare", methods=["POST"])
def m_prepare():
    data = request.json or {}
    name = data.get("name", "Unknown Meeting")
    prep = {
        "meeting": name,
        "agenda": [
            "Review previous action items",
            "Current status update",
            "Open discussion",
            "Next steps"
        ],
        "talking_points": [
            "Start with positives",
            "Address blockers clearly",
            "Propose solutions",
            "Define clear action items"
        ],
        "documents_to_prepare": ["Status report", "Relevant data", "Previous meeting notes"],
        "reminders": ["Send agenda 1h before", "Prepare screen share", "Test audio/video"]
    }
    return jsonify(prep)

@meeting_prep_bp.route("/api/hermes/skills/meeting/web")
def m_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Meeting Prep</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
input{width:300px;background:#111;border:1px solid #333;color:#00f0ff;padding:8px;border-radius:6px;font-family:monospace}
button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:8px 16px;border-radius:6px;cursor:pointer;margin-left:10px}
.prep{margin-top:20px;background:#111;border-radius:12px;padding:20px}
.prep h3{color:#00f0ff}
ul{padding-left:20px} li{margin:5px 0}
</style></head><body>
<h1>MEETING PREP</h1>
<input id="name" placeholder="Meeting name"><button onclick="prepare()">Prepare</button>
<div id="prep"></div>
<script>function prepare(){fetch('/api/hermes/skills/meeting/prepare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('name').value})}).then(r=>r.json()).then(d=>{document.getElementById('prep').innerHTML='<div class="prep"><h3>'+d.meeting+'</h3><h4>Agenda</h4><ul>'+d.agenda.map(a=>'<li>'+a+'</li>').join('')+'</ul><h4>Talking Points</h4><ul>'+d.talking_points.map(t=>'<li>'+t+'</li>').join('')+'</ul><h4>Documents</h4><ul>'+d.documents_to_prepare.map(doc=>'<li>'+doc+'</li>').join('')+'</ul></div>'})}</script></body></html>"""
