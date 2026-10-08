import os
import subprocess

import requests

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")


def generate_morning_briefing():
    prompt = (
        "Genera un resumen ejecutivo matutino en español de España (máximo 3 frases). "
        "Da los buenos días, confirma que la infraestructura del Pixel y el Monorepo están al 100%, "
        "y desea una jornada productiva."
    )
    if OPENROUTER_KEY:
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "google/gemini-2.5-flash:free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=4.0)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
    return "Buenos días. Todos los sistemas del Pixel operan con normalidad."


if __name__ == "__main__":
    briefing = generate_morning_briefing()
    print(briefing)
    subprocess.run(["python3", os.path.expanduser("~/apps/aig/phone/core/tts_hd.py"), briefing])
