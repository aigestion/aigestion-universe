import json
import os
import subprocess
import time

FILE_INGESTA = os.path.expanduser("~/daniela-os/research/chrome_capturas.json")

print("🦾 [DANIELA OS]: Ciclo Autónomo de Ingesta > Kanban > Drive activado...")

if not os.path.exists(FILE_INGESTA):
    open(FILE_INGESTA, "w").close()

with open(FILE_INGESTA, encoding="utf-8") as f:
    f.seek(0, os.SEEK_END)

    while True:
        line = f.readline()
        if not line:
            time.sleep(2)
            continue

        try:
            data = json.loads(line.strip())
            print(f"\n⚡ [NUEVA CAPTURA RECIBIDA]: {data.get('url')}")

            # Sincronizar actualización con Google Drive Docs
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

            print("☁️ [SYNC]: Expediente en Drive actualizado.")

        except Exception:
            pass
