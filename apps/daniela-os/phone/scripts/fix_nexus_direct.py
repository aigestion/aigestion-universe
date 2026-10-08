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
        import json
        from urllib.parse import urlparse
        parsed_path = urlparse(self.path).path

        def respond_json(data_dict, status=200):
            body = json.dumps(data_dict).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        if parsed_path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed_path == "/health":
            respond_json({"status": "HEALTHY", "service": "Nexus Command Center V5 Pro"})
        elif parsed_path == "/api/thermal-status":
            try:
                respond_json(self.get_thermal_summary())
            except Exception as e:
                respond_json({"error": str(e)}, 500)
        elif parsed_path == "/api/tasks-status":
            try:
                respond_json(self.get_tasks_summary())
            except Exception as e:
                respond_json({"error": str(e)}, 500)
        elif parsed_path == "/api/finops-status":
            try:
                respond_json(self.get_finops_summary())
            except Exception as e:
                respond_json({"error": str(e)}, 500)
        elif parsed_path == "/api/chat/stream":
            self.handle_chat_stream()
        else:
            self.send_error(404, "Ruta no encontrada")
""")
        continue

    if in_doget:
        if line.startswith(("    def ", "class ")):
            in_doget = False
            new_lines.append(line)
        continue
    else:
        new_lines.append(line)

with open(nexus_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("✨ [Nexus Repair] do_GET reparado con respond_json autónomo.")
