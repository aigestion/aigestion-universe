import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.append(os.path.expanduser("~/apps/aig/phone/core"))
from daniela_brain import query_daniela


class DanielaServer(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        try:
            req = json.loads(post_data.decode("utf-8"))
            prompt = req.get("prompt", "")
            response = query_daniela(prompt)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"response": response}).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))


def start_server(port=8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, DanielaServer)
    print(f"📡 Servidor de red de Daniela OS activo en el puerto {port}...")
    httpd.handle_request()  # Procesa 1 solicitud en modo demonio ligero


if __name__ == "__main__":
    start_server()
