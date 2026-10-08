import os
import time

from google import genai


def process_chrome_context(dom_content: str, action: str = "summarize") -> str:
    """Procesa el contenido extraído de la pestaña activa de Chrome usando Gemini 3.6 Flash."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [CHROME BRIDGE]: Se requiere GEMINI_API_KEY configurada."

    if not dom_content or " " in dom_content.strip() and len(dom_content) < 10:
        return "⚠️ [CHROME BRIDGE]: Contenido del DOM vacío o insuficiente."

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""Actúa como el asistente de navegador de Daniela OS.
Analiza este contenido extraído de la pestaña activa de Google Chrome:

{dom_content[:5000]}

Acción solicitada: {action}

Instrucciones:
1. Si 'summarize': Genera un resumen ejecutivo de 3 puntos clave.
2. Si 'extract_graph': Extrae entidades (Personas, Empresas, Tecnologías) para el Knowledge Graph.
3. Responde en Markdown conciso y estructurado."""

        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        analysis = res.text.strip()

        # Guardar registro en el directorio de salida
        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"chrome_sidepanel_{int(time.time())}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"ACTION: {action}\n\n{analysis}")

        return f"🌐 [DANIELA CHROME SIDEPANEL]: Análisis completado.\n📁 Guardado: {filepath}\n\n{analysis}"

    except Exception as e:
        return f"❌ [CHROME BRIDGE ERROR]: {e}"


if __name__ == "__main__":
    print(
        process_chrome_context(
            "<h1>Ejemplo de prueba</h1><p>Contenido de prueba para Chrome Bridge.</p>"
        )
    )
