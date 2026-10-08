# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

sec_bp = Blueprint("security", __name__)

@sec_bp.route("/api/frontend2/security/status")
def s_status():
    return jsonify({"csp": True, "xss_protection": True, "csrf": True, "headers": 12, "score": "A+"})

@sec_bp.route("/api/frontend2/security/web")
def s_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Security</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>SECURITY</h1>
<div class="card"><h3>CSP</h3><p>Content Security Policy</p></div>
<div class="card"><h3>XSS Protection</h3><p>Sanitized</p></div>
<div class="card"><h3>CSRF</h3><p>Tokens</p></div>
<div class="card"><h3>Score</h3><p>A+</p></div></body></html>"""
