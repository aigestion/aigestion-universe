import os

nexus_path = os.path.expanduser("~/aig-monorepo/apps/nexus-command-center/nexus_dashboard.py")

with open(nexus_path, encoding="utf-8") as f:
    code = f.read()

# 1. Habilitar SO_REUSEADDR en ThreadedHTTPServer
old_server_cls = """class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True"""

new_server_cls = """class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True"""

if old_server_cls in code:
    code = code.replace(old_server_cls, new_server_cls)

# 2. Agregar lógica de retribución de puertos en run()
old_run = """def run(server_class=ThreadedHTTPServer, handler_class=NexusHandler, port=8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"🚀 [Nexus Pro V5] Servidor activo en http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()"""

new_run = """def run(server_class=ThreadedHTTPServer, handler_class=NexusHandler, default_port=8000):
    ports = [default_port, 8080, 8001, 8081]
    httpd = None
    active_port = default_port
    for p in ports:
        try:
            httpd = server_class(("", p), handler_class)
            active_port = p
            break
        except OSError:
            continue
    if not httpd:
        print("❌ No se pudo abrir ningún puerto entre 8000 y 8081.")
        return

    print(f"🚀 [Nexus Pro V5] Servidor activo en http://localhost:{active_port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()"""

if old_run in code:
    code = code.replace(old_run, new_run)

with open(nexus_path, "w", encoding="utf-8") as f:
    f.write(code)

print("✨ [Port Fix] SO_REUSEADDR y Fallback de Puertos inyectados en nexus_dashboard.py.")
