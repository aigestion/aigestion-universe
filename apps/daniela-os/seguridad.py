import os
import subprocess
import time

import google.generativeai as genai
from PIL import Image

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    print("[WARN] GEMINI_API_KEY no configurada — analisis IA desactivado")
    model = None


def take_photo():
    photo_dir = os.path.expanduser("~/daniela-os/static")
    os.makedirs(photo_dir, exist_ok=True)
    photo_path = os.path.join(photo_dir, "seguridad.jpg")
    try:
        subprocess.run(["termux-camera-photo", "-c", "0", photo_path], timeout=10)
        return photo_path if os.path.exists(photo_path) else None
    except Exception as e:
        print("⚠️ Error cámara:", e)
        return None


def analyze_image(path):
    if model is None:
        return "NORMAL"
    try:
        img = Image.open(path)
        prompt = "Analiza esta imagen. ¿Hay una persona o una intrusión en la escena? Responde EXACTAMENTE 'ALERT: [razón]' si ves algo sospechoso, o 'NORMAL' si todo está bien."
        res = model.generate_content([prompt, img])
        return res.text.strip()
    except Exception as e:
        print("⚠️ Error Gemini Vision:", e)
        return "NORMAL"


def notify(message):
    try:
        subprocess.run(
            [
                "termux-notification",
                "--title",
                "⚠️ ALERTA DE SEGURIDAD",
                "--content",
                message,
                "--priority",
                "high",
                "--vibrate",
                "1000",
            ],
            timeout=5,
        )
    except Exception:
        pass


print("🚀 Agente de Seguridad iniciado. Vigilando entorno...")

while True:
    img_path = take_photo()
    if img_path:
        status = analyze_image(img_path)
        print(f"[{time.strftime('%H:%M:%S')}] Estado: {status}")
        if status.startswith("ALERT"):
            notify(status)
    time.sleep(60)  # Analiza cada 60 segundos
