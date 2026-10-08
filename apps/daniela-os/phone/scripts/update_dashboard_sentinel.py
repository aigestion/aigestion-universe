import os

repo_dir = os.path.expanduser("~/aig-monorepo/pixela8/app/agents")
dash_path = os.path.join(repo_dir, "agent_dashboard.py")

code = """#!/usr/bin/env python3
import os
import sqlite3
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

DB_PATH = os.path.expanduser("~/aig-monorepo/pixela8/app/daniela_memory.db")
ROADMAP_PATH = os.path.expanduser("~/aig-monorepo/ROADMAP.md")

def get_battery():
    try:
        res = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return json.loads(res.stdout)
    except Exception:
        pass
    return {"percentage": 0, "temperature": 0, "status": "UNKNOWN"}

def get_sentinel_logs():
    if not os.path.exists(DB_PATH): return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT timestamp, service, status FROM system_sentinel ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
    except Exception: rows = []
    conn.close()
    return rows

def get_recent_notes():
    if not os.path.exists(DB_PATH): return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT timestamp, content FROM quick_memory ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
    except Exception: rows = []
    conn.close()
    return rows

def get_jobs():
    if not os.path.exists(DB_PATH): return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, timestamp, task_name, status FROM background_jobs ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
    except Exception: rows = []
    conn.close()
    return rows

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        bat = get_battery()
        notes = get_recent_notes()
        jobs = get_jobs()
        sentinel_logs = get_sentinel_logs()

        roadmap_content = "Sin roadmap."
        if os.path.exists(ROADMAP_PATH):
            with open(ROADMAP_PATH, "r", encoding="utf-8") as f:
                roadmap_content = f.read()[:1000]

        notes_html = "".join([f"<li><strong>[{n[0]}]</strong> {n[1]}</li>" for n in notes]) or "<li>Sin notas grabadas.</li>"
        jobs_html = "".join([f"<li><strong>#{j[0]} [{j[3]}]</strong> {j[2]} ({j[1]})</li>" for j in jobs]) or "<li>Sin tareas en cola.</li>"
        sentinel_html = "".join([f"<li><strong>[{s[0]}]</strong> {s[1]}: <span style='color:#4ade80;'>{s[2]}</span></li>" for s in sentinel_logs]) or "<li>Sin eventos de reinicio.</li>"

        html = f\"\"\"<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daniela AI Swarm</title>
    <style>
        body {{ font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; margin: 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; max-width: 1000px; margin: auto; }}
        .card {{ background: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }}
        h1 {{ color: #38bdf8; text-align: center; }} h2 {{ color: #a855f7; font-size: 1.1rem; margin-top: 0; }}
        .stat {{ font-size: 2.2rem; font-weight: bold; color: #4ade80; }}
        pre {{ background: #090d16; padding: 10px; border-radius: 6px; font-size: 0.8rem; overflow-x: auto; color: #94a3b8; }}
        ul {{ padding-left: 20px; color: #cbd5e1; }}
    </style>
</head>
<body>
    <h1>📱 Daniela AI Swarm Dashboard</h1>
    <div class="grid">
        <div class="card">
            <h2>🔋 Telemetría Pixel 8a</h2>
            <div class="stat">{bat.get('percentage')}%</div>
            <p>Estado: <strong>{bat.get('status')}</strong> | Temp: <strong>{bat.get('temperature')}°C</strong></p>
        </div>
        <div class="card">
            <h2>🛡️ Sentinel Auto-Fixer</h2>
            <ul>{sentinel_html}</ul>
        </div>
        <div class="card">
            <h2>🧠 Memoria Reciente</h2>
            <ul>{notes_html}</ul>
        </div>
        <div class="card">
            <h2>⚙️ Cola de Trabajos (Worker)</h2>
            <ul>{jobs_html}</ul>
        </div>
        <div class="card" style="grid-column: 1 / -1;">
            <h2>🗺️ Roadmap Actual</h2>
            <pre>{roadmap_content}</pre>
        </div>
    </div>
</body>
</html>\"\"\"

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), DashboardHandler)
    server.serve_forever()
"""

with open(dash_path, "w", encoding="utf-8") as f:
    f.write(code)

print("✅ Dashboard actualizado con soporte para el Sentinel.")
