from flask import Blueprint, jsonify

code_review_auto_bp = Blueprint("code_auto_reviewer", __name__)
_reviews = []

@code_review_auto_bp.route("/api/hermes/automation/code-review/status")
def cr_status():
    return jsonify({"reviews": _reviews[-10:], "total": len(_reviews)})

@code_review_auto_bp.route("/api/hermes/automation/code-review/web")
def cr_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Code Auto Reviewer</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.review{background:#111;border-left:3px solid #00ff88;padding:10px;margin:5px 0}
</style></head><body><h1>CODE AUTO REVIEWER</h1><div id="reviews"></div>
<script>fetch('/api/hermes/automation/code-review/status').then(r=>r.json()).then(d=>{document.getElementById('reviews').innerHTML=d.reviews.length?d.reviews.map(r=>'<div class="review">'+r+'</div>').join(''):'<p>No reviews yet</p>'})</script></body></html>"""
