from flask import Blueprint, jsonify, request

creative_bp = Blueprint("creative_writer", __name__)

SKILL = {"name": "Creative Writer", "description": "Write emails, posts, articles with user's style"}

@creative_bp.route("/api/hermes/skills/creative/status")
def c_status():
    return jsonify(SKILL)

@creative_bp.route("/api/hermes/skills/creative/write", methods=["POST"])
def c_write():
    data = request.json or {}
    topic = data.get("topic", "")
    style = data.get("style", "professional")
    data.get("length", "medium")
    return jsonify({
        "topic": topic,
        "style": style,
        "draft": f"[Generated {style} text about {topic}...]",
        "suggestions": ["Add more specific examples", "Include a call to action"]
    })

@creative_bp.route("/api/hermes/skills/creative/web")
def c_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Creative Writer</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
input,textarea,select{width:100%;background:#111;border:1px solid #333;color:#00f0ff;padding:8px;border-radius:6px;font-family:monospace;margin:5px 0}
textarea{height:100px}
select{width:auto}
button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:8px 16px;border-radius:6px;cursor:pointer}
.draft{margin-top:10px;padding:15px;background:#111;border-radius:8px;white-space:pre-wrap}
</style></head><body>
<h1>CREATIVE WRITER</h1>
<input id="topic" placeholder="Topic"><br>
<select id="style"><option>professional</option><option>casual</option><option>formal</option><option>creative</option></select>
<textarea id="prompt" placeholder="Additional instructions..."></textarea><br>
<button onclick="write()">Generate</button>
<div class="draft" id="draft"></div>
<script>function write(){fetch('/api/hermes/skills/creative/write',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic:document.getElementById('topic').value,style:document.getElementById('style').value})}).then(r=>r.json()).then(d=>{document.getElementById('draft').textContent=d.draft})}</script></body></html>"""
