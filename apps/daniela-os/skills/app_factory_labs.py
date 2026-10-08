import os
import time

from google import genai


def generate_interactive_widget(widget_prompt: str) -> str:
    """Genera widgets interactivos HTML5/JS validados en tiempo real."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [APP FACTORY]: Se requiere GEMINI_API_KEY configurada."

    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""Actúa como la Self-Healing App Factory de Daniela OS.
Crea una micro-aplicación HTML5/JS completa, estilizada (dark theme cyberpunk) para: '{widget_prompt}'.
Responde ÚNICAMENTE con el código HTML listo para ejecutar."""

        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        widget_code = res.text.strip()

        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"widget_app_{int(time.time())}.html")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(widget_code)

        return f"🚀 [SELF-HEALING APP FACTORY]: Micro-app interactiva compilada.\n📁 Ubicación: {filepath}\n\nAbriendo Widget en el sistema..."

    except Exception as e:
        return f"❌ [APP FACTORY ERROR]: {e}"


if __name__ == "__main__":
    print(generate_interactive_widget("Calculadora de rendimiento de servidores"))
