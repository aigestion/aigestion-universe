from flask import Blueprint, jsonify

tc_bp = Blueprint("test_coverage", __name__)

@tc_bp.route("/api/perf/test/status")
def t_status():
    return jsonify({"coverage": "78%", "target": "80%", "tests": 247, "framework": "pytest"})

@tc_bp.route("/api/perf/test/web")
def t_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Test Coverage</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>TEST COVERAGE</h1>
<div class="card"><h3>Current</h3><p>78%</p></div>
<div class="card"><h3>Target</h3><p>80%</p></div>
<div class="card"><h3>Tests</h3><p>247</p></div></body></html>"""
