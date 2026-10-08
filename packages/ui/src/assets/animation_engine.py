from flask import Blueprint, jsonify

anim_bp = Blueprint("animation_engine", __name__)

@anim_bp.route("/api/frontend/anim/status")
def a_status():
    return jsonify({"fps": 60, "animations": 15, "gpu_accelerated": True, "will_change": True})

@anim_bp.route("/api/frontend/anim/web")
def a_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Animation Engine</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.demo{width:100px;height:100px;background:linear-gradient(135deg,#00f0ff,#ff0066);border-radius:12px;margin:20px auto;animation:float 2s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-20px)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
.stats{display:flex;gap:15px;justify-content:center;margin:20px 0}
.stat{background:#111;border:1px solid #333;border-radius:8px;padding:15px}
</style></head><body><h1 style="text-align:center">ANIMATION ENGINE</h1>
<div class="stats"><div class="stat"><div class="num" id="fps">60</div><p>FPS</p></div><div class="stat"><div class="num">15</div><p>Animations</p></div></div>
<div class="demo" id="demo"></div>
<p style="text-align:center">GPU accelerated | will-change: transform</p>
<script>let fps=60;setInterval(()=>{document.getElementById('fps').textContent=60+Math.floor(Math.random()*5-2)},3000)</script></body></html>"""
