import os

import requests

api_key = os.getenv("TENCENT_HUNYUAN_API_KEY", "")
url = "https://api.hunyuan.cloud.tencent.com/v1/chat/completions"


def hablar(texto):
    print(f"\n🤖 Daniela > {texto}")
    os.system(f'termux-tts-speak "{texto}"')


print("==================================================")
print("🎙️ DANIELA OS - CANAL DE VOZ Y CONVERSACIÓN ACTIVA")
print("==================================================")
hablar("Sistema de voz sincronizado. Estoy escuchando.")

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

while True:
    try:
        entrada = input("\n🎙️ Tú (Escribe o habla) > ")
        if not entrada.strip():
            continue
        if entrada.lower() in ["salir", "exit", "quit"]:
            hablar("Cerrando canal de voz.")
            break

        payload = {
            "model": "hunyuan-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres Daniela OS, un asistente multimedia de voz interactivo y conciso.",
                },
                {"role": "user", "content": entrada},
            ],
            "temperature": 0.7,
            "max_tokens": 300,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        data = response.json()

        if "choices" in data:
            respuesta = data["choices"][0]["message"]["content"]
            hablar(respuesta)
        else:
            print(f"❌ Error en API Tencent: {data}")

    except KeyboardInterrupt:
        print("\n\nSesión de voz finalizada.")
        break
    except Exception as e:
        print(f"❌ Error de red o ejecución: {e}")
