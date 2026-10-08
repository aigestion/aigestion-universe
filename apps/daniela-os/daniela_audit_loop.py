import os
import sys

import requests


def ejecutar_auditoria():
    print("\n==================================================")
    print("📊 DANIELA OS — REPORTE DE AUDITORÍA GENERAL")
    print("==================================================")
    py_ver = sys.version.split()[0]
    print(f"🐍 Python Version: {py_ver}")

    termux_api = os.system("which termux-tts-speak > /dev/null 2>&1")
    print(f"🔊 Termux TTS/API: {'🟢 INSTALADO' if termux_api == 0 else '🔴 FALTA termux-api'}")

    api_key = os.getenv("TENCENT_HUNYUAN_API_KEY", "")
    print(
        f"🔑 Tencent API Key: {'🟢 DETECTADA (' + api_key[:8] + '...)' if len(api_key) > 10 else '🔴 NO CONFIGURADA'}"
    )

    try:
        st = os.statvfs(os.path.expanduser("~"))
        free_gb = (st.f_bavail * st.f_frsize) / (1024**3)
        print(f"💾 Espacio Libre Termux: {free_gb:.2f} GB")
    except Exception:
        pass
    print("==================================================\n")


def hablar(texto):
    print(f"\n🤖 Daniela > {texto}")
    os.system(f'termux-tts-speak "{texto}"')


ejecutar_auditoria()

api_key = os.getenv("TENCENT_HUNYUAN_API_KEY")
url = "https://api.hunyuan.cloud.tencent.com/v1/chat/completions"

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

hablar("Auditoría completada. Sistema de voz activo.")

while True:
    try:
        entrada = input("\n🎙️ Tú (Escribe o habla) > ")
        if not entrada.strip():
            continue

        if any(w in entrada.lower() for w in ["salir", "apagar", "cerrar", "descansa"]):
            hablar("Finalizando sesión de control.")
            break

        payload = {
            "model": "hunyuan-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres Daniela OS, asistente en un Google Pixel 8a. Respuestas breves y precisas.",
                },
                {"role": "user", "content": entrada},
            ],
            "temperature": 0.7,
            "max_tokens": 200,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        data = response.json()

        if "choices" in data:
            respuesta = data["choices"][0]["message"]["content"]
            hablar(respuesta)
        else:
            err = data.get("error", {}).get("message", str(data))
            print(f"❌ Error API Tencent: {err}")

    except KeyboardInterrupt:
        print("\n\nSesión de auditoría finalizada por el usuario.")
        break
    except Exception as e:
        print(f"❌ Error de red/ejecución: {e}")
