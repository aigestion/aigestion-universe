import os

nexus_path = os.path.expanduser("~/aig-monorepo/apps/nexus-command-center/nexus_dashboard.py")

with open(nexus_path, encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
in_doget = False

for line in lines:
    if "def do_GET(self):" in line:
        in_doget = True
        new_lines.append("""    def do_GET(self):
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
            self.send_error(404, "Ruta no encontrada en Nexus Command Center")
""")
        continue

    if in_doget:
        # Salir de do_GET cuando encontramos la siguiente función
        if line.startswith(("    def ", "class ")):
            in_doget = False
            new_lines.append(line)
        continue
    else:
        new_lines.append(line)

with open(nexus_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("✨ [Nexus Fix] do_GET reemplazado limpiamente.")
