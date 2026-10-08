import os

from google import genai


def generate_visual_asset(prompt: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ [VISUALIZER]: Sin GEMINI_API_KEY configurada."
    try:
        client = genai.Client(api_key=api_key)
        # Generación conceptual con modelos de imagen/multimodal
        result = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=f"Genera una descripción detallada en SVG para un diagrama de: {prompt}",
        )
        output_path = os.path.expanduser("~/daniela-os/static/live_frame.jpg")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(result.text)
        return "🎨 [VISUALIZER LABS]: Diagrama conceptual guardado en static/live_frame.jpg"
    except Exception as e:
        return f"❌ [VISUALIZER ERROR]: {e}"
