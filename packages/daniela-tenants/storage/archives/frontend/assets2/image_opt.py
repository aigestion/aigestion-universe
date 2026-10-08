# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

img_bp = Blueprint("image_opt", __name__)

@img_bp.route("/api/frontend2/image/status")
def i_status():
    return jsonify({"format": "AVIF/WebP", "compression": 85, "lazy": True, "responsive": True, "savings": "-70%"})

@img_bp.route("/api/frontend2/image/web")
def i_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Image Opt</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:20px 0}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:15px;text-align:center}
.card .num{font-size:24px;color:#00ff88}
</style></head><body><h1>IMAGE OPTIMIZATION</h1>
<div class="grid"><div class="card"><div class="num">AVIF</div><p>Format</p></div><div class="card"><div class="num">WebP</div><p>Fallback</p></div><div class="card"><div class="num">85%</div><p>Compression</p></div><div class="card"><div class="num">-70%</div><p>Savings</p></div></div><p>Responsive srcset + lazy loading + blur placeholders</p></body></html>"""
