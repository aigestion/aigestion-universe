# -*- coding: utf-8 -*-
"""
Idea 4: Clipboard Enhanced
Universal clipboard with history, search, categories, and pinning.
"""

import os
import json
import time
import hashlib
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent.parent / "data" / "clipboard"
DATA_DIR.mkdir(parents=True, exist_ok=True)

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
    return CLIP_HTML

@app.route("/api/pixel/clipboard/history")
def history():
    clips = load_json(DATA_DIR / "clips.json", {"clips": []})
    query = request.args.get("q", "").lower()
    category = request.args.get("category", "")
    result = clips.get("clips", [])
    if query: result = [c for c in result if query in c.get("text", "").lower()]
    if category: result = [c for c in result if c.get("category") == category]
    return jsonify({"clips": result[-50:], "total": len(clips.get("clips", []))})

@app.route("/api/pixel/clipboard/add", methods=["POST"])
def add_clip():
    data = request.json or {}
    text = data.get("text", "")
    if not text: return jsonify({"ok": False})
    clips = load_json(DATA_DIR / "clips.json", {"clips": []})
    clip_hash = hashlib.md5(text.encode()).hexdigest()
    for c in clips["clips"]:
        if c.get("hash") == clip_hash:
            c["count"] = c.get("count", 1) + 1
            c["last_used"] = time.time()
            save_json(DATA_DIR / "clips.json", clips)
            return jsonify({"ok": True, "id": c["id"]})
    clip = {"id": clip_hash[:8], "text": text, "hash": clip_hash, "category": data.get("category", "general"),
            "pinned": False, "created": time.time(), "last_used": time.time(), "count": 1}
    clips["clips"].append(clip)
    if len(clips["clips"]) > 500: clips["clips"] = clips["clips"][-500:]
    save_json(DATA_DIR / "clips.json", clips)
    return jsonify({"ok": True, "id": clip["id"]})

@app.route("/api/pixel/clipboard/pin", methods=["POST"])
def pin_clip():
    data = request.json or {}
    clips = load_json(DATA_DIR / "clips.json", {"clips": []})
    for c in clips["clips"]:
        if c.get("id") == data.get("id"):
            c["pinned"] = not c.get("pinned", False)
            break
    save_json(DATA_DIR / "clips.json", clips)
    return jsonify({"ok": True})

@app.route("/api/pixel/clipboard/delete", methods=["POST"])
def delete_clip():
    data = request.json or {}
    clips = load_json(DATA_DIR / "clips.json", {"clips": []})
    clips["clips"] = [c for c in clips["clips"] if c.get("id") != data.get("id")]
    save_json(DATA_DIR / "clips.json", clips)
    return jsonify({"ok": True})

CLIP_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Clipboard Enhanced</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:16px}
.search{display:flex;gap:8px;margin-bottom:12px}
.input{flex:1;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-size:12px}
.filter{display:flex;gap:6px;margin-bottom:12px}
.filter-btn{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:6px;padding:4px 10px;cursor:pointer;font-size:10px;color:#64748b}
.filter-btn.active{border-color:#00f0ff;color:#00f0ff}
.clips{display:grid;gap:6px}
.clip{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:8px;padding:10px;display:flex;justify-content:space-between;align-items:center;transition:all 0.2s}
.clip:hover{border-color:#00f0ff}
.clip.pinned{border-color:#f59e0b}
.clip-text{font-size:11px;flex:1;font-family:'Share Tech Mono',monospace;max-height:40px;overflow:hidden}
.clip-meta{font-size:9px;color:#64748b;margin-left:12px;white-space:nowrap}
.clip-actions{display:flex;gap:4px;margin-left:8px}
.btn-sm{background:rgba(0,240,255,0.08);border:1px solid var(--border);padding:4px 8px;border-radius:4px;cursor:pointer;font-size:9px;color:#64748b}
.btn-sm:hover{border-color:#00f0ff;color:#00f0ff}
.stats{font-size:11px;color:#64748b;margin-bottom:12px}
</style></head><body>
<h1>CLIPBOARD ENHANCED</h1>
<div class="search"><input class="input" id="search" placeholder="Search clips..." oninput="loadClips()"></div>
<div class="filter">
  <div class="filter-btn active" onclick="setFilter('')">All</div>
  <div class="filter-btn" onclick="setFilter('text')">Text</div>
  <div class="filter-btn" onclick="setFilter('url')">URLs</div>
  <div class="filter-btn" onclick="setFilter('code')">Code</div>
  <div class="filter-btn" onclick="setFilter('pinned')">Pinned</div>
</div>
<div class="stats" id="stats">0 clips</div>
<div class="clips" id="clips"></div>
<script>
let currentFilter='';
function setFilter(f){currentFilter=f;document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));event.target.classList.add('active');loadClips()}
async function loadClips(){const q=document.getElementById('search').value;const r=await(await fetch('/api/pixel/clipboard/history?q='+encodeURIComponent(q)+'&category='+currentFilter)).json();document.getElementById('stats').textContent=r.total+' clips total, showing '+r.clips.length;document.getElementById('clips').innerHTML=(r.clips||[]).map(c=>'<div class="clip'+(c.pinned?' pinned':'')+'"><div class="clip-text">'+c.text.substring(0,100)+'</div><div class="clip-meta">'+c.count+'x</div><div class="clip-actions"><button class="btn-sm" onclick="copyClip(\''+btoa(c.text)+'\')">Copy</button><button class="btn-sm" onclick="pinClip(\''+c.id+'\')">Pin</button><button class="btn-sm" onclick="delClip(\''+c.id+'\')">Del</button></div></div>').join('')||'<div style="color:#64748b;font-size:11px">No clips</div>'}
function copyClip(b64){navigator.clipboard.writeText(atob(b64))}
async function pinClip(id){await fetch('/api/pixel/clipboard/pin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});loadClips()}
async function delClip(id){await fetch('/api/pixel/clipboard/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});loadClips()}
loadClips();
</script></body></html>
"""

if __name__ == "__main__":
    print("[Idea 4] Clipboard Enhanced starting on port 9103...")
    app.run(host="0.0.0.0", port=9103, debug=False)