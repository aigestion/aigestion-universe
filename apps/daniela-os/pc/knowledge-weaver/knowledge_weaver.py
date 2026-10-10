"""
System 20: Knowledge Weaver
Connects ideas between different apps: email mentions file which is in project
"""

import json
import re
import time
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

CONNECTIONS_FILE = DATA_DIR / "connections.json"


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_entities(text):
    entities = {"apps": [], "files": [], "projects": [], "people": [], "dates": []}
    file_matches = re.findall(r"[\w/\\:.]+\.\w{2,4}", text)
    entities["files"] = list(set(file_matches))[:5]
    date_matches = re.findall(r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}", text)
    entities["dates"] = list(set(date_matches))[:3]
    name_patterns = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", text)
    entities["people"] = list(set(name_patterns))[:5]
    app_names = [
        "slack",
        "discord",
        "chrome",
        "vscode",
        "github",
        "notion",
        "email",
        "calendar",
        "drive",
        "dropbox",
    ]
    for app in app_names:
        if app.lower() in text.lower():
            entities["apps"].append(app)
    return entities


@app.route("/")
def index():
    return WEAVER_HTML


@app.route("/api/weaver/connections")
def get_connections():
    return jsonify(load_json(CONNECTIONS_FILE, {"connections": []}))


@app.route("/api/weaver/add", methods=["POST"])
def add_connection():
    data = request.json or {}
    entities = extract_entities(data.get("text", "") + " " + data.get("context", ""))
    connection = {
        "id": int(time.time()),
        "title": data.get("title", ""),
        "text": data.get("text", ""),
        "source": data.get("source", "manual"),
        "entities": entities,
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M"),
    }
    conns = load_json(CONNECTIONS_FILE, {"connections": []})
    conns["connections"].append(connection)
    save_json(CONNECTIONS_FILE, conns)
    return jsonify({"ok": True, "entities": entities})


@app.route("/api/weaver/graph")
def graph_data():
    conns = load_json(CONNECTIONS_FILE, {"connections": []}).get("connections", [])
    nodes = {}
    links = []
    for c in conns:
        title = c.get("title", "Untitled")
        if title not in nodes:
            nodes[title] = {"id": title, "count": 0, "type": "source"}
        nodes[title]["count"] += 1
        for entity_type, values in c.get("entities", {}).items():
            for v in values:
                if v not in nodes:
                    nodes[v] = {"id": v, "count": 0, "type": entity_type}
                nodes[v]["count"] += 1
                links.append({"source": title, "target": v})
    unique_links = []
    seen = set()
    for ln in links:
        key = f"{ln['source']}->{ln['target']}"
        if key not in seen:
            seen.add(key)
            unique_links.append(ln)
    return jsonify({"nodes": list(nodes.values()), "links": unique_links})


@app.route("/api/weaver/search")
def search():
    q = request.args.get("q", "").lower()
    conns = load_json(CONNECTIONS_FILE, {"connections": []}).get("connections", [])
    results = []
    for c in conns:
        searchable = f"{c.get('title', '')} {c.get('text', '')}".lower()
        if q in searchable or not q:
            results.append(c)
    results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return jsonify({"results": results[:30]})


@app.route("/api/weaver/delete", methods=["POST"])
def delete_connection():
    data = request.json or {}
    cid = data.get("id")
    conns = load_json(CONNECTIONS_FILE, {"connections": []})
    conns["connections"] = [c for c in conns["connections"] if c["id"] != cid]
    save_json(CONNECTIONS_FILE, conns)
    return jsonify({"ok": True})


