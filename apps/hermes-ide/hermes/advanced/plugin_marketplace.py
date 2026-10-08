from flask import Blueprint, jsonify

plugin_marketplace_bp = Blueprint("plugin_marketplace", __name__)

PLUGINS = [
    {"name": "Memory Pro", "desc": "Advanced memory management", "installs": 1250, "rating": 4.8},
    {"name": "Code Master", "desc": "AI-powered code review", "installs": 890, "rating": 4.7},
    {"name": "Email Wizard", "desc": "Smart email management", "installs": 2100, "rating": 4.9},
    {"name": "Health Tracker", "desc": "Personal health monitoring", "installs": 560, "rating": 4.5},
    {"name": "Finance AI", "desc": "Financial analysis", "installs": 780, "rating": 4.6}
]

@plugin_marketplace_bp.route("/api/hermes/advanced/marketplace/status")
def pm_status():
    return jsonify({"plugins": PLUGINS})

@plugin_marketplace_bp.route("/api/hermes/advanced/marketplace/web")
def pm_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Plugin Marketplace</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.plugin{background:#111;border:1px solid #333;border-radius:8px;padding:15px;margin:10px 0;display:flex;justify-content:space-between;align-items:center}
.install{background:#00ff8822;border:1px solid #00ff88;color:#00ff88;padding:5px 12px;border-radius:6px;cursor:pointer}
</style></head><body><h1>PLUGIN MARKETPLACE</h1><div id="plugins"></div>
<script>fetch('/api/hermes/advanced/marketplace/status').then(r=>r.json()).then(d=>{document.getElementById('plugins').innerHTML=d.plugins.map(p=>'<div class="plugin"><div><h3>'+p.name+'</h3><p>'+p.desc+'</p><small>'+p.installs+' installs | '+p.rating+'</small></div><button class="install">Install</button></div>').join('')})</script></body></html>"""
