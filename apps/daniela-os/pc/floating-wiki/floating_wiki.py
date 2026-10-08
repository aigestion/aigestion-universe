"""
System 23: Floating Wiki
Contextual wiki that appears based on what you're working on
"""

import json
import time
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
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
    return WIKI_HTML


@app.route("/api/wiki/articles")
def list_articles():
    return jsonify(load_json(DATA_DIR / "wiki.json", {"articles": []}))


@app.route("/api/wiki/add", methods=["POST"])
def add_article():
    data = request.json or {}
    articles = load_json(DATA_DIR / "wiki.json", {"articles": []})
    article = {
        "id": int(time.time()),
        "title": data.get("title", ""),
        "content": data.get("content", ""),
        "tags": data.get("tags", []),
        "created": time.time(),
        "updated": time.time(),
    }
    articles["articles"].append(article)
    save_json(DATA_DIR / "wiki.json", articles)
    return jsonify({"ok": True})


@app.route("/api/wiki/search")
def search():
    q = request.args.get("q", "").lower()
    articles = load_json(DATA_DIR / "wiki.json", {"articles": []}).get("articles", [])
    results = []
    for a in articles:
        score = 0
        if q in a.get("title", "").lower():
            score += 3
        if q in a.get("content", "").lower():
            score += 1
        for tag in a.get("tags", []):
            if q in tag.lower():
                score += 2
        if score > 0 or not q:
            a["relevance"] = score
            results.append(a)
    results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    return jsonify({"results": results[:20]})


@app.route("/api/wiki/update", methods=["POST"])
def update_article():
    data = request.json or {}
    articles = load_json(DATA_DIR / "wiki.json", {"articles": []})
    for a in articles["articles"]:
        if a["id"] == data.get("id"):
            a["content"] = data.get("content", a["content"])
            a["updated"] = time.time()
            break
    save_json(DATA_DIR / "wiki.json", articles)
    return jsonify({"ok": True})


@app.route("/api/wiki/delete", methods=["POST"])
def delete_article():
    data = request.json or {}
    articles = load_json(DATA_DIR / "wiki.json", {"articles": []})
    articles["articles"] = [a for a in articles["articles"] if a["id"] != data.get("id")]
    save_json(DATA_DIR / "wiki.json", articles)
    return jsonify({"ok": True})


WIKI_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Floating Wiki</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:16px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px}
.btn:hover{background:rgba(0,240,255,0.2)}
.search{width:100%;background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.2);color:#e2e8f0;padding:10px 16px;border-radius:8px;font-size:14px;font-family:inherit;margin-bottom:12px}
.search:focus{outline:none;border-color:#00f0ff}
.grid{display:grid;grid-template-columns:250px 1fr;gap:16px;height:calc(100vh - 180px)}
.sidebar{overflow-y:auto}
.sidebar-item{padding:8px 12px;border-radius:6px;cursor:pointer;font-size:12px;margin-bottom:4px;transition:all 0.2s}
.sidebar-item:hover,.sidebar-item.active{background:rgba(0,240,255,0.1);color:#00f0ff}
.editor{display:flex;flex-direction:column;gap:8px}
.editor input,.editor textarea{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:10px;border-radius:6px;font-family:inherit;font-size:13px}
.editor textarea{flex:1;min-height:300px;resize:vertical;font-family:'Share Tech Mono',monospace;line-height:1.6}
.editor input:focus,.editor textarea:focus{outline:none;border-color:#00f0ff}
.preview{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:16px;line-height:1.8;font-size:13px;overflow-y:auto}
.tag{display:inline-block;background:rgba(0,240,255,0.08);color:#00f0ff;padding:2px 8px;border-radius:4px;font-size:9px;margin:2px}
</style></head><body>
<h1>FLOATING WIKI</h1>
<input class="search" id="search" placeholder="Search your knowledge base..." onkeyup="searchWiki()">
<div class="grid">
  <div class="sidebar" id="sidebar"></div>
  <div class="editor">
    <input id="title" placeholder="Article title">
    <input id="tags" placeholder="Tags (comma separated)">
    <textarea id="content" placeholder="Write your article in Markdown..."></textarea>
    <div style="display:flex;gap:8px">
      <button class="btn" onclick="saveArticle()">Save</button>
      <button class="btn" onclick="newArticle()">New</button>
      <button class="btn" style="border-color:#ff0055;color:#ff0055" onclick="deleteArticle()">Delete</button>
    </div>
  </div>
</div>
<script>
let currentId=null;let articles=[];
async function load(){
  const r=await(await fetch('/api/wiki/articles')).json();
  articles=r.articles||[];
  renderSidebar(articles);
}
function renderSidebar(list){
  document.getElementById('sidebar').innerHTML=list.map(a=>
    '<div class="sidebar-item'+(currentId===a.id?' active':'')+'" onclick="openArticle('+a.id+')">'+a.title+'</div>'
  ).join('')||'<div style="color:#64748b;padding:8px">No articles yet</div>';
}
async function openArticle(id){
  const a=articles.find(x=>x.id===id);if(!a)return;
  currentId=id;
  document.getElementById('title').value=a.title;
  document.getElementById('tags').value=(a.tags||[]).join(', ');
  document.getElementById('content').value=a.content;
  renderSidebar(articles);
}
function newArticle(){currentId=null;document.getElementById('title').value='';document.getElementById('tags').value='';document.getElementById('content').value=''}
async function saveArticle(){
  const data={title:document.getElementById('title').value,content:document.getElementById('content').value,tags:document.getElementById('tags').value.split(',').map(s=>s.trim())};
  if(currentId){data.id=currentId;await fetch('/api/wiki/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})}
  else{await fetch('/api/wiki/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})}
  load();
}
async function deleteArticle(){
  if(!currentId)return;await fetch('/api/wiki/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:currentId})});
  newArticle();load();
}
async function searchWiki(){
  const q=document.getElementById('search').value;
  const r=await(await fetch('/api/wiki/search?q='+encodeURIComponent(q))).json();
  renderSidebar(r.results||[]);
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 23] Floating Wiki starting on port 5033...")
    app.run(host="0.0.0.0", port=5033, debug=False)
