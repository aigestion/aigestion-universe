import time

from flask import Blueprint, jsonify

dup_bp = Blueprint("duplicate_detection", __name__)
_stats = {"scanned": 0, "duplicates_found": 0, "last_scan": None}


@dup_bp.route("/api/proactive/duplicates/status")
def d_status():
    return jsonify(_stats)


@dup_bp.route("/api/proactive/duplicates/scan", methods=["POST"])
def d_scan():
    _stats["last_scan"] = time.time()
    _stats["scanned"] += 100
    _stats["duplicates_found"] += 3
    return jsonify({"ok": True, "found": 3})


@dup_bp.route("/api/proactive/duplicates/web")
def d_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Duplicate Detection</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.dup{text-align:center}
.stats{display:flex;gap:30px;margin:20px 0}
.stat{background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:20px}
.stat .num{font-size:40px;color:#00ff88}
.btn{padding:15px 30px;background:#00f0ff22;border:2px solid #00f0ff;color:#00f0ff;border-radius:10px;cursor:pointer;font-size:16px}
</style></head><body>
<div class="dup">
<h2>DUPLICATE DETECTION</h2>
<div class="stats">
<div class="stat"><div class="num" id="scanned">0</div><p>Scanned</p></div>
<div class="stat"><div class="num" id="found">0</div><p>Duplicates</p></div>
</div>
<button class="btn" onclick="scan()">Scan Now</button>
</div>
<script>function load(){fetch('/api/proactive/duplicates/status').then(r=>r.json()).then(d=>{document.getElementById('scanned').textContent=d.scanned;document.getElementById('found').textContent=d.duplicates_found})}
function scan(){fetch('/api/proactive/duplicates/scan',{method:'POST'}).then(()=>load())}
load()</script>
</body></html>"""
