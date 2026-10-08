import re

path = "/data/data/com.termux/files/home/aig-monorepo/apps/nexus-command-center/nexus_dashboard.py"

html_code = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>NEXUS COMMAND CENTER V5 PRO</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #080b12; color: #00f0ff; font-family: -apple-system, sans-serif; padding: 20px; }
        .header { background: #0f1523; padding: 15px; border-bottom: 2px solid #00f0ff; display: flex; justify-content: space-between; align-items: center; border-radius: 8px; margin-bottom: 20px; }
        .card { background: #0e1320; border: 1px solid #1c273e; padding: 16px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        h1 { font-size: 18px; color: #fff; }
        h2 { font-size: 14px; color: #ffb700; margin-bottom: 10px; }
        p { font-size: 12px; color: #94a3b8; line-height: 1.6; }
        .status { color: #00ff9d; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ NEXUS COMMAND CENTER</h1>
        <span class="status">🟢 ONLINE</span>
    </div>
    <div class="card">
        <h2>📡 TELEMETRÍA MÓVIL Y NODOS</h2>
        <p>Nodo Local: <strong>Pixel 8a (Master Edge)</strong></p>
        <p>Sincronización PC Master: <span class="status">ACTIVE (100.64.170.206)</span></p>
        <p>Motor de Ejecución: <strong>Python 3.14 / SocketServer</strong></p>
    </div>
    <div class="card">
        <h2>🛡️ SENTINEL & TASK WORKER</h2>
        <p>Estado de la Bóveda: <strong>Sincronizada</strong></p>
        <p>Auto-Recovery Guard: <span class="status">RUNNING</span></p>
    </div>
</body>
</html>
"""

with open(path, encoding="utf-8") as f:
    content = f.read()

# Definición limpia de HTML_TEMPLATE sin f-strings
template_definition = f'HTML_TEMPLATE = """{html_code}"""\n'

if "HTML_TEMPLATE" not in content:
    content = template_definition + content
else:
    # Reemplazo de cualquier definición anterior de HTML_TEMPLATE
    content = re.sub(
        r"HTML_TEMPLATE\s*=\s*[\s\S]*?(?=\n[A-Z_]+\s*=|\nclass|\ndef|$)",
        template_definition,
        content,
        count=1,
    )

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ HTML_TEMPLATE definido e inyectado con éxito.")
