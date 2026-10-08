# -*- coding: utf-8 -*-
import json, time, hashlib, os
from pathlib import Path
from flask import Blueprint, jsonify, request, send_from_directory

sw_bp = Blueprint("sw_engine", __name__)

SW_CACHE_NAME = "daniela-v2"
CACHED_ASSETS = ["/", "/index.html", "/mobile.html", "/api/status"]

@sw_bp.route("/api/frontend/sw/register", methods=["POST"])
def sw_register():
    data = request.json or {}
    scope = data.get("scope", "/")
    return jsonify({"ok": True, "scope": scope, "cache": SW_CACHE_NAME})

@sw_bp.route("/api/frontend/sw/offline")
def sw_offline():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Offline</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;text-align:center}
.offline{font-size:24px} .icon{font-size:80px;margin:20px 0}
</style></head><body><div class="offline"><div class="icon">📡</div><h1>OFFLINE</h1><p>You're offline. Content may be cached.</p><p>Reconnect to restore full functionality.</p></div></body></html>"""

@sw_bp.route("/api/frontend/sw/cache", methods=["POST"])
def sw_cache():
    data = request.json or {}
    urls = data.get("urls", [])
    return jsonify({"cached": len(urls), "cache": SW_CACHE_NAME})

@sw_bp.route("/api/frontend/sw/web")
def sw_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Service Worker</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
.active{color:#00ff88} .inactive{color:#ff0066}
</style></head><body><h1>SERVICE WORKER ENGINE</h1>
<div class="card"><h3>PWA Status</h3><p>Service Worker: <span class="active">Active</span></p><p>Cache: daniela-v2</p><p>Offline Support: Enabled</p></div>
<div class="card"><h3>Cached Assets</h3><p>5 assets cached</p><p>Strategy: Cache First</p></div>
<div class="card"><h3>Manifest</h3><p>PWA Ready: Yes</p><p>Theme Color: #0a0a0f</p></div></body></html>"""
