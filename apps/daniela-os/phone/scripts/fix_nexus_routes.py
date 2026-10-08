import os

nexus_path = os.path.expanduser("~/aig-monorepo/apps/nexus-command-center/nexus_dashboard.py")

with open(nexus_path, encoding="utf-8") as f:
    code = f.read()

# Reemplazar do_GET completo por una versión limpia y robusta
old_doget_start = "def do_GET(self):"
# Buscar el final de do_GET o reescribir la lógica de rutas
new_do_get = """    def do_GET(self):
        from urllib.parse import urlparse
        parsed_path = urlparse(self.path).path

        if parsed_path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed_path == "/health":
            self.send_json_or_html(200, {"status": "HEALTHY", "service": "Nexus Command Center V5 Pro"})
        elif parsed_path == "/api/thermal-status":
            self.send_json_or_html(200, self.get_thermal_summary())
        elif parsed_path == "/api/tasks-status":
            self.send_json_or_html(200, self.get_tasks_summary())
        elif parsed_path == "/api/finops-status":
            self.send_json_or_html(200, self.get_finops_summary())
        elif parsed_path == "/api/chat/stream":
            self.handle_chat_stream()
        else:
            self.send_error(404, "Ruta no encontrada en Nexus Command Center")"""

# Aplicar el parche reemplazando la función do_GET existente
import re

code = re.sub(r"def do_GET\(self\):.*?(?=def |\Z)", new_do_get + "\n\n", code, flags=re.DOTALL)

with open(nexus_path, "w", encoding="utf-8") as f:
    f.write(code)

print("✨ [Nexus Routes] Rutas do_GET reestructuradas y reparadas con éxito.")
