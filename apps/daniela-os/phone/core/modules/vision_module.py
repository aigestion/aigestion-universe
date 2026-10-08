import base64
import os
import sys

import requests

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")


def analyze_image(image_path, prompt="¿Qué hay en esta imagen? Describe y extrae texto clave."):
    if not os.path.exists(image_path):
        return "❌ Archivo de imagen no encontrado."
    if not OPENROUTER_KEY:
        return "❌ Se requiere OPENROUTER_API_KEY configurada."

    try:
        with open(image_path, "rb") as img_f:
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
        r = requests.post(url, headers=headers, json=payload, timeout=8.0)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        return f"Error Vision API: {r.status_code}"
    except Exception as e:
        return f"Excepción en módulo de visión: {e}"


if __name__ == "__main__":
    img = sys.argv[1] if len(sys.argv) > 1 else "/sdcard/DCIM/Camera/sample.jpg"
    print(analyze_image(img))
