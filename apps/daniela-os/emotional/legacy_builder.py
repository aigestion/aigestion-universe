import time

from flask import Blueprint, jsonify, request

legacy_bp = Blueprint("legacy_builder", __name__)
_journal = []


@legacy_bp.route("/api/emotional/legacy/status")
def l_status():
    return jsonify({"entries": len(_journal), "recent": _journal[-5:]})


@legacy_bp.route("/api/emotional/legacy/add", methods=["POST"])
def l_add():
    data = request.json or {}
    _journal.append(
        {
            "id": len(_journal) + 1,
            "content": data.get("content", ""),
            "type": data.get("type", "event"),
            "time": time.time(),
        }
    )
    return jsonify({"ok": True})


@legacy_bp.route("/api/emotional/legacy/web")
def l_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Legacy Builder</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.timeline{max-width:600px;margin:0 auto}
.entry{background:#111;border-left:3px solid #ff0066;border-radius:0 12px 12px 0;padding:15px;margin:10px 0}
.entry::before{content:'';position:absolute;left:-9px;top:20px;width:12px;height:12px;border-radius:50%;background:#ff0066}
</style></head><body>
<h1 style="text-align:center">LEGACY BUILDER</h1>
<p style="text-align:center;color:#666">Tu diario de vida automatico</p>
<div class="timeline" id="timeline"></div>
<script>fetch('/api/emotional/legacy/status').then(r=>r.json()).then(d=>{document.getElementById('timeline').innerHTML=d.recent.map(e=>'<div class="entry"><p>'+e.content+'</p><p style="font-size:11px;color:#666">'+new Date(e.time*1000).toLocaleString()+'</p></div>').reverse().join('')||'<p style="text-align:center">No entries yet</p>'})</script>
</body></html>"""
