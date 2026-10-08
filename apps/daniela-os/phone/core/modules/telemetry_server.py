import http.server
import json
import socketserver

PORT = 8080


class TelemetryHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            # Datos de salud basicos
            data = {"status": "ONLINE", "device": "Pixel Termux", "monorepo": "AIGESTION-MONOREPO"}
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = "<h1>📱 Daniela OS - Dashboard de Telemetría</h1><p>Estado: ONLINE | Puerto: 8080</p>"
            self.wfile.write(html.encode("utf-8"))


def start_telemetry_server():
    try:
        with socketserver.TCPServer(("", PORT), TelemetryHandler):
            print(f"🌐 Servidor de Telemetría corriendo en http://localhost:{PORT}")
            return f"🌐 **DASHBOARD ACTIVO**: Accede a http://localhost:{PORT}"
    except Exception as e:
        return f"⚠️ Error al iniciar servidor web: {e}"


if __name__ == "__main__":
    start_telemetry_server()
