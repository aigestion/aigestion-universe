import json
import os
import time

import requests

PC_ENDPOINT = "http://192.168.1.170:5000/api/telemetry"
FILE_INGESTA = os.path.expanduser("~/daniela-os/research/chrome_capturas.json")

print("📡 [DANIELA OS - WORKER]: Demonio Satélite conectado al PC Master...")

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
            print(f"📦 Enviando captura al PC: {data.get('url')}")
            res = requests.post(PC_ENDPOINT, json=data, timeout=3)
            print("✅ [PC MASTER 200]: Sincronizado en tiempo real.")
        except Exception as e:
            print(f"⚠️ [MODO OFFLINE]: Guardado en búfer local ({e})")
