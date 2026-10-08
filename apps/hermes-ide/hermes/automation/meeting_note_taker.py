from flask import Blueprint, jsonify, request

note_taker_bp = Blueprint("meeting_note_taker", __name__)
_notes = []

@note_taker_bp.route("/api/hermes/automation/notes/status")
def n_status():
    return jsonify({"notes": _notes[-10:]})

@note_taker_bp.route("/api/hermes/automation/notes/add", methods=["POST"])
def n_add():
    data = request.json or {}
    _notes.append({"meeting": data.get("meeting",""), "notes": data.get("notes",""), "action_items": data.get("action_items",[]), "time": data.get("time","")})
    return jsonify({"ok": True})

@note_taker_bp.route("/api/hermes/automation/notes/web")
def n_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Meeting Note Taker</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.note{background:#111;border:1px solid #333;border-radius:8px;padding:15px;margin:10px 0}
</style></head><body><h1>MEETING NOTE TAKER</h1><div id="notes"></div>
<script>fetch('/api/hermes/automation/notes/status').then(r=>r.json()).then(d=>{document.getElementById('notes').innerHTML=d.notes.length?d.notes.map(n=>'<div class="note"><h3>'+n.meeting+'</h3><p>'+n.notes+'</p><p>Action items: '+(n.action_items||[]).join(', ')+'</p></div>').join(''):'<p>No notes yet</p>'})</script></body></html>"""
