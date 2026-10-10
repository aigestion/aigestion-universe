from flask import Blueprint, jsonify

ci_bp = Blueprint("ci_cd", __name__)

@ci_bp.route("/api/perf/ci/status")
def c_status():
    return jsonify({"provider": "GitHub Actions", "workflows": 5, "stages": ["lint", "test", "build", "deploy"], "auto_deploy": True})

@ci_bp.route("/api/perf/ci/web")
def c_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>CI/CD Pipeline</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>CI/CD PIPELINE</h1>
<div class="card"><h3>Provider</h3><p>GitHub Actions</p></div>
<div class="card"><h3>Workflows</h3><p>5</p></div>
<div class="card"><h3>Stages</h3><p>lint, test, build, deploy</p></div></body></html>"""
