"""
System 11: AI Memory Palace
Semantic activity history - remembers everything you do on your PC
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "memories"
DATA_DIR.mkdir(exist_ok=True)


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.route("/")
def index():
    return MEMORY_HTML


@app.route("/api/memory/log", methods=["POST"])
def log_activity():
    data = request.json or {}
    entry = {
        "id": hashlib.md5(f"{time.time()}{data.get('text', '')}".encode()).hexdigest()[:8],
        "timestamp": time.time(),
        "datetime": datetime.now().isoformat(),
        "type": data.get("type", "general"),
        "title": data.get("title", ""),
        "text": data.get("text", ""),
        "app": data.get("app", ""),
        "tags": data.get("tags", []),
        "importance": data.get("importance", 5),
    }
    day = datetime.now().strftime("%Y-%m-%d")
    day_file = DATA_DIR / f"{day}.json"
    memories = load_json(day_file, {"entries": []})
    memories["entries"].append(entry)
    save_json(day_file, memories)
    return jsonify({"ok": True, "id": entry["id"]})


@app.route("/api/memory/search")
def search_memories():
    query = request.args.get("q", "").lower()
    days = int(request.args.get("days", 7))
    results = []
    for i in range(days):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_file = DATA_DIR / f"{day}.json"
        if not day_file.exists():
            continue
        memories = load_json(day_file, {"entries": []})
        for entry in memories.get("entries", []):
            score = 0
            searchable = f"{entry.get('title', '')} {entry.get('text', '')} {' '.join(entry.get('tags', []))}".lower()
            for word in query.split():
                if word in searchable:
                    score += 1
            if score > 0 or not query:
                entry["relevance"] = score
                results.append(entry)
    results.sort(key=lambda x: (x.get("relevance", 0), x.get("timestamp", 0)), reverse=True)
    return jsonify({"results": results[:50], "total": len(results)})


@app.route("/api/memory/timeline")
def timeline():
    days = int(request.args.get("days", 7))
    timeline_data = []
    for i in range(days):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_file = DATA_DIR / f"{day}.json"
        if not day_file.exists():
            continue
        memories = load_json(day_file, {"entries": []})
        if memories.get("entries"):
            timeline_data.append(
                {"date": day, "count": len(memories["entries"]), "entries": memories["entries"][:5]}
            )
    return jsonify({"timeline": timeline_data})


@app.route("/api/memory/stats")
def stats():
    total = 0
    types = {}
    for f in DATA_DIR.glob("*.json"):
        data = load_json(f, {"entries": []})
        entries = data.get("entries", [])
        total += len(entries)
        for e in entries:
            t = e.get("type", "general")
            types[t] = types.get(t, 0) + 1
    return jsonify({"total_memories": total, "types": types})


MEMORY_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>AI Memory Palace</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.search-bar{display:flex;gap:8px;margin-bottom:20px}
.search-bar input{flex:1;background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.2);color:#e2e8f0;padding:10px 16px;border-radius:8px;font-size:14px;font-family:inherit}
.search-bar input:focus{outline:none;border-color:#00f0ff}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:10px 16px;border-radius:8px;cursor:pointer;font-family:inherit;font-size:13px}
.btn:hover{background:rgba(0,240,255,0.2)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.card{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px}
.card-time{font-size:10px;color:#64748b;font-family:'Share Tech Mono',monospace}
.card-title{font-size:14px;color:#00f0ff;margin:6px 0}
.card-text{font-size:12px;color:#94a3b8}
.card-tags{display:flex;gap:4px;margin-top:8px;flex-wrap:wrap}
.tag{background:rgba(0,240,255,0.08);color:#00f0ff;padding:2px 8px;border-radius:4px;font-size:9px}
.stats{position:fixed;bottom:20px;right:20px;font-size:10px;color:#64748b;font-family:'Share Tech Mono',monospace}
.add-form{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.15);border-radius:10px;padding:16px;margin-bottom:20px;display:none}
.add-form.show{display:block}
.form-row{display:flex;gap:8px;margin-bottom:8px}
.form-row input,.form-row select{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px;flex:1}
.form-row textarea{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px;flex:1;min-height:60px;resize:vertical}
</style></head><body>
<h1>AI MEMORY PALACE</h1>
<div class="search-bar">
  <input id="query" placeholder="Search your memories..." onkeyup="search()">
  <button class="btn" onclick="toggleAdd()">+ New</button>
</div>
<div class="add-form" id="addForm">
  <div class="form-row">
    <input id="newTitle" placeholder="Title">
    <select id="newType"><option>general</option><option>idea</option><option>task</option><option>note</option><option>event</option></select>
  </div>
  <div class="form-row"><textarea id="newText" placeholder="What do you want to remember?"></textarea></div>
  <div class="form-row">
    <input id="newTags" placeholder="Tags (comma separated)">
    <button class="btn" onclick="saveMemory()">Save</button>
  </div>
</div>
<div class="grid" id="results"></div>
<div class="stats" id="stats"></div>
<script>
async function search(){
  const q=document.getElementById('query').value;
  const r=await(await fetch('/api/memory/search?q='+encodeURIComponent(q))).json();
  document.getElementById('results').innerHTML=r.results.map(m=>
    '<div class="card"><div class="card-time">'+new Date(m.timestamp*1000).toLocaleString()+'</div>'+
    '<div class="card-title">'+(m.title||'Untitled')+'</div>'+
    '<div class="card-text">'+(m.text||'').substring(0,150)+'</div>'+
    '<div class="card-tags">'+(m.tags||[]).map(t=>'<span class="tag">'+t+'</span>').join('')+'</div></div>'
  ).join('')||'<div style="color:#64748b">No memories found</div>';
  const s=await(await fetch('/api/memory/stats')).json();
  document.getElementById('stats').textContent=s.total_memories+' memories | '+Object.keys(s.types).length+' types';
}
function toggleAdd(){document.getElementById('addForm').classList.toggle('show')}
async function saveMemory(){
  const data={title:document.getElementById('newTitle').value,text:document.getElementById('newText').value,type:document.getElementById('newType').value,tags:document.getElementById('newTags').value.split(',').map(t=>t.trim()).filter(Boolean)};
  await fetch('/api/memory/log',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  document.getElementById('newTitle').value='';document.getElementById('newText').value='';document.getElementById('newTags').value='';
  document.getElementById('addForm').classList.remove('show');search();
}
search();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 11] AI Memory Palace starting on port 5021...")
    app.run(host="0.0.0.0", port=5021, debug=False)
