from flask import Blueprint, jsonify, request

secrets_bp = Blueprint("shared_secrets", __name__)
_secrets = [{"id": 1, "content": "El nombre real del servidor es 'Potato'", "added": "2026-03-15"}]


@secrets_bp.route("/api/emotional/secrets/status")
def s_status():
    return jsonify({"secrets": _secrets, "count": len(_secrets)})


@secrets_bp.route("/api/emotional/secrets/add", methods=["POST"])
def s_add():
    data = request.json or {}
    _secrets.append(
        {
            "id": len(_secrets) + 1,
            "content": data.get("content", ""),
            "added": data.get("added", "2026-01-01"),
        }
    )
    return jsonify({"ok": True})


@secrets_bp.route("/api/emotional/secrets/web")
def s_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Shared Secrets</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:40px}
.secret{background:#111;border:2px dashed #ff0066;border-radius:12px;padding:20px;margin:10px 0;text-align:center}
.secret h3{color:#ff0066}
</style></head><body>
<h1 style="text-align:center">SHARED SECRETS</h1>
<p style="text-align:center;color:#666">Solo tu y yo sabemos esto</p>
<div id="list"></div>
<script>fetch('/api/emotional/secrets/status').then(r=>r.json()).then(d=>{document.getElementById('list').innerHTML=d.secrets.map(s=>'<div class="secret"><h3>SECRET #'+s.id+'</h3><p>'+s.content+'</p><p style="font-size:11px;color:#666">'+s.added+'</p></div>').join('')})</script>
</body></html>"""
