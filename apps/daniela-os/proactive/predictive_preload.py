from pathlib import Path

from flask import Blueprint, jsonify, request

preload_bp = Blueprint("predictive_preload", __name__)
_data = DATA = Path(__file__).parent.parent / "data"
_preloads = {
    "morning": {"apps": ["gmail", "calendar", "news"], "time": "07:00"},
    "work": {"apps": ["vscode", "browser", "slack"], "time": "09:00"},
    "lunch": {"apps": ["spotify", "maps"], "time": "12:00"},
    "evening": {"apps": ["netflix", "spotify"], "time": "18:00"},
    "night": {"apps": ["kindle", "meditation"], "time": "22:00"},
}


@preload_bp.route("/api/proactive/preload/status")
def pl_status():
    return jsonify({"preloads": _preloads})


@preload_bp.route("/api/proactive/preload/set", methods=["POST"])
def pl_set():
    data = request.json or {}
    period = data.get("period", "morning")
    if period in _preloads:
        _preloads[period]["apps"] = data.get("apps", _preloads[period]["apps"])
    return jsonify({"ok": True})


@preload_bp.route("/api/proactive/preload/web")
def pl_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Predictive Preload</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.period{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;margin:10px 0}
.period h3{margin-top:0;color:#00f0ff}
.app{display:inline-block;background:#00f0ff11;padding:5px 12px;border-radius:20px;margin:3px;font-size:12px}
</style></head><body>
<h1>PREDICTIVE PRELOAD</h1>
<div id="list"></div>
<script>fetch('/api/proactive/preload/status').then(r=>r.json()).then(d=>{document.getElementById('list').innerHTML=Object.entries(d.preloads).map(([k,v])=>'<div class="period"><h3>'+k.toUpperCase()+' ('+v.time+')</h3>'+v.apps.map(a=>'<span class="app">'+a+'</span>').join('')+'</div>').join('')})</script>
</body></html>"""
