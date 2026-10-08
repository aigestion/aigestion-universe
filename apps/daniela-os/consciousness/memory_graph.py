import json
import time
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request

memory_bp = Blueprint("memory_graph", __name__)
DATA = Path(__file__).parent.parent / "data"
DATA.mkdir(exist_ok=True)
_nodes_file = DATA / "memory_nodes.json"


def _load():
    if _nodes_file.exists():
        return json.loads(_nodes_file.read_text(encoding="utf-8"))
    return []


def _save(nodes):
    _nodes_file.write_text(json.dumps(nodes, ensure_ascii=False, indent=2), encoding="utf-8")


@memory_bp.route("/api/consciousness/memory/graph")
def mg_graph():
    return jsonify({"nodes": _load()})


@memory_bp.route("/api/consciousness/memory/add", methods=["POST"])
def mg_add():
    data = request.json or {}
    node = {
        "id": str(uuid.uuid4())[:8],
        "content": data.get("content", ""),
        "type": data.get("type", "note"),
        "tags": data.get("tags", []),
        "connections": data.get("connections", []),
        "created": time.time(),
        "strength": 1.0,
    }
    nodes = _load()
    nodes.append(node)
    _save(nodes)
    return jsonify({"ok": True, "node": node})


@memory_bp.route("/api/consciousness/memory/search")
def mg_search():
    q = request.args.get("q", "").lower()
    nodes = _load()
    results = [
        n
        for n in nodes
        if q in n.get("content", "").lower() or any(q in t for t in n.get("tags", []))
    ]
    return jsonify({"results": results[:20]})


@memory_bp.route("/api/consciousness/memory/connect", methods=["POST"])
def mg_connect():
    data = request.json or {}
    nodes = _load()
    for n in nodes:
        if n["id"] == data.get("from"):
            if data.get("to") not in n["connections"]:
                n["connections"].append(data["to"])
            n["strength"] = min(10, n["strength"] + 0.1)
    _save(nodes)
    return jsonify({"ok": True})


@memory_bp.route("/api/consciousness/memory/web")
def mg_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Memory Graph</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace}
canvas{display:block} .add-form{position:fixed;top:20px;right:20px;background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;width:250px}
.add-form input,.add-form textarea{width:100%;background:#0a0a0f;border:1px solid #333;color:#00f0ff;padding:8px;border-radius:6px;margin:5px 0;font-family:monospace}
.add-form button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:8px 16px;border-radius:6px;cursor:pointer;width:100%;margin-top:5px}
</style></head><body>
<canvas id="canvas"></canvas>
<div class="add-form">
<h3>MEMORY NODE</h3>
<textarea id="content" placeholder="Memory content..."></textarea>
<input id="tags" placeholder="Tags (comma separated)">
<button onclick="addNode()">Add Memory</button>
<button onclick="search()">Search</button>
</div>
<script>const c=document.getElementById('canvas');const ctx=c.getContext('2d');
c.width=window.innerWidth;c.height=window.innerHeight;
let nodes=[];
function draw(){ctx.clearRect(0,0,c.width,c.height);nodes.forEach((n,i)=>{n.x+=(Math.random()-.5)*.5;n.y+=(Math.random()-.5)*.5;n.x=Math.max(50,Math.min(c.width-50,n.x));n.y=Math.max(50,Math.min(c.height-50,n.y));ctx.beginPath();ctx.arc(n.x,n.y,8,0,Math.PI*2);ctx.fillStyle='#00f0ff';ctx.fill();n.connections.forEach(cid=>{const t=nodes.find(x=>x.id===cid);if(t){ctx.beginPath();ctx.moveTo(n.x,n.y);ctx.lineTo(t.x,t.y);ctx.strokeStyle='#00f0ff44';ctx.stroke()}})});
requestAnimationFrame(draw)}
function load(){fetch('/api/consciousness/memory/graph').then(r=>r.json()).then(d=>{nodes=d.nodes.map((n,i)=>({...n,x:100+Math.random()*600,y:100+Math.random()*400}));draw()})}
function addNode(){fetch('/api/consciousness/memory/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:document.getElementById('content').value,tags:document.getElementById('tags').value.split(',').map(s=>s.trim())})}).then(()=>{document.getElementById('content').value='';load()})}
function search(){const q=prompt('Search:');if(q)fetch('/api/consciousness/memory/search?q='+q).then(r=>r.json()).then(d=>alert(d.results.map(r=>r.content).join('\\n')))};
load();setInterval(load,10000)
</script></body></html>"""
