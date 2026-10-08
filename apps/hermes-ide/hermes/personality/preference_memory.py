from flask import Blueprint, jsonify, request

pref_bp = Blueprint("preference_memory", __name__)
_prefs = [{"key": "theme", "value": "dark"}, {"key": "language", "value": "Spanish"}, {"key": "notifications", "value": "minimal"}]

@pref_bp.route("/api/hermes/personality/prefs/status")
def p_status():
    return jsonify({"preferences": _prefs})

@pref_bp.route("/api/hermes/personality/prefs/set", methods=["POST"])
def p_set():
    data = request.json or {}
    for p in _prefs:
        if p["key"] == data.get("key"):
            p["value"] = data.get("value")
            return jsonify({"ok": True})
    _prefs.append({"key": data.get("key"), "value": data.get("value")})
    return jsonify({"ok": True})

@pref_bp.route("/api/hermes/personality/prefs/web")
def p_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Preference Memory</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.pref{background:#111;padding:10px;margin:5px 0;border-radius:6px;display:flex;justify-content:space-between}
</style></head><body><h1>PREFERENCES</h1><div id="prefs"></div>
<script>fetch('/api/hermes/personality/prefs/status').then(r=>r.json()).then(d=>{document.getElementById('prefs').innerHTML=d.preferences.map(p=>'<div class="pref"><span>'+p.key+'</span><span>'+p.value+'</span></div>').join('')})</script></body></html>"""
