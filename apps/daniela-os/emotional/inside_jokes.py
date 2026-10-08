from flask import Blueprint, jsonify, request

inside_jokes_bp = Blueprint("inside_jokes", __name__)
_jokes = [
    {"id": 1, "joke": "Cuando el servidor se cayo y dijimos 'es un feature'", "used": 3},
    {"id": 2, "joke": "El bug que se arreglo solo despues de 3 horas", "used": 1},
]


@inside_jokes_bp.route("/api/emotional/jokes/status")
def j_status():
    return jsonify({"jokes": _jokes})


@inside_jokes_bp.route("/api/emotional/jokes/add", methods=["POST"])
def j_add():
    data = request.json or {}
    _jokes.append({"id": len(_jokes) + 1, "joke": data.get("joke", ""), "used": 0})
    return jsonify({"ok": True})


@inside_jokes_bp.route("/api/emotional/jokes/web")
def j_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Inside Jokes</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.joke{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;margin:10px 0}
.joke h3{margin-top:0;color:#ff8800}
</style></head><body>
<h1>INSIDE JOKES</h1>
<div id="list"></div>
<script>fetch('/api/emotional/jokes/status').then(r=>r.json()).then(d=>{document.getElementById('list').innerHTML=d.jokes.map(j=>'<div class="joke"><h3>🤣 '+j.joke+'</h3><p>Used '+j.used+' times</p></div>').join('')})</script>
</body></html>"""
