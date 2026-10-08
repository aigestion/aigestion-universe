from flask import Blueprint, jsonify, request

skill_creator_bp = Blueprint("skill_creator", __name__)

_skills_created = []

@skill_creator_bp.route("/api/hermes/advanced/skill-creator/status")
def sc_status():
    return jsonify({"skills_created": _skills_created, "total": len(_skills_created)})

@skill_creator_bp.route("/api/hermes/advanced/skill-creator/create", methods=["POST"])
def sc_create():
    data = request.json or {}
    skill = {
        "name": data.get("name", "New Skill"),
        "description": data.get("description", ""),
        "category": data.get("category", "general"),
        "auto_generated": True
    }
    _skills_created.append(skill)
    return jsonify({"ok": True, "skill": skill})

@skill_creator_bp.route("/api/hermes/advanced/skill-creator/web")
def sc_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Skill Creator</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
input,textarea{width:100%;background:#111;border:1px solid #333;color:#00f0ff;padding:8px;border-radius:6px;font-family:monospace;margin:5px 0}
textarea{height:80px}
button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:8px 16px;border-radius:6px;cursor:pointer}
.skill{background:#111;border:1px solid #00ff88;border-radius:8px;padding:10px;margin:5px 0}
</style></head><body><h1>SKILL CREATOR</h1>
<input id="name" placeholder="Skill name"><textarea id="desc" placeholder="Description"></textarea>
<button onclick="create()">Create Skill</button>
<div id="skills"></div>
<script>function load(){fetch('/api/hermes/advanced/skill-creator/status').then(r=>r.json()).then(d=>{document.getElementById('skills').innerHTML=d.skills_created.map(s=>'<div class="skill"><h3>'+s.name+'</h3><p>'+s.description+'</p></div>').join('')})}
function create(){fetch('/api/hermes/advanced/skill-creator/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('name').value,description:document.getElementById('desc').value})}).then(()=>{document.getElementById('name').value='';document.getElementById('desc').value='';load()})}
load()</script></body></html>"""
