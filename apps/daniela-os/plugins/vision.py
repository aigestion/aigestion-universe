import subprocess
import os
from google import genai
from google.genai import types

# Configuramos el cliente dentro del plugin
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def run(context):
    try:
        # 1. Capturar foto con Termux
        photo_path = "/data/data/com.termux/files/home/daniela-os/vision_snap.jpg"
        subprocess.run(['termux-camera-photo', '-c', '0', photo_path], timeout=5)
        
        if not os.path.exists(photo_path):
            return "❌ [VISION]: Error al acceder al hardware de cámara."

        # 2. Enviar a Gemini para análisis multimodal
        with open(photo_path, "rb") as image_file:
            image_data = image_file.read()

        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=[
                types.Part.from_data(data=image_data, mime_type="image/jpeg"),
                "Analiza esta imagen con detalle táctico. ¿Qué ves? ¿Hay algo que requiera atención urgente o alguna anomalía?"
            ]
        )
        return f"👁️ [VISION]: {response.text}"
    
    except Exception as e:
        return f"❌ [VISION]: Error crítico de análisis: {str(e)}"
