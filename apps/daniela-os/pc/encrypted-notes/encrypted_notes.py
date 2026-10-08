"""
System 56: Encrypted Notes
Encrypted note-taking with categories
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


def simple_encrypt(text, key):
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text))


NOTES_KEY = "daniela_notes_2024"


@app.route("/")
def index():
    return NOTES_HTML


@app.route("/api/notes/list")
def list_notes():
    notes = load_json(DATA_DIR / "notes.json", {"notes": []})
    result = []
    for n in notes.get("notes", []):
        try:
            content = simple_encrypt(n.get("content", ""), NOTES_KEY)
        except Exception:
            content = ""
        result.append(
            {
                "id": n.get("id"),
                "title": n.get("title"),
                "content": content,
                "category": n.get("category", "general"),
                "pinned": n.get("pinned", False),
                "created": n.get("created"),
                "updated": n.get("updated"),
            }
        )
    return jsonify({"notes": result})


@app.route("/api/notes/add", methods=["POST"])
def add_note():
    data = request.json or {}
    notes = load_json(DATA_DIR / "notes.json", {"notes": []})
    note = {
        "id": str(int(time.time() * 1000)),
        "title": data.get("title", "Untitled"),
        "content": simple_encrypt(data.get("content", ""), NOTES_KEY),
        "category": data.get("category", "general"),
        "pinned": data.get("pinned", False),
        "created": time.time(),
        "updated": time.time(),
    }
    notes["notes"].append(note)
    save_json(DATA_DIR / "notes.json", notes)
    return jsonify({"ok": True, "id": note["id"]})


@app.route("/api/notes/update", methods=["POST"])
def update_note():
    data = request.json or {}
    notes = load_json(DATA_DIR / "notes.json", {"notes": []})
    for n in notes["notes"]:
        if n.get("id") == data.get("id"):
            n["title"] = data.get("title", n.get("title"))
            n["content"] = simple_encrypt(data.get("content", ""), NOTES_KEY)
            n["category"] = data.get("category", n.get("category"))
            n["pinned"] = data.get("pinned", n.get("pinned"))
            n["updated"] = time.time()
            break
    save_json(DATA_DIR / "notes.json", notes)
    return jsonify({"ok": True})


@app.route("/api/notes/delete", methods=["POST"])
def delete_note():
    data = request.json or {}
    notes = load_json(DATA_DIR / "notes.json", {"notes": []})
    notes["notes"] = [n for n in notes["notes"] if n.get("id") != data.get("id")]
    save_json(DATA_DIR / "notes.json", notes)
    return jsonify({"ok": True})


NOTES_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Encrypted Notes</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-size:11px;font-family:inherit}
.btn-danger{border-color:#ff0055;color:#ff0055;background:rgba(255,0,85,0.1)}
.filter{display:flex;gap:6px;margin-bottom:12px}
.filter-btn{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:6px;padding:4px 10px;cursor:pointer;font-size:10px;color:#64748b}
.filter-btn.active{border-color:#00f0ff;color:#00f0ff}
.notes{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
.note{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;cursor:pointer;transition:all 0.3s}
.note:hover{border-color:#00f0ff}
.note.pinned{border-color:#f59e0b}
.note-title{font-family:'Orbitron',monospace;font-size:12px;color:#00f0ff;margin-bottom:4px}
.note-content{font-size:11px;color:#94a3b8;max-height:60px;overflow:hidden}
.note-meta{display:flex;justify-content:space-between;margin-top:8px;font-size:9px;color:#64748b}
.note-cat{background:rgba(0,240,255,0.08);padding:1px 6px;border-radius:4px;color:#00f0ff}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:100;display:none;align-items:center;justify-content:center}
.modal.show{display:flex}
.modal-content{background:#0a0a1a;border:1px solid rgba(0,240,255,0.2);border-radius:12px;padding:20px;width:500px}
.input{width:100%;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px;margin-bottom:10px}
textarea.input{min-height:200px;resize:vertical;font-family:'Share Tech Mono',monospace}
</style></head><body>
<h1>ENCRYPTED NOTES</h1>
<div class="header"><div style="font-size:12px;color:#64748b" id="count">0 notes</div><button class="btn" onclick="showModal()">New Note</button></div>
<div class="filter">
  <div class="filter-btn active" onclick="filterCat('all',this)">All</div>
  <div class="filter-btn" onclick="filterCat('general',this)">General</div>
  <div class="filter-btn" onclick="filterCat('work',this)">Work</div>
  <div class="filter-btn" onclick="filterCat('personal',this)">Personal</div>
  <div class="filter-btn" onclick="filterCat('ideas',this)">Ideas</div>
</div>
<div class="notes" id="notes"></div>
<div class="modal" id="modal">
  <div class="modal-content">
    <div style="font-family:'Orbitron',monospace;color:#00f0ff;margin-bottom:12px">New Note</div>
    <input class="input" id="title" placeholder="Title">
    <textarea class="input" id="content" placeholder="Content..."></textarea>
    <select class="input" id="category"><option value="general">General</option><option value="work">Work</option><option value="personal">Personal</option><option value="ideas">Ideas</option></select>
    <div style="display:flex;gap:8px"><button class="btn" onclick="saveNote()">Save</button><button class="btn btn-danger" onclick="closeModal()">Cancel</button></div>
  </div>
</div>
<script>
let allNotes=[];let currentFilter='all';
async function load(){
  const r=await(await fetch('/api/notes/list')).json();
  allNotes=r.notes||[];
  document.getElementById('count').textContent=allNotes.length+' notes';
  renderNotes();
}
function renderNotes(){
  let filtered=currentFilter==='all'?allNotes:allNotes.filter(n=>n.category===currentFilter);
  filtered.sort((a,b)=>(b.pinned?1:0)-(a.pinned?1:0));
  document.getElementById('notes').innerHTML=filtered.map(n=>
    '<div class="note'+(n.pinned?' pinned':'')+'" onclick="editNote(\''+n.id+'\')">'+
    '<div class="note-title">'+n.title+'</div>'+
    '<div class="note-content">'+n.content.substring(0,100)+'</div>'+
    '<div class="note-meta"><span class="note-cat">'+n.category+'</span><span>'+new Date(n.updated*1000).toLocaleDateString()+'</span></div></div>'
  ).join('')||'<div style="color:#64748b">No notes</div>';
}
function filterCat(cat,currentFilter=cat;document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));event.target.classList.add('active');renderNotes()}
function showModal(){document.getElementById('modal').classList.add('show')}
function closeModal(){document.getElementById('modal').classList.remove('show')}
async function saveNote(){
  await fetch('/api/notes/add',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({title:document.getElementById('title').value,content:document.getElementById('content').value,category:document.getElementById('category').value})});
  closeModal();load();
}
function editNote(id){const n=allNotes.find(x=>x.id===id);if(n){document.getElementById('title').value=n.title;document.getElementById('content').value=n.content;document.getElementById('category').value=n.category;showModal()}}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 56] Encrypted Notes starting on port 5066...")
    app.run(host="0.0.0.0", port=5066, debug=False)
