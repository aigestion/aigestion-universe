import time

import requests

PC_MASTER_IP = "192.168.1.170"
PORT = "5000"
ENDPOINT = f"http://{PC_MASTER_IP}:{PORT}/api/v1/telemetry"


def iniciar_satelite():
    print("📡 [DANIELA OS - WORKER]: Demonio Satélite conectado al PC Master...")
    print(f"🔗 Enlace objetivo: {ENDPOINT}")

    while True:
        try:
            # Ping de sincronización y heartbeat con el nodo central
            res = requests.get(f"http://{PC_MASTER_IP}:{PORT}/", timeout=3)
            if res.status_code == 200:
                print("🟢 [SATÉLITE MÓVIL]: Sincronización activa con PC Host.", end="\r")
        except Exception:
            print("⚠️ [SATÉLITE MÓVIL]: Esperando conexión con el nodo PC Master...", end="\r")

        time.sleep(5)


if __name__ == "__main__":
    iniciar_satelite()
