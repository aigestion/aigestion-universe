import json
import time
from pathlib import Path

from flask import Blueprint, jsonify, request

memory_sync_bp = Blueprint("shared_memory_sync", __name__)
DATA = Path(__file__).parent.parent / "data"
DATA.mkdir(exist_ok=True)
_mem_file = DATA / "shared_memory.json"

def _load():
    if _mem_file.exists():
        return json.loads(_mem_file.read_text(encoding="utf-8"))
    return {"nodes": [], "last_sync": 0}

def _save(data):
    _mem_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

@memory_sync_bp.route("/api/hermes/memory/sync/status")
def ms_status():
    return jsonify(_load())

@memory_sync_bp.route("/api/hermes/memory/sync/push", methods=["POST"])
def ms_push():
    data = request.json or {}
    mem = _load()
    node = {
        "id": str(int(time.time()*1000))[-8:],
        "content": data.get("content", ""),
        "type": data.get("type", "note"),
        "source": data.get("source", "hermes"),
        "time": time.time()
    }
    mem["nodes"].append(node)
    mem["last_sync"] = time.time()
    if len(mem["nodes"]) > 500:
        mem["nodes"] = mem["nodes"][-500:]
    _save(mem)
    return jsonify({"ok": True, "node": node})

@memory_sync_bp.route("/api/hermes/memory/sync/pull")
def ms_pull():
    since = float(request.args.get("since", 0))
    mem = _load()
    nodes = [n for n in mem["nodes"] if n["time"] > since]
    return jsonify({"nodes": nodes[-50:], "total": len(mem["nodes"])})

@memory_sync_bp.route("/api/hermes/memory/sync/web")
def ms_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Shared Memory</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.node{background:#111;border:1px solid #333;border-radius:8px;padding:10px;margin:5px 0}
.add{margin-top:20px} textarea{width:100%;height:80px;background:#0a0a0f;border:1px solid #333;color:#00f0ff;padding:8px;border-radius:6px;font-family:monospace}
button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:8px 16px;border-radius:6px;cursor:pointer;margin-top:5px}
</style></head><body>
<h1>SHARED MEMORY</h1>
<div id="nodes"></div>
<div class="add"><textarea id="content" placeholder="Memory content..."></textarea><br><button onclick="add()">Add Memory</button></div>
<script>function load(){fetch('/api/hermes/memory/sync/pull').then(r=>r.json()).then(d=>{document.getElementById('nodes').innerHTML=d.nodes.reverse().map(n=>'<div class="node"><strong>'+n.source+'</strong>: '+n.content+'</div>').join('')})}
function add(){fetch('/api/hermes/memory/sync/push',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:document.getElementById('content').value,source:'hermes'})}).then(()=>{document.getElementById('content').value='';load()})}
load()</script></body></html>"""
