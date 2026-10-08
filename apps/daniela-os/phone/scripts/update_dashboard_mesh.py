import os

dash_path = os.path.expanduser("~/aig-monorepo/pixela8/app/agents/agent_dashboard.py")

code = """#!/usr/bin/env python3
import os, sqlite3, json, subprocess, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

DB_PATH = os.path.expanduser("~/aig-monorepo/pixela8/app/daniela_memory.db")
ROADMAP_PATH = os.path.expanduser("~/aig-monorepo/ROADMAP.md")
REPO_DIR = os.path.expanduser("~/aig-monorepo")

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

def check_mesh_status():
    report = {}
    nodes = {"Router Gateway": "192.168.1.1", "DNS Cloudflare": "1.1.1.1"}
    for name, ip in nodes.items():
        res = subprocess.run(["ping", "-c", "1", "-W", "1", ip], capture_output=True, text=True)
        report[name] = "ONLINE" if res.returncode == 0 else "OFFLINE"
    return report

def run_git_sync():
    try:
        subprocess.run(["git", "-C", REPO_DIR, "add", "."], check=True)
        subprocess.run(["git", "-C", REPO_DIR, "commit", "-m", "Auto-sync via Dashboard Web"], check=False)
        res = subprocess.run(["git", "-C", REPO_DIR, "push"], capture_output=True, text=True, check=False)
        return "Sync exitoso con GitHub." if res.returncode == 0 else "Git Sync completado."
    except Exception as e:
        return f"Error Git: {e}"

def add_note_web(content):
    if not os.path.exists(DB_PATH): return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ts = subprocess.check_output(["date", "+%Y-%m-%d %H:%M:%S"]).decode().strip()
    cursor.execute("INSERT INTO quick_memory (timestamp, key_tag, content) VALUES (?, ?, ?)", (ts, "WEB_NOTE", content))
    conn.commit()
    conn.close()

class DashboardHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        params = urllib.parse.parse_qs(body)
        action = params.get('action', [''])[0]

        if action == 'sync':
            run_git_sync()
        elif action == 'add_note':
            note_text = params.get('note', [''])[0]
            if note_text:
                add_note_web(note_text)

        self.send_response(303)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        bat = get_battery()
        notes = get_recent_notes()
        jobs = get_jobs()
        sentinel_logs = get_sentinel_logs()
        mesh_status = check_mesh_status()

        roadmap_content = "Sin roadmap."
        if os.path.exists(ROADMAP_PATH):
            with open(ROADMAP_PATH, "r", encoding="utf-8") as f:
                roadmap_content = f.read()[:1000]

        notes_html = "".join([f"<li><strong>[{n[0]}]</strong> {n[1]}</li>" for n in notes]) or "<li>Sin notas.</li>"
        jobs_html = "".join([f"<li><strong>#{j[0]} [{j[3]}]</strong> {j[2]}</li>" for j in jobs]) or "<li>Sin tareas.</li>"
        sentinel_html = "".join([f"<li><strong>[{s[0]}]</strong> {s[1]}: <span style='color:#4ade80;'>{s[2]}</span></li>" for s in sentinel_logs]) or "<li>Sin eventos.</li>"
        mesh_html = "".join([f"<li><strong>{k}:</strong> <span style='color:{'#4ade80' if v=='ONLINE' else '#f87171'};'>{v}</span></li>" for k, v in mesh_status.items()])

        html = f\"\"\"<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daniela AI Swarm - Control Pro</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 15px; margin: 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; max-width: 1100px; margin: auto; }}
        .card {{ background: #1e293b; padding: 15px; border-radius: 12px; border: 1px solid #334155; }}
        h1 {{ color: #38bdf8; text-align: center; margin-bottom: 20px; font-size: 1.5rem; }}
        h2 {{ color: #a855f7; font-size: 1.1rem; margin-top: 0; border-bottom: 1px solid #334155; padding-bottom: 5px; }}
        .stat {{ font-size: 2.2rem; font-weight: bold; color: #4ade80; }}
        pre {{ background: #090d16; padding: 10px; border-radius: 6px; font-size: 0.8rem; overflow-x: auto; color: #94a3b8; }}
        ul {{ padding-left: 20px; color: #cbd5e1; font-size: 0.9rem; }}
        .btn {{ background: #0284c7; color: white; border: none; padding: 10px 15px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; margin-top: 5px; }}
        .btn:active {{ background: #0369a1; }}
        input[type="text"] {{ width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: white; box-sizing: border-box; margin-bottom: 8px; }}
    </style>
</head>
<body>
    <h1>📱 Daniela AI Swarm — Centro de Control</h1>
    <div class="grid">
        <div class="card">
            <h2>🔋 Telemetría Hardware</h2>
            <div class="stat">{bat.get('percentage')}%</div>
            <p>Estado: <strong>{bat.get('status')}</strong> | Temp: <strong>{bat.get('temperature')}°C</strong></p>
            <form method="POST">
                <input type="hidden" name="action" value="sync">
                <button type="submit" class="btn">⚡ Ejecutar Git Sync</button>
            </form>
        </div>
        <div class="card">
            <h2>🛰️ Red & Mesh Health</h2>
            <ul>{mesh_html}</ul>
        </div>
        <div class="card">
            <h2>📝 Nota Rápida (Secretario)</h2>
            <form method="POST">
                <input type="hidden" name="action" value="add_note">
                <input type="text" name="note" placeholder="Escribe una nota rápida..." required>
                <button type="submit" class="btn" style="background:#8b5cf6;">💾 Guardar Nota</button>
            </form>
            <ul>{notes_html}</ul>
        </div>
        <div class="card">
            <h2>🛡️ Sentinel Auto-Fixer</h2>
            <ul>{sentinel_html}</ul>
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

    def log_message(self, format, *args): return

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), DashboardHandler)
    server.serve_forever()
"""

with open(dash_path, "w", encoding="utf-8") as f:
    f.write(code)

print("✨ [DASHBOARD MESH UPDATE] Dashboard actualizado con telemetría de red y Mesh.")
