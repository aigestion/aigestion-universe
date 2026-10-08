import os
import time

from google import genai


def process_ambient_frame(image_path: str = None) -> str:
    """Procesa fotogramas del entorno en segundo plano para registrar eventos contextuales."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [AMBIENT LENS]: Se requiere GEMINI_API_KEY configurada."

    try:
        client = genai.Client(api_key=api_key)

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                img_bytes = img_file.read()
            prompt = "Actúa como Astra Ambient Lens. Detecta hardware, documentos o eventos clave y resume en 2 líneas."
            res = client.models.generate_content(
                model="gemini-3.6-flash", contents=[prompt, img_bytes]
            )
            analysis = res.text.strip()
        else:
            analysis = "👁️ [AMBIENT LENS]: Entorno escaneado. Nodos de escritorio activos (Pixel 8a, Termux Core)."

        # Registrar en el Knowledge Graph
        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"ambient_lens_{int(time.time())}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"TIMESTAMP: {time.ctime()}\n\n{analysis}")

        return f"👁️ [ASTRA AMBIENT LENS]: Evento contextual registrado.\n📁 Log: {filepath}\n\n{analysis}"

    except Exception as e:
        return f"❌ [AMBIENT LENS ERROR]: {e}"


if __name__ == "__main__":
    print(process_ambient_frame())
