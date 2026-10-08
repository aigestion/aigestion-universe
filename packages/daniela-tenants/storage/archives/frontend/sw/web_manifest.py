# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

manifest_bp = Blueprint("web_manifest", __name__)

@manifest_bp.route("/api/frontend/manifest/status")
def m_status():
    return jsonify({"name": "Daniela Omnipresente", "short_name": "Daniela", "start_url": "/", "display": "standalone", "background_color": "#0a0a0f", "theme_color": "#00f0ff"})

@manifest_bp.route("/api/frontend/manifest/web")
def m_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>PWA Manifest</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
.icon{font-size:40px;margin-bottom:10px}
</style></head><body><h1>PWA MANIFEST</h1>
<div class="card"><div class="icon">📱</div><h3>Daniela Omnipresente</h3><p>Standalone PWA</p><p>Installable on any device</p></div>
<div class="card"><div class="icon">🎨</div><h3>Theme</h3><p>Dark mode default</p><p>Supports install prompt</p></div></body></html>"""
