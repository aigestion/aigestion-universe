# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

cache_bp = Blueprint("frontend_cache", __name__)

@cache_bp.route("/api/frontend/cache/status")
def f_status():
    return jsonify({"strategy": "cache-first", "cache_name": "daniela-v2", "assets": 50, "stale_while_revalidate": True})

@cache_bp.route("/api/frontend/cache/web")
def f_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Frontend Cache</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.strategy{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
.strategy.active{border-color:#00ff88}
</style></head><body><h1>FRONTEND CACHE</h1>
<div class="strategy active"><h3>Cache First</h3><p>Assets served from cache</p><p>Stale-while-revalidate: ON</p></div>
<div class="strategy"><h3>API Cache</h3><p>TTL: 5 minutes</p><p>Redis-backed</p></div></body></html>"""
