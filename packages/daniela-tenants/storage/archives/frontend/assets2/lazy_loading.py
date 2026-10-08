# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

lazy_bp = Blueprint("lazy_loading", __name__)

@lazy_bp.route("/api/frontend2/lazy/status")
def l_status():
    return jsonify({"images_lazy": True, "components_lazy": 15, "iframes_lazy": True, "fonts_lazy": True})

@lazy_bp.route("/api/frontend2/lazy/web")
def l_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Lazy Loading</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.features{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}
.feat{background:#111;border:1px solid #333;border-radius:12px;padding:15px 20px}
.feat.on{border-color:#00ff88}
</style></head><body><h1>LAZY LOADING</h1>
<div class="features"><div class="feat on"><h3>Images</h3><p>loading=lazy</p></div><div class="feat on"><h3>Components</h3><p>15 async</p></div><div class="feat on"><h3>Iframes</h3><p>lazy load</p></div><div class="feat on"><h3>Fonts</h3><p>font-display</p></div></div></body></html>"""
