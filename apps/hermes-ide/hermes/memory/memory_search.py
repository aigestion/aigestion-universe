from flask import Blueprint, jsonify, request

mem_search_bp = Blueprint("memory_search", __name__)

@mem_search_bp.route("/api/hermes/memory/search")
def ms_search():
    q = request.args.get("q", "").lower()
    results = [
        {"type": "episodic", "content": "Deployment event", "relevance": 0.9},
        {"type": "semantic", "content": "Python concept", "relevance": 0.8},
        {"type": "procedural", "content": "Git deployment procedure", "relevance": 0.85}
    ]
    return jsonify({"query": q, "results": results})

@mem_search_bp.route("/api/hermes/memory/search/web")
def ms_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Memory Search</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
input{width:400px;background:#111;border:1px solid #333;color:#00f0ff;padding:10px;border-radius:8px;font-family:monospace}
button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:10px 20px;border-radius:6px;cursor:pointer;margin-left:10px}
.result{background:#111;padding:8px;margin:5px 0;border-radius:6px;border-left:3px solid #00f0ff}
</style></head><body><h1>MEMORY SEARCH</h1>
<input id="q" placeholder="Search memories..."><button onclick="search()">Search</button>
<div id="results"></div>
<script>function search(){fetch('/api/hermes/memory/search?q='+document.getElementById('q').value).then(r=>r.json()).then(d=>{document.getElementById('results').innerHTML=d.results.map(r=>'<div class="result"><strong>['+r.type+']</strong> '+r.content+' <small>(relevance: '+r.relevance+')</small></div>').join('')})}</script></body></html>"""
