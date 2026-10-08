from flask import Blueprint, jsonify, request

suggestions_bp = Blueprint("contextual_suggestions", __name__)
_suggestions = [
    {"context": "photo", "suggestion": "Quieres buscar vuelos a este lugar?", "active": True},
    {"context": "contact", "suggestion": "Quieres llamar a este contacto?", "active": True},
    {"context": "code", "suggestion": "Quieres que ejecute este codigo?", "active": True},
]


@suggestions_bp.route("/api/proactive/suggestions/status")
def sg_status():
    return jsonify({"suggestions": _suggestions})


@suggestions_bp.route("/api/proactive/suggestions/toggle", methods=["POST"])
def sg_toggle():
    data = request.json or {}
    for s in _suggestions:
        if s["context"] == data.get("context"):
            s["active"] = not s["active"]
    return jsonify({"ok": True})


@suggestions_bp.route("/api/proactive/suggestions/web")
def sg_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Contextual Suggestions</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.suggestion{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;margin:10px 0;display:flex;justify-content:space-between;align-items:center}
.suggestion.active{border-color:#00ff88}
.toggle{width:50px;height:26px;border-radius:13px;border:2px solid #333;cursor:pointer;position:relative;transition:all .3s}
.toggle.on{border-color:#00ff88;background:#00ff8833}
.toggle::after{content:'';position:absolute;width:20px;height:20px;border-radius:50%;background:#fff;top:1px;left:1px;transition:all .3s}
.toggle.on::after{left:25px;background:#00ff88}
</style></head><body>
<h1>CONTEXTUAL SUGGESTIONS</h1>
<div id="list"></div>
<script>fetch('/api/proactive/suggestions/status').then(r=>r.json()).then(d=>{document.getElementById('list').innerHTML=d.suggestions.map(s=>'<div class="suggestion '+(s.active?'active':'')+'"><div><h3>'+s.context.toUpperCase()+'</h3><p>'+s.suggestion+'</p></div><div class="toggle '+(s.active?'on':'')+'" onclick="toggle(\\''+s.context+'\\')"></div></div>').join('')});
function toggle(ctx){fetch('/api/proactive/suggestions/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({context:ctx})}).then(()=>location.reload())}</script>
</body></html>"""
