import os

from google import genai


def analyze_visual_lens(image_path: str = None) -> str:
    """Procesa análisis de visión multimodal usando la SDK oficial google.genai."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [LENS ENGINE]: Se requiere GEMINI_API_KEY configurada."

    if not image_path or not os.path.exists(image_path):
        return "📷 [LENS ENGINE]: Módulo inicializado y listo para análisis de imágenes."

    try:
        client = genai.Client(api_key=api_key)
        with open(image_path, "rb") as f:
            img_bytes = f.read()

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=["Analiza el contenido visual de esta imagen en detalle.", img_bytes],
        )
        return f"🔍 [LENS ANALYSIS]: {response.text.strip()}"
    except Exception as e:
        return f"❌ [LENS ERROR]: {e}"


if __name__ == "__main__":
    print(analyze_visual_lens())
