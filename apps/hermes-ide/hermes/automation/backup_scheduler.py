from flask import Blueprint, jsonify

backup_bp = Blueprint("backup_scheduler", __name__)

@backup_bp.route("/api/hermes/automation/backup/status")
def b_status():
    return jsonify({"backups": [{"name": "Daily", "last": "2026-09-13", "size": "256MB", "status": "ok"}, {"name": "Weekly", "last": "2026-09-08", "size": "1.2GB", "status": "ok"}]})

@backup_bp.route("/api/hermes/automation/backup/web")
def b_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Backup Scheduler</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.backup{background:#111;border:1px solid #333;border-radius:8px;padding:15px;margin:10px 0;display:flex;justify-content:space-between}
.ok{color:#00ff88}
</style></head><body><h1>BACKUP SCHEDULER</h1><div id="backups"></div>
<script>fetch('/api/hermes/automation/backup/status').then(r=>r.json()).then(d=>{document.getElementById('backups').innerHTML=d.backups.map(b=>'<div class="backup"><div><h3>'+b.name+'</h3><p>'+b.last+' | '+b.size+'</p></div><span class="ok">'+b.status+'</span></div>').join('')})</script></body></html>"""
