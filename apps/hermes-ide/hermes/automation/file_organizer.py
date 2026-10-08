from flask import Blueprint, jsonify

file_organizer_bp = Blueprint("file_organizer", __name__)

@file_organizer_bp.route("/api/hermes/automation/organizer/status")
def fo_status():
    return jsonify({"organized": 45, "categories": {"documents": 15, "images": 10, "code": 15, "media": 5}})

@file_organizer_bp.route("/api/hermes/automation/organizer/web")
def fo_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>File Organizer</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.cat{background:#111;border-radius:8px;padding:15px;margin:10px 0;display:flex;justify-content:space-between}
.num{font-size:20px;color:#00ff88}
</style></head><body><h1>FILE ORGANIZER</h1>
<div class="cat"><span>Documents</span><span class="num">15</span></div>
<div class="cat"><span>Images</span><span class="num">10</span></div>
<div class="cat"><span>Code</span><span class="num">15</span></div>
<div class="cat"><span>Media</span><span class="num">5</span></div></body></html>"""
