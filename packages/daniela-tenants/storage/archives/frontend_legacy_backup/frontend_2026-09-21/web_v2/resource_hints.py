# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

rh_bp = Blueprint("resource_hints", __name__)

@rh_bp.route("/api/frontend2/rh/status")
def r_status():
    return jsonify({"preload": True, "prefetch": True, "preconnect": True, "dns_prefetch": True})

@rh_bp.route("/api/frontend2/rh/web")
def r_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Resource Hints</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>RESOURCE HINTS</h1>
<div class="card"><h3>Preload</h3><p>Critical resources</p></div>
<div class="card"><h3>Prefetch</h3><p>Next pages</p></div>
<div class="card"><h3>Preconnect</h3><p>3 origins</p></div>
<div class="card"><h3>DNS Prefetch</h3><p>4 domains</p></div></body></html>"""
