from flask import Blueprint, jsonify

bs_bp = Blueprint("backup_scheduler", __name__)

@bs_bp.route("/api/infra/db/backup/status")
def b_status():
    return jsonify({"interval": "daily", "compression": "gzip", "retention": 30, "last_backup": "2h ago", "size": "12MB"})

@bs_bp.route("/api/infra/db/backup/web")
def b_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Backup Scheduler</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0}
</style></head><body><h1>BACKUP SCHEDULER</h1>
<div class="card"><h3>Interval</h3><p>Daily</p></div>
<div class="card"><h3>Compression</h3><p>gzip</p></div>
<div class="card"><h3>Retention</h3><p>30 days</p></div>
<div class="card"><h3>Last Backup</h3><p>2 hours ago</p></div></body></html>"""
