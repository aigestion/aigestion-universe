import os
import subprocess

import requests

SECRET_TOKEN = os.getenv("SECRET_TOKEN", "DANIELA_POWER_SECRET_2026")
PC_URL = os.getenv("PC_TARGET_URL", "http://192.168.1.170:9090/power")


def guardian_dependencias():
    print("🛠️ [GUARDIÁN]: Verificando librerías...")
    librerias = ["flask", "google-genai", "edge-tts", "pytest", "requests"]
    for lib in librerias:
        try:
            __import__(lib.replace("-", "_"))
        except ImportError:
            print(f"📦 Instalando {lib}...")
            subprocess.run(["pip", "install", lib], stdout=subprocess.DEVNULL)


def sincronizar_secretos_gh():
    print("🔑 [GUARDIÁN]: Sincronizando secreto MASTER_ENV_B64...")
    try:
        res = subprocess.run(
            ["gh", "secret", "list", "--repo", "aigestion/AIGESTION-MONOREPO"],
            capture_output=True,
            text=True,
        )
        if "MASTER_ENV_B64" in res.stdout:
            print("🟢 Secreto Maestro detectado en GitHub CLI.")
    except Exception as e:
        print(f"⚠️ Alerta GitHub CLI: {e}")


def monitorear_servidor_pc():
    print(f"⚡ [GUARDIÁN]: Auditando PC Master en {PC_URL}...")
    try:
        payload = {"token": SECRET_TOKEN, "action": "ping"}
        r = requests.post(PC_URL, json=payload, timeout=3)
        if r.status_code in [200, 400]:
            print("🟢 Servidor PC Master (Puerto 9090): ONLINE")
    except Exception:
        print("🔴 Servidor PC Master: OFFLINE (Esperando reconexión...)")


if __name__ == "__main__":
    print("🛡️ [DANIELA OS]: Activando Orquestador Maestro...")
    guardian_dependencias()
    sincronizar_secretos_gh()
    monitorear_servidor_pc()
