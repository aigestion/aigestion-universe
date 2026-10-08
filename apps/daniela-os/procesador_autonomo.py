import json
import os
import subprocess
import time

FILE_PATH = os.path.expanduser("~/daniela-os/research/chrome_capturas.json")

print("🤖 [DANIELA OS]: Motor autónomo iniciado en segundo plano...")

# Crear el archivo si no existe
if not os.path.exists(FILE_PATH):
    open(FILE_PATH, "w").close()

with open(FILE_PATH, encoding="utf-8") as f:
    # Ir al final del archivo
    f.seek(0, os.SEEK_END)

    while True:
        line = f.readline()
        if not line:
            time.sleep(1)
            continue

        try:
            data = json.loads(line.strip())
            print(f"\n⚡ [NUEVA CAPTURA RECIBIDA]: {data.get('url')}")
            print(f"📝 Contenido: {data.get('content')[:80]}...")

            # Exportar automáticamente a Google Drive Docs tras cada captura
            subprocess.run(
                [
                    "python3",
                    "-c",
                    "import importlib; gdr = importlib.import_module('plugins.gdrive_reporter'); print(gdr.run('exportar'))",
                ],
                cwd=os.path.expanduser("~/daniela-os"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            print("☁️ Sincronizado automáticamente con Google Docs Vault.")
        except Exception:
            pass
