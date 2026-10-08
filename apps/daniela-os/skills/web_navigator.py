import logging
import os
import time
import urllib.request

from google import genai


def navigate_and_extract(target_url: str = "https://news.ycombinator.com") -> str:
    """Navega a una URL, captura/extrae la estructura visual con Gemini Vision e inyecta datos al Grafo."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [WEB NAVIGATOR]: Se requiere GEMINI_API_KEY configurada."

    # Sanitización: si recibe código o diffs, revertir al valor por defecto
    if not target_url or "diff --git" in target_url or " " in target_url.strip():
        target_url = "https://news.ycombinator.com"

    if not target_url.startswith("http"):
        target_url = "https://" + target_url

    try:
        logging.info(f"🌐 [WEB NAVIGATOR]: Consultando sitio '{target_url}'...")

        req = urllib.request.Request(
            target_url, headers={"User-Agent": "Mozilla/5.0 (DanielaOS/32.0)"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode("utf-8", errors="ignore")[:4000]

        client = genai.Client(api_key=api_key)
        prompt = f"""Actúa como un agente de navegación web autónomo.
Analiza este extracto estructurado de la URL ({target_url}):

{html_content}

Extrae:
1. Título principal y propósito del sitio.
2. 3 Noticias o datos clave destacados.
3. Clasificación de categoría (TECH, FINANZAS, INFRAESTRUCTURA, OTRO).

Responde en formato Markdown directo y conciso."""

        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        extracted_info = res.text.strip()

        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, f"web_nav_{int(time.time())}.txt")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"URL: {target_url}\n\n{extracted_info}")

        return f"🕸️ [GEMINI WEB NAVIGATOR]: Navegación y extracción completada.\n🔗 URL: {target_url}\n📁 Reporte: {report_path}\n\n--- SÍNTESIS DE EXTRACCIÓN ---\n{extracted_info[:300]}..."

    except Exception as e:
        return f"❌ [WEB NAVIGATOR ERROR]: {e}"


if __name__ == "__main__":
    print(navigate_and_extract())
