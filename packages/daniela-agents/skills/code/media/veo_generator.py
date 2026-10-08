import logging
import os
import time

from google import genai
from google.genai import types


def generate_video_asset(prompt_text: str = "Cinematic drone shot of a futuristic server room") -> str:
    """Genera activos visuales usando la SDK google.genai con fallback seguro."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [VEO GENERATOR]: Se requiere GEMINI_API_KEY configurada."

    client = genai.Client(api_key=api_key)
    output_dir = os.path.expanduser("~/daniela-os/output")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Intentar generación de video con Veo
    try:
        operation = client.models.generate_videos(
            model='veo-2.0-generate-001',
            prompt=prompt_text,
            config=types.GenerateVideosConfig(
                person_generation="DONT_ALLOW",
                aspect_ratio="16:9",
                duration_seconds=5,
            )
        )
        while not operation.done:
            time.sleep(5)
            operation = client.operations.get(operation)

        if operation.result and operation.result.generated_videos:
            filepath = os.path.join(output_dir, f"veo_{int(time.time())}.mp4")
            video_bytes = client.files.download(file=operation.result.generated_videos[0].video)
            with open(filepath, "wb") as f:
                f.write(video_bytes)
            return f"🎬 [VEO GENERATOR]: Video generado en {filepath}"
    except Exception as e:
        logging.warning(f"Veo no disponible, aplicando fallback a Imagen 3: {e}")

    # 2. Fallback a Imagen 3 (Generación Visual Ultra-Rápida)
    try:
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt_text,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                output_mime_type="image/jpeg",
            )
        )
        if result.generated_images:
            filepath = os.path.join(output_dir, f"imagen3_{int(time.time())}.jpg")
            with open(filepath, "wb") as f:
                f.write(result.generated_images[0].image.image_bytes)
            return f"🖼️ [LABS ASSET]: Imagen fotorrealista generada (Fallback Imagen 3).\n📁 Ruta: {filepath}"
    except Exception as e:
        return f"❌ [LABS GENERATOR ERROR]: {e}"

    return "❌ [LABS GENERATOR]: No se pudo generar el activo visual."

if __name__ == "__main__":
    print(generate_video_asset())
