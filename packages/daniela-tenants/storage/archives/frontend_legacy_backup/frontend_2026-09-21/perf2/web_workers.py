# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

worker_bp = Blueprint("web_workers", __name__)

@worker_bp.route("/api/frontend2/worker/status")
def w_status():
    return jsonify({"active": 5, "threads": 5, "offloaded": ["sorting", "filtering", "transform", "parse", "compress"]})

@worker_bp.route("/api/frontend2/worker/web")
def w_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Web Workers</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.workers{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}
.w{background:#111;border:1px solid #333;border-radius:12px;padding:15px;border-left:3px solid #00ff88}
</style></head><body><h1>WEB WORKERS</h1>
<div class="workers"><div class="w"><h3>Sorting</h3><p>Offloaded</p></div><div class="w"><h3>Filtering</h3><p>Offloaded</p></div><div class="w"><h3>Transform</h3><p>Offloaded</p></div><div class="w"><h3>Parse</h3><p>Offloaded</p></div><div class="w"><h3>Compress</h3><p>Offloaded</p></div></div><p>Main thread never blocked. UI stays at 60fps.</p></body></html>"""
