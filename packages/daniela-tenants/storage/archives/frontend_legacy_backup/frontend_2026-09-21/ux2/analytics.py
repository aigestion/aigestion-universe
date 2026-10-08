# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/api/frontend2/analytics/status")
def a_status():
    return jsonify({"rum": True, "libraries": ["sentry", "datadog", "plausible"], "events": 25, "privacy": True})

@analytics_bp.route("/api/frontend2/analytics/web")
def a_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Analytics</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>ANALYTICS</h1>
<div class="card"><h3>RUM</h3><p>Real User Monitoring</p></div>
<div class="card"><h3>Events</h3><p>25 tracked</p></div>
<div class="card"><h3>Privacy</h3><p>GDPR compliant</p></div>
<div class="card"><h3>Providers</h3><p>Sentry, DD, Plausible</p></div></body></html>"""
