import time

from flask import Blueprint, jsonify, request

journal_bp = Blueprint("emotional_journaling", __name__)
_entries = []


@journal_bp.route("/api/emotional/journal/status")
def j_status():
    return jsonify({"entries": _entries[-10:]})


@journal_bp.route("/api/emotional/journal/add", methods=["POST"])
def j_add():
    data = request.json or {}
    _entries.append(
        {
            "id": len(_entries) + 1,
            "text": data.get("text", ""),
            "mood": data.get("mood", "neutral"),
            "time": time.time(),
        }
    )
    return jsonify({"ok": True})


@journal_bp.route("/api/emotional/journal/web")
def j_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Emotional Journaling</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.journal{max-width:600px;margin:0 auto}
.entry{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:15px;margin:10px 0}
.entry .time{font-size:11px;color:#666}
.add{margin-top:20px}
textarea{width:100%;height:100px;background:#0a0a0f;border:1px solid #333;color:#00f0ff;padding:10px;border-radius:8px;font-family:monospace}
button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:10px 20px;border-radius:6px;cursor:pointer;margin-top:10px}
</style></head><body>
<div class="journal">
<h1>EMOTIONAL JOURNAL</h1>
<div id="entries"></div>
<div class="add">
<textarea id="text" placeholder="How are you feeling?"></textarea>
<button onclick="add()">Add Entry</button>
</div>
</div>
<script>function load(){fetch('/api/emotional/journal/status').then(r=>r.json()).then(d=>{document.getElementById('entries').innerHTML=d.entries.reverse().map(e=>'<div class="entry"><div class="time">'+new Date(e.time*1000).toLocaleString()+'</div><p>'+e.text+'</p><p>Mood: '+e.mood+'</p></div>').join('')})}
function add(){fetch('/api/emotional/journal/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:document.getElementById('text').value,mood:'neutral'})}).then(()=>{document.getElementById('text').value='';load()})}
load()</script>
</body></html>"""
