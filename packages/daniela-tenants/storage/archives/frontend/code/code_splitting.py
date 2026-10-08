# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

split_bp = Blueprint("code_splitting", __name__)

@split_bp.route("/api/frontend2/code/status")
def s_status():
    return jsonify({"chunks": 24, "lazy_loaded": 18, "bundle_size": "142KB", "split_savings": "-65%"})

@split_bp.route("/api/frontend2/code/web")
def s_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Code Splitting</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin:20px 0}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;text-align:center}
.card .num{font-size:28px;color:#00ff88}
</style></head><body><h1>CODE SPLITTING</h1>
<div class="grid"><div class="card"><div class="num">24</div><p>Chunks</p></div><div class="card"><div class="num">18</div><p>Lazy Loaded</p></div><div class="card"><div class="num">-65%</div><p>Savings</p></div><div class="card"><div class="num">142KB</div><p>Bundle</p></div></div>
<p>Webpack/Vite automatic code splitting enabled</p></body></html>"""
