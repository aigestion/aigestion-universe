"""
System 45: Meme Generator
Create memes from screenshots and templates
"""

import json
import time
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR = Path.home() / "Pictures" / "Screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


MEME_TEMPLATES = [
    {"id": "drake", "name": "Drake Hotline Bling", "category": "reaction"},
    {"id": "distracted", "name": "Distracted Boyfriend", "category": "reaction"},
    {"id": "change", "name": "Change My Mind", "category": "debate"},
    {"id": "brain", "name": "Expanding Brain", "category": "idea"},
    {"id": "woman_cat", "name": "Woman Yelling at Cat", "category": "reaction"},
    {"id": "this_is", "name": "This Is Fine", "category": "situation"},
    {"id": "uno", "name": "UNO Reverse Card", "category": "reaction"},
    {"id": "stonks", "name": "Stonks", "category": "finance"},
    {"id": "gigachad", "name": "Gigachad", "category": "reaction"},
    {"id": "sadge", "name": "Pepe Sadge", "category": "reaction"},
]


@app.route("/")
def index():
    return MEME_HTML


@app.route("/api/memes/templates")
def templates():
    return jsonify({"templates": MEME_TEMPLATES})


@app.route("/api/memes/recent")
def recent():
    files = []
    if SCREENSHOTS_DIR.exists():
        for f in sorted(SCREENSHOTS_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)[
            :20
        ]:
            files.append({"name": f.name, "path": str(f), "time": f.stat().st_mtime})
    return jsonify({"screenshots": files})


@app.route("/api/memes/save", methods=["POST"])
def save_meme():
    data = request.json or {}
    memes = load_json(DATA_DIR / "memes.json", {"saved": []})
    memes["saved"].append(
        {
            "name": data.get("name", "untitled"),
            "template": data.get("template", ""),
            "top": data.get("top", ""),
            "bottom": data.get("bottom", ""),
            "time": time.time(),
        }
    )
    save_json(DATA_DIR / "memes.json", memes)
    return jsonify({"ok": True})


MEME_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Meme Generator</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.templates{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;margin-bottom:20px}
.template{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;cursor:pointer;transition:all 0.3s;text-align:center}
.template:hover{border-color:#00f0ff}
.template.selected{border-color:#ff0055;box-shadow:0 0 15px rgba(255,0,85,0.2)}
.tmpl-name{font-size:11px;color:#00f0ff;margin-top:6px}
.tmpl-cat{font-size:9px;color:#64748b}
.editor{background:rgba(3,8,20,0.8);border:1px solid rgba(255,0,85,0.2);border-radius:12px;padding:16px;margin-bottom:20px}
.editor-row{display:flex;gap:10px;margin-bottom:10px}
.input{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px;flex:1}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px}
.btn-danger{border-color:#ff0055;color:#ff0055;background:rgba(255,0,85,0.1)}
.screenshots{display:flex;gap:8px;flex-wrap:wrap}
.screenshot{width:120px;height:80px;background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:6px;cursor:pointer;overflow:hidden;position:relative}
.screenshot img{width:100%;height:100%;object-fit:cover}
.screenshot.selected{border-color:#ff0055}
.screenshot-name{position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,0.7);font-size:8px;padding:2px 4px;color:#94a3b8}
.preview{background:#000;border:2px solid #00f0ff;border-radius:10px;padding:20px;text-align:center;margin-top:16px;font-family:'Impact',sans-serif;font-size:24px;color:#fff;text-shadow:3px 3px 0 #000,-3px -3px 0 #000,3px -3px 0 #000,-3px 3px 0 #000;min-height:120px;display:flex;flex-direction:column;justify-content:space-between}
</style></head><body>
<h1>MEME GENERATOR</h1>
<div class="templates" id="templates"></div>
<div class="editor">
  <div class="editor-row">
    <input class="input" id="topText" placeholder="Top text">
    <input class="input" id="bottomText" placeholder="Bottom text">
  </div>
  <div class="editor-row">
    <button class="btn" onclick="saveMeme()">Save Meme</button>
    <button class="btn btn-danger" onclick="clear()">Clear</button>
  </div>
  <div class="preview" id="preview"><div id="prevTop">TOP TEXT</div><div id="prevBottom">BOTTOM TEXT</div></div>
</div>
<div style="margin-top:16px;font-size:12px;color:#64748b;font-family:'Orbitron',monospace;letter-spacing:1px">SCREENSHOTS</div>
<div class="screenshots" id="shots" style="margin-top:8px"></div>
<script>
let selected=null,selectedShot=null;
async function load(){
  const t=await(await fetch('/api/memes/templates')).json();
  const s=await(await fetch('/api/memes/recent')).json();
  document.getElementById('templates').innerHTML=(t.templates||[]).map(tmpl=>
    '<div class="template" onclick="selectTemplate(this,\''+tmpl.id+'\')"><div style="font-size:36px">127918</div><div class="tmpl-name">'+tmpl.name+'</div><div class="tmpl-cat">'+tmpl.category+'</div></div>'
  ).join('');
  document.getElementById('shots').innerHTML=(s.screenshots||[]).map(sh=>
    '<div class="screenshot" onclick="selectShot(this)"><div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:24px">128248</div><div class="screenshot-name">'+sh.name+'</div></div>'
  ).join('');
}
function selectTemplate(el,id){document.querySelectorAll('.template').forEach(t=>t.classList.remove('selected'));el.classList.add('selected');selected=id}
function selectShot(el){document.querySelectorAll('.screenshot').forEach(s=>s.classList.remove('selected'));el.classList.add('selected');selectedShot=true}
document.getElementById('topText').oninput=function(){document.getElementById('prevTop').textContent=this.value||'TOP TEXT'};
document.getElementById('bottomText').oninput=function(){document.getElementById('prevBottom').textContent=this.value||'BOTTOM TEXT'};
async function saveMeme(){await fetch('/api/memes/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'meme_'+Date.now(),template:selected,top:document.getElementById('topText').value,bottom:document.getElementById('bottomText').value})});alert('Meme saved!')}
function clear(){selected=null;selectedShot=null;document.getElementById('topText').value='';document.getElementById('bottomText').value='';document.getElementById('prevTop').textContent='TOP TEXT';document.getElementById('prevBottom').textContent='BOTTOM TEXT';document.querySelectorAll('.template,.screenshot').forEach(e=>e.classList.remove('selected'))}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 45] Meme Generator starting on port 5055...")
    app.run(host="0.0.0.0", port=5055, debug=False)
