import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class IngestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length)) if length > 0 else {}
        os.makedirs("/data/data/com.termux/files/home/daniela-os/research", exist_ok=True)
        with open(
            "/data/data/com.termux/files/home/daniela-os/research/chrome_capturas.json",
            "a",
            encoding="utf-8",
        ) as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8081), IngestHandler)
    server.serve_forever()
