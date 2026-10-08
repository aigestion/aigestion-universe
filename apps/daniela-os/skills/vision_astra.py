import os
import subprocess

from google import genai


def inspect_hardware_with_camera() -> str:
    photo_path = os.path.expanduser("~/daniela-os/data/hardware_capture.jpg")
    os.makedirs(os.path.dirname(photo_path), exist_ok=True)

    # Capturar imagen vía Termux
    try:
        subprocess.run(
            ["termux-camera-photo", "-c", "0", photo_path], capture_output=True, timeout=5
        )
    except Exception as e:
        return f"⚠️ [VISION ASTRA]: No se pudo acceder a la cámara de Termux: {e}"

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not os.path.exists(photo_path):
        return "⚠️ [VISION ASTRA]: Captura almacenada localmente en data/hardware_capture.jpg."

    try:
        client = genai.Client(api_key=api_key)
        with open(photo_path, "rb") as img_file:
            image_data = img_file.read()
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=["Analiza este componente o hardware y reporta estado:", image_data],
        )
        return f"👁️ [VISION ASTRA]: {response.text.strip()}"
    except Exception as e:
        return f"❌ [VISION ERROR]: {e}"
