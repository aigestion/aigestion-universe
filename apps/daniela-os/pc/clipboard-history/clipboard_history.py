"""
System 31: Smart Clipboard History
Infinite clipboard history with search, categories, and quick paste
"""

import hashlib
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
    return CLIP_HTML


@app.route("/api/clip/add", methods=["POST"])
def add_clip():
    data = request.json or {}
    clips = load_json(DATA_DIR / "clips.json", {"items": []})
    text = data.get("text", "")
    if not text:
        return jsonify({"ok": False})
    for existing in clips["items"][-50:]:
        if existing.get("text") == text:
            existing["last_used"] = time.time()
            existing["count"] = existing.get("count", 0) + 1
            save_json(DATA_DIR / "clips.json", clips)
            return jsonify({"ok": True, "duplicate": True})
    clip = {
        "id": hashlib.md5(f"{time.time()}{text}".encode()).hexdigest()[:8],
        "text": text,
        "preview": text[:100],
        "type": "code"
        if any(c in text for c in ["def ", "class ", "import ", "{", "}", ";"])
        else "text",
        "length": len(text),
        "timestamp": time.time(),
        "last_used": time.time(),
        "count": 1,
        "pinned": False,
    }
    clips["items"].append(clip)
    clips["items"] = clips["items"][-500:]
    save_json(DATA_DIR / "clips.json", clips)
    return jsonify({"ok": True})


@app.route("/api/clip/list")
def list_clips():
    clips = load_json(DATA_DIR / "clips.json", {"items": []})
    q = request.args.get("q", "").lower()
    items = clips.get("items", [])
    if q:
        items = [c for c in items if q in c.get("text", "").lower()]
    items.sort(key=lambda x: x.get("pinned", False) and 1 or 0, reverse=True)
    items.sort(key=lambda x: x.get("last_used", 0), reverse=True)
    return jsonify({"items": items[:100]})


@app.route("/api/clip/pin", methods=["POST"])
def pin_clip():
    data = request.json or {}
    clips = load_json(DATA_DIR / "clips.json", {"items": []})
    for c in clips["items"]:
        if c["id"] == data.get("id"):
            c["pinned"] = not c.get("pinned", False)
            break
    save_json(DATA_DIR / "clips.json", clips)
    return jsonify({"ok": True})


@app.route("/api/clip/delete", methods=["POST"])
def delete_clip():
    data = request.json or {}
    clips = load_json(DATA_DIR / "clips.json", {"items": []})
    clips["items"] = [c for c in clips["items"] if c["id"] != data.get("id")]
    save_json(DATA_DIR / "clips.json", clips)
    return jsonify({"ok": True})


@app.route("/api/clip/clear", methods=["POST"])
def clear_clips():
    save_json(DATA_DIR / "clips.json", {"items": []})
    return jsonify({"ok": True})


CLIP_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Smart Clipboard History</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:16px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px}
.btn:hover{background:rgba(0,240,255,0.2)}
.btn.red{border-color:#ff0055;color:#ff0055}
.search{width:100%;background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.2);color:#e2e8f0;padding:10px 16px;border-radius:8px;font-size:14px;font-family:inherit;margin-bottom:12px}
.search:focus{outline:none;border-color:#00f0ff}
.clip-list{display:flex;flex-direction:column;gap:8px}
.clip-item{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:8px;padding:12px;cursor:pointer;transition:all 0.2s}
.clip-item:hover{border-color:#00f0ff;background:rgba(0,240,255,0.05)}
.clip-item.pinned{border-color:#f59e0b;background:rgba(245,158,11,0.05)}
.clip-text{font-family:'Share Tech Mono',monospace;font-size:11px;color:#e2e8f0;white-space:pre-wrap;word-break:break-all;max-height:60px;overflow:hidden}
.clip-meta{display:flex;justify-content:space-between;margin-top:6px;font-size:9px;color:#64748b}
.clip-type{background:rgba(0,240,255,0.08);color:#00f0ff;padding:1px 6px;border-radius:3px}
.clip-type.code{background:rgba(139,92,246,0.15);color:#8b5cf6}
.controls{display:flex;gap:8px;margin-bottom:12px}
</style></head><body>
<h1>SMART CLIPBOARD HISTORY</h1>
<div class="controls">
  <button class="btn" onclick="addManual()">+ Add Text</button>
  <button class="btn red" onclick="clearAll()">Clear All</button>
</div>
<input class="search" id="search" placeholder="Search clipboard history..." onkeyup="load()">
<div class="clip-list" id="clips"></div>
<script>
async function load(){
  const q=document.getElementById('search').value;
  const r=await(await fetch('/api/clip/list?q='+encodeURIComponent(q))).json();
  document.getElementById('clips').innerHTML=(r.items||[]).map(c=>
    '<div class="clip-item'+(c.pinned?' pinned':'')+'" onclick="copyClip(\''+c.text.replace(/'/g,"\\'").replace(/\n/g,"\\n")+'\')">'+
    '<div class="clip-text">'+c.text.substring(0,200).replace(/</g,'&lt;')+'</div>'+
    '<div class="clip-meta"><span><span class="clip-type '+c.type+'">'+c.type+'</span> '+c.length+' chars | Used '+c.count+'x</span>'+
    '<span><button class="btn" onclick="event.stopPropagation();pin(\''+c.id+'\')">'+(c.pinned?'Unpin':'Pin')+'</button> '+
    '<button class="btn red" onclick="event.stopPropagation();del(\''+c.id+'\')">X</button></span></div></div>'
  ).join('')||'<div style="color:#64748b">No clipboard history</div>';
}
async function copyClip(text){await navigator.clipboard.writeText(text)}
async function addManual(){const t=prompt('Enter text to add:');if(t){await fetch('/api/clip/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});load()}}
async function pin(id){await fetch('/api/clip/pin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
async function del(id){await fetch('/api/clip/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
async function clearAll(){if(confirm('Clear all?')){await fetch('/api/clip/clear',{method:'POST'});load()}}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 31] Smart Clipboard History starting on port 5041...")
    app.run(host="0.0.0.0", port=5041, debug=False)
