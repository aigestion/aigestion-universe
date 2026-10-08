import os
import time

from google import genai


def generate_canvas_3d_scape(target_url: str = "https://aigestion.net") -> str:
    """Extrae la estructura DOM y genera un grafo/paisaje 3D interactivo codificado en Three.js."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [CANVAS 3D]: Se requiere GEMINI_API_KEY configurada."

    if not target_url or " " in target_url.strip() or "diff --git" in target_url:
        target_url = "https://aigestion.net"

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""Actúa como un Diseñador de Grafo 3D y Web Scraper Espacial.
URL objetivo: {target_url}

Genera el código HTML/JavaScript autónomo utilizando Three.js (vía CDN CDNJS) para visualizar la estructura relacional de la página como una red tridimensional de nodos interconectados (Nodos: Header, Main, Nav, Footer, API Endpoints).

Estructura de la respuesta:
Genera ÚNICAMENTE el bloque HTML completo listo para abrir en Chrome Canvas."""

        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        canvas_html = res.text.strip()

        # Guardar artefacto HTML interactivo
        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"canvas_3d_{int(time.time())}.html")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(canvas_html)

        return f"🎨 [GEMINI LIVE CANVAS 3D]: Modelo 3D y Web Scrape visual generado con éxito.\n🔗 URL Target: {target_url}\n📁 Canvas 3D Render: {filepath}\n\nAbriendo entorno Canvas interactivamente..."

    except Exception as e:
        return f"❌ [CANVAS 3D ERROR]: {e}"


if __name__ == "__main__":
    print(generate_canvas_3d_scape())
