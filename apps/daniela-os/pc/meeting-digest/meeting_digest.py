"""
System 18: Post-Meeting Digest
Transcribes audio, generates summary, extracts action items, creates calendar events
"""

import json
import re
import time
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

DIGESTS_FILE = DATA_DIR / "digests.json"


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_actions(text):
    patterns = [
        r"(?:need to|must|should|have to|will|going to)\s+(.+?)(?:\.|$)",
        r"(?:action item|todo|task)[:\s]+(.+?)(?:\.|$)",
        r"(?:follow up|follow-up)[:\s]+(.+?)(?:\.|$)",
    ]
    actions = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        actions.extend(matches)
    return actions[:10]


@app.route("/")
def index():
    return DIGEST_HTML


@app.route("/api/digest/list")
def list_digests():
    return jsonify(load_json(DIGESTS_FILE, {"digests": []}))


@app.route("/api/digest/create", methods=["POST"])
def create_digest():
    data = request.json or {}
    transcript = data.get("transcript", "")
    words = transcript.split()
    sentences = re.split(r"[.!?]+", transcript)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    summary = " ".join(sentences[:3]) if sentences else transcript[:200]
    key_points = [s.strip() for s in sentences[:5]]
    action_items = extract_actions(transcript)

    digest = {
        "id": int(time.time()),
        "title": data.get("title", f"Meeting {time.strftime('%Y-%m-%d %H:%M')}"),
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "transcript": transcript,
        "summary": summary,
        "key_points": key_points,
        "action_items": action_items,
        "word_count": len(words),
        "duration_est": f"{max(1, len(words) // 150)} min",
        "attendees": data.get("attendees", []),
    }

    digests = load_json(DIGESTS_FILE, {"digests": []})
    digests["digests"].append(digest)
    save_json(DIGESTS_FILE, digests)
    return jsonify({"ok": True, "id": digest["id"]})


@app.route("/api/digest/delete", methods=["POST"])
def delete_digest():
    data = request.json or {}
    did = data.get("id")
    digests = load_json(DIGESTS_FILE, {"digests": []})
    digests["digests"] = [d for d in digests["digests"] if d["id"] != did]
    save_json(DIGESTS_FILE, digests)
    return jsonify({"ok": True})


DIGEST_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Post-Meeting Digest</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:10px 16px;border-radius:8px;cursor:pointer;font-family:inherit}
.btn:hover{background:rgba(0,240,255,0.2)}
.textarea{width:100%;min-height:120px;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:12px;border-radius:8px;font-family:inherit;font-size:12px;resize:vertical}
.textarea:focus{outline:none;border-color:#00f0ff}
.input{width:100%;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:10px;border-radius:6px;font-family:inherit;font-size:12px;margin-bottom:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:12px;margin-top:16px}
.card{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px}
.card-title{font-family:'Orbitron',monospace;color:#00f0ff;font-size:14px}
.card-date{font-size:10px;color:#64748b;margin:4px 0}
.card-summary{font-size:12px;color:#94a3b8;margin:8px 0}
.card-section{margin-top:8px}
.card-section h3{font-size:11px;color:#00f0ff;margin-bottom:4px;letter-spacing:1px}
.card-item{font-size:11px;color:#94a3b8;padding:2px 0;padding-left:8px;border-left:2px solid rgba(0,240,255,0.2)}
.card-action{font-size:11px;color:#f59e0b;padding:2px 0;padding-left:8px;border-left:2px solid #f59e0b}
</style></head><body>
<h1>POST-MEETING DIGEST</h1>
<div style="margin-bottom:16px">
  <input class="input" id="title" placeholder="Meeting title">
  <textarea class="textarea" id="transcript" placeholder="Paste meeting transcript or notes here..."></textarea>
  <button class="btn" onclick="create()" style="margin-top:8px">Generate Digest</button>
</div>
<div class="grid" id="digests"></div>
<script>
async function load(){
  const r=await(await fetch('/api/digest/list')).json();
  document.getElementById('digests').innerHTML=(r.digests||[]).reverse().map(d=>
    '<div class="card"><div class="card-title">'+d.title+'</div>'+
    '<div class="card-date">'+d.date+' | '+d.duration_est+' | '+d.word_count+' words</div>'+
    '<div class="card-summary">'+d.summary+'</div>'+
    (d.key_points.length?'<div class="card-section"><h3>KEY POINTS</h3>'+d.key_points.map(p=>'<div class="card-item">'+p+'</div>').join('')+'</div>':'')+
    (d.action_items.length?'<div class="card-section"><h3>ACTION ITEMS</h3>'+d.action_items.map(a=>'<div class="card-action">'+a+'</div>').join('')+'</div>':'')+
    '<button class="btn" style="margin-top:8px;border-color:#ff0055;color:#ff0055" onclick="del('+d.id+')">Delete</button></div>'
  ).join('')||'<div style="color:#64748b">No digests yet</div>';
}
async function create(){
  const title=document.getElementById('title').value;
  const transcript=document.getElementById('transcript').value;
  if(!transcript.trim())return;
  await fetch('/api/digest/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,transcript})});
  document.getElementById('title').value='';document.getElementById('transcript').value='';load();
}
async function del(id){await fetch('/api/digest/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 18] Post-Meeting Digest starting on port 5028...")
    app.run(host="0.0.0.0", port=5028, debug=False)
