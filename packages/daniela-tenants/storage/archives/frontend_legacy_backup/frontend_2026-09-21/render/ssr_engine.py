# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

ssr_bp = Blueprint("ssr_engine", __name__)

@ssr_bp.route("/api/frontend2/ssr/status")
def s_status():
    return jsonify({"mode": "SSG+ISR", "prerendered": 50, "regenerate_interval": 60, "edge_cached": True})

@ssr_bp.route("/api/frontend2/ssr/web")
def s_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>SSR/SSG</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>SSR / SSG / ISR</h1>
<div class="card"><h3>SSG</h3><p>50 pages pre-rendered at build</p></div>
<div class="card"><h3>ISR</h3><p>Regenerate every 60s</p></div>
<div class="card"><h3>Edge Cache</h3><p>CDN distributed</p></div></body></html>"""