WEAVER_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Knowledge Weaver</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:10px 16px;border-radius:8px;cursor:pointer;font-family:inherit}
.btn:hover{background:rgba(0,240,255,0.2)}
.input{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:10px;border-radius:6px;font-family:inherit;font-size:12px;width:100%}
.textarea{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:10px;border-radius:6px;font-family:inherit;font-size:12px;width:100%;min-height:80px;resize:vertical}
.add-form{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.15);border-radius:10px;padding:16px;margin-bottom:16px;display:none}
.add-form.show{display:block}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.graph-area{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;height:400px;position:relative;overflow:hidden}
.connections-list{max-height:400px;overflow-y:auto}
.conn-card{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:8px;padding:10px;margin-bottom:8px}
.conn-title{font-size:13px;color:#00f0ff}
.conn-text{font-size:11px;color:#94a3b8;margin:4px 0}
.conn-entities{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
.entity-tag{padding:2px 6px;border-radius:4px;font-size:9px;font-family:'Share Tech Mono',monospace}
.entity-tag.app{background:rgba(139,92,246,0.15);color:#8b5cf6}
.entity-tag.file{background:rgba(0,240,255,0.1);color:#00f0ff}
.entity-tag.person{background:rgba(34,197,94,0.15);color:#22c55e}
.entity-tag.date{background:rgba(245,158,11,0.15);color:#f59e0b}
.entity-tag.project{background:rgba(239,68,68,0.15);color:#ef4444}
#graphCanvas{width:100%;height:100%}
</style></head><body>
<h1>KNOWLEDGE WEAVER</h1>
<button class="btn" onclick="toggleForm()">+ Add Connection</button>
<div class="add-form" id="addForm">
  <input class="input" id="title" placeholder="Title (e.g. 'Sprint Planning')" style="margin-bottom:8px">
  <textarea class="textarea" id="text" placeholder="Describe the connection... mention files, people, apps, dates"></textarea>
  <button class="btn" onclick="addConn()" style="margin-top:8px">Weave Connection</button>
</div>
<div class="grid">
  <div class="graph-area"><canvas id="graphCanvas"></canvas></div>
  <div class="connections-list" id="connections"></div>
</div>
<script>
function toggleForm(){document.getElementById('addForm').classList.toggle('show')}
async function load(){
  const r=await(await fetch('/api/weaver/connections')).json();
  document.getElementById('connections').innerHTML=(r.connections||[]).reverse().map(c=>
    '<div class="conn-card"><div class="conn-title">'+c.title+'</div>'+
    '<div class="conn-text">'+(c.text||'').substring(0,100)+'</div>'+
    '<div class="conn-entities">'+Object.entries(c.entities||{}).flatMap(([type,vals])=>vals.map(v=>'<span class="entity-tag '+type.slice(0,-1)+'">'+v+'</span>')).join('')+'</div>'+
    '<div style="font-size:9px;color:#64748b;margin-top:4px">'+c.date+' | '+c.source+'</div></div>'
  ).join('')||'<div style="color:#64748b">No connections yet</div>';
  drawGraph();
}
async function addConn(){
  const title=document.getElementById('title').value;
  const text=document.getElementById('text').value;
  if(!text.trim())return;
  await fetch('/api/weaver/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,text,source:'manual'})});
  document.getElementById('title').value='';document.getElementById('text').value='';
  document.getElementById('addForm').classList.remove('show');load();
}
async function drawGraph(){
  const g=await(await fetch('/api/weaver/graph')).json();
  const canvas=document.getElementById('graphCanvas');
  const ctx=canvas.getContext('2d');
  canvas.width=canvas.parentElement.clientWidth;
  canvas.height=canvas.parentElement.clientHeight;
  ctx.clearRect(0,0,canvas.width,canvas.height);
  const nodes=g.nodes||[];
  const links=g.links||[];
  if(!nodes.length)return;
  const cx=canvas.width/2,cy=canvas.height/2;
  const nodeMap={};
  nodes.forEach((n,i)=>{const a=(i/nodes.length)*Math.PI*2,r=120+Math.random()*60;n.x=cx+Math.cos(a)*r;n.y=cy+Math.sin(a)*r;nodeMap[n.id]=n});
  ctx.strokeStyle='rgba(0,240,255,0.15)';ctx.lineWidth=1;
  links.forEach(l=>{const s=nodeMap[l.source],t=nodeMap[l.target];if(s&&t){ctx.beginPath();ctx.moveTo(s.x,s.y);ctx.lineTo(t.x,t.y);ctx.stroke()}});
  nodes.forEach(n=>{const r=Math.min(20,4+n.count*2);ctx.beginPath();ctx.arc(n.x,n.y,r,0,Math.PI*2);ctx.fillStyle='rgba(0,240,255,0.3)';ctx.fill();ctx.strokeStyle='#00f0ff';ctx.lineWidth=1.5;ctx.stroke();ctx.fillStyle='#e2e8f0';ctx.font='9px Share Tech Mono';ctx.textAlign='center';ctx.fillText(n.id.substring(0,12),n.x,n.y+r+12)});
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 20] Knowledge Weaver starting on port 5030...")
    app.run(host="0.0.0.0", port=5030, debug=False)
