import base64
import os
import subprocess
import time

import requests

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
CAP_PATH = "/data/data/com.termux/files/usr/tmp/daniela_ram/surveillance.jpg"


def capture_and_analyze(prompt="Describe si hay personas o cambios importantes en la escena."):
    os.makedirs(os.path.dirname(CAP_PATH), exist_ok=True)
    subprocess.run(
        ["termux-camera-photo", "-c", "0", CAP_PATH],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.5)

    if not os.path.exists(CAP_PATH) or os.path.getsize(CAP_PATH) < 1000:
        return "No se pudo acceder a la cámara o capturar la imagen."

    if not OPENROUTER_KEY:
        return "Cámara capturada. Se requiere OPENROUTER_API_KEY para análisis visual."

    try:
        with open(CAP_PATH, "rb") as img_f:
            b64_img = base64.b64encode(img_f.read()).decode("utf-8")

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "google/gemini-2.5-flash:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                        },
                    ],
                }
            ],
        }
        r = requests.post(url, headers=headers, json=payload, timeout=6.0)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error en vigilancia visual: {e}"
    return "Análisis de escena finalizado sin detección de anomalías."


if __name__ == "__main__":
    print(capture_and_analyze())
