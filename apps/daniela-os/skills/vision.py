import os

from google import genai


def analyze_image(image_path: str, prompt_text: str = "Describe esta imagen") -> str:
    """Procesa una imagen usando la SDK oficial google.genai con Gemini 3.6 Flash."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [VISION]: Falta GEMINI_API_KEY."

    if not os.path.exists(image_path):
        return f"❌ [VISION]: No existe la imagen en '{image_path}'."

    try:
        client = genai.Client(api_key=api_key)
        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()

        response = client.models.generate_content(
            model="gemini-3.6-flash", contents=[prompt_text, image_bytes]
        )
        return f"👁️ [VISION]: {response.text.strip()}"
    except Exception as e:
        return f"❌ [VISION ERROR]: {e}"
