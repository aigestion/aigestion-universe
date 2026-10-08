from flask import Blueprint, jsonify

fmt_bp = Blueprint("auto_formatting", __name__)

@fmt_bp.route("/api/perf/format/status")
def f_status():
    return jsonify({"tools": ["black", "ruff", "isort"], "pre_commit": True, "line_length": 100, "target_version": "py311"})

@fmt_bp.route("/api/perf/format/web")
def f_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Auto Formatting</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>AUTO FORMATTING</h1>
<div class="card"><h3>Tools</h3><p>black, ruff, isort</p></div>
<div class="card"><h3>Pre-commit</h3><p>Enabled</p></div>
<div class="card"><h3>Line Length</h3><p>100</p></div></body></html>"""
