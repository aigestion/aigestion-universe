from flask import Blueprint, jsonify, request

research_bp = Blueprint("research_assistant", __name__)

SKILL = {"name": "Research Assistant", "description": "Web research, synthesis, and report generation"}

@research_bp.route("/api/hermes/skills/research/status")
def r_status():
    return jsonify(SKILL)

@research_bp.route("/api/hermes/skills/research/query", methods=["POST"])
def r_query():
    data = request.json or {}
    query = data.get("query", "")
    return jsonify({
        "query": query,
        "results": [
            {"title": "Result 1", "summary": "First relevant finding", "source": "web"},
            {"title": "Result 2", "summary": "Second relevant finding", "source": "docs"},
            {"title": "Result 3", "summary": "Third relevant finding", "source": "academic"}
        ],
        "synthesis": f"Research on '{query}' shows multiple relevant sources. Key findings include...",
        "confidence": 0.85
    })

@research_bp.route("/api/hermes/skills/research/web")
def r_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Research Assistant</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
input{width:400px;background:#111;border:1px solid #333;color:#00f0ff;padding:8px;border-radius:6px;font-family:monospace}
button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:8px 16px;border-radius:6px;cursor:pointer;margin-left:10px}
.results{margin-top:20px}
.result{background:#111;border:1px solid #333;border-radius:8px;padding:10px;margin:5px 0}
</style></head><body>
<h1>RESEARCH ASSISTANT</h1>
<input id="query" placeholder="Research query..."><button onclick="search()">Search</button>
<div class="results" id="results"></div>
<script>function search(){fetch('/api/hermes/skills/research/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:document.getElementById('query').value})}).then(r=>r.json()).then(d=>{document.getElementById('results').innerHTML='<h3>Synthesis</h3><p>'+d.synthesis+'</p><h3>Results</h3>'+d.results.map(r=>'<div class="result"><h4>'+r.title+'</h4><p>'+r.summary+'</p><small>'+r.source+'</small></div>').join('')})}</script></body></html>"""
