import http.server
import json
import socketserver
import subprocess

PORT = 8888


class DanielaDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            ps_res = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            daemon_active = (
                "run_daemon.sh" in ps_res.stdout or "danielas_guardians" in ps_res.stdout
            )

            status_data = {
                "status": "ONLINE",
                "daemon_active": daemon_active,
                "accounts": ["noemisanalex@gmail.com", "admin@aigestion.net"],
                "gdrive_usage": "0 MB (100% Purgado)",
                "storage_backend": "MEGA:GOOGLE_DRIVE_BACKUP/",
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DANIELA OS - Dashboard Táctico</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { background-color: #0d1117; color: #58a6ff; font-family: monospace; padding: 20px; }
                .card { border: 1px solid #30363d; background: #161b22; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
                h1 { color: #7ee787; font-size: 1.4rem; }
                .status-ok { color: #7ee787; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>🤖 DANIELA OS - PIXEL DASHBOARD</h1>
            <div class="card">
                <h3>Estado del Sistema</h3>
                <p>Guardianes Daemon: <span class="status-ok" id="daemon">Cargando...</span></p>
                <p>Google Drive: <span class="status-ok" id="drive">0 MB</span></p>
            </div>
            <script>
                fetch('/api/status')
                    .then(r => r.json())
                    .then(d => {
                        document.getElementById('daemon').innerText = d.daemon_active ? 'ACTIVO 24/7' : 'INACTIVO';
                        document.getElementById('drive').innerText = d.gdrive_usage;
                    });
            </script>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))


def run_dashboard():
    print(f"🚀 Dashboard táctico de Daniela OS iniciado en http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), DanielaDashboardHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    run_dashboard()
