import time

from flask import Blueprint, jsonify

consolidation_bp = Blueprint("memory_consolidation", __name__)
_state = {"last_consolidation": time.time(), "memories_consolidated": 15, "memories_forgotten": 3, "strength_avg": 0.72}

@consolidation_bp.route("/api/hermes/memory/consolidation/status")
def mc_status():
    return jsonify(_state)

@consolidation_bp.route("/api/hermes/memory/consolidation/run", methods=["POST"])
def mc_run():
    _state["last_consolidation"] = time.time()
    _state["memories_consolidated"] += 5
    return jsonify({"ok": True})

@consolidation_bp.route("/api/hermes/memory/consolidation/web")
def mc_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Memory Consolidation</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.consolidate{text-align:center}
.brain{font-size:80px;margin:20px 0}
button{padding:15px 30px;background:#00f0ff22;border:2px solid #00f0ff;color:#00f0ff;border-radius:10px;cursor:pointer;font-size:16px}
</style></head><body>
<div class="consolidate"><h2>MEMORY CONSOLIDATION</h2><div class="brain">🧠</div>
<p>Consolidated: <span id="cons">15</span></p>
<p>Forgotten: <span id="for">3</span></p>
<button onclick="run()">Run Consolidation</button></div>
<script>function run(){fetch('/api/hermes/memory/consolidation/run',{method:'POST'}).then(r=>r.json()).then(d=>{document.getElementById('cons').textContent=parseInt(document.getElementById('cons').textContent)+5})}</script></body></html>"""
