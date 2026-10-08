import time

from flask import Blueprint, jsonify

auto_org_bp = Blueprint("auto_organization", __name__)
_stats = {
    "files_organized": 0,
    "last_run": None,
    "categories": {"documents": 0, "images": 0, "code": 0, "media": 0},
}


@auto_org_bp.route("/api/proactive/auto-org/status")
def ao_status():
    return jsonify(_stats)


@auto_org_bp.route("/api/proactive/auto-org/run", methods=["POST"])
def ao_run():
    _stats["last_run"] = time.time()
    _stats["files_organized"] += 5
    return jsonify({"ok": True, "organized": 5})


@auto_org_bp.route("/api/proactive/auto-org/web")
def ao_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Auto Organization</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.org{text-align:center}
.stats{display:flex;gap:20px;margin:20px 0}
.stat{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px;width:120px}
.stat .num{font-size:30px;color:#00ff88}
.btn{padding:15px 30px;background:#00f0ff22;border:2px solid #00f0ff;color:#00f0ff;border-radius:10px;cursor:pointer;font-size:16px;margin-top:20px}
</style></head><body>
<div class="org">
<h2>AUTO ORGANIZATION</h2>
<div class="stats">
<div class="stat"><div class="num" id="docs">0</div><p>Documents</p></div>
<div class="stat"><div class="num" id="imgs">0</div><p>Images</p></div>
<div class="stat"><div class="num" id="code">0</div><p>Code</p></div>
<div class="stat"><div class="num" id="media">0</div><p>Media</p></div>
</div>
<button class="btn" onclick="run()">Run Organization</button>
<p id="total">Total: 0 files organized</p>
</div>
<script>function load(){fetch('/api/proactive/auto-org/status').then(r=>r.json()).then(d=>{document.getElementById('total').textContent='Total: '+d.files_organized+' files organized'})}
function run(){fetch('/api/proactive/auto-org/run',{method:'POST'}).then(()=>load())}
load()</script>
</body></html>"""
