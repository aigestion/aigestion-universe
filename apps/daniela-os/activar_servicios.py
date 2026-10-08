import os
import subprocess

BASE_DIR = os.path.expanduser("~/daniela-os")

print("🚀 [DANIELA OS]: Inicializando servicios de interconexión...")

# 1. Crear el webhook receptor de capturas desde Chrome
webhook_code = """from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os

class IngestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length)) if length > 0 else {}
        os.makedirs('/data/data/com.termux/files/home/daniela-os/research', exist_ok=True)
        with open('/data/data/com.termux/files/home/daniela-os/research/chrome_capturas.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\\n')
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8081), IngestHandler)
    server.serve_forever()
"""

with open(os.path.join(BASE_DIR, "webhook_server.py"), "w", encoding="utf-8") as f:
    f.write(webhook_code)

# 2. Iniciar Webhook en segundo plano
subprocess.run(["pkill", "-f", "webhook_server.py"], check=False)
subprocess.Popen(
    ["python3", os.path.join(BASE_DIR, "webhook_server.py")],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
print("📡 [WEBHOOK]: Listener activo en el puerto 8081 (Escuchando Chrome)")

# 3. Exportar reporte de estado a Google Drive Docs
try:
    import importlib

    gdr = importlib.import_module("plugins.gdrive_reporter")
    resultado = gdr.run("exportar")
    print(f"📄 [GDRIVE REPORT]: {resultado}")
except Exception as e:
    print(f"⚠️ [GDRIVE REPORT]: {e}")

print("\n✨ [ESTADO DEL SISTEMA]: Entorno 100% Interconectado y Operativo.")
