import json
import urllib.request

from flask import Blueprint, jsonify, request

bridge_bp = Blueprint("hermes_daniela_bridge", __name__)
DANIELA_URL = "http://localhost:9200"

@bridge_bp.route("/api/hermes/daniela/status")
def hd_status():
    try:
        req = urllib.request.Request(f"{DANIELA_URL}/api/status", timeout=3)
        resp = urllib.request.urlopen(req, timeout=3)
        data = json.loads(resp.read())
        return jsonify({"connected": True, "daniela": data})
    except Exception:
        return jsonify({"connected": False})

@bridge_bp.route("/api/hermes/daniela/invoke/<path:system>", methods=["POST"])
def hd_invoke(system):
    data = request.json or {}
    try:
        url = f"{DANIELA_URL}/api/{system}"
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"}, timeout=10)
        resp = urllib.request.urlopen(req, timeout=10)
        return jsonify(json.loads(resp.read()))
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@bridge_bp.route("/api/hermes/daniela/systems")
def hd_systems():
    try:
        req = urllib.request.Request(f"{DANIELA_URL}/api/unified/status", timeout=5)
        resp = urllib.request.urlopen(req, timeout=5)
        return jsonify(json.loads(resp.read()))
    except Exception:
        return jsonify({"error": "Daniela offline"})

@bridge_bp.route("/api/hermes/daniela/web")
def hd_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Hermes-Daniela Bridge</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.status{text-align:center;padding:20px}
.connected{color:#00ff88} .disconnected{color:#ff0066}
 systems{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-top:20px}
.sys{background:#111;border:1px solid #333;border-radius:8px;padding:10px;cursor:pointer}
.sys:hover{border-color:#00f0ff}
</style></head><body>
<h1>HERMES <-> DANIELA BRIDGE</h1>
<div class="status" id="status">Checking...</div>
<div class="systems" id="systems"></div>
<script>fetch('/api/hermes/daniela/status').then(r=>r.json()).then(d=>{
document.getElementById('status').innerHTML=d.connected?'<span class="connected">Connected to Daniela</span>':'<span class="disconnected">Daniela Offline</span>';
if(d.connected){fetch('/api/hermes/daniela/systems').then(r=>r.json()).then(s=>{
document.getElementById('systems').innerHTML=(s.systems||[]).map(sys=>'<div class="sys" onclick="window.open(\\''+sys.url+'\\')"><h4>'+sys.name+'</h4><p>:'+sys.port+' '+sys.status+'</p></div>').join('')})}});
</script></body></html>"""
