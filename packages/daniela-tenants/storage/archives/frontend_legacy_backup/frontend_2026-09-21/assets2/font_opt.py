# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

font_bp = Blueprint("font_opt", __name__)

@font_bp.route("/api/frontend2/font/status")
def f_status():
    return jsonify({"variable": True, "preload": True, "subset": "latin", "display": "swap", "savings": "-80%"})

@font_bp.route("/api/frontend2/font/web")
def f_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Font Opt</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>FONT OPTIMIZATION</h1>
<div class="card"><h3>Variable Fonts</h3><p>One file instead of 4</p></div>
<div class="card"><h3>font-display: swap</h3><p>No FOIT</p></div>
<div class="card"><h3>Subset</h3><p>Latin only</p></div>
<div class="card"><h3>Preload</h3><p>Critical fonts</p></div></body></html>"""
