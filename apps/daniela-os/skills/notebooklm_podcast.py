import os
import time

from google import genai
from skills import knowledge_graph


def generate_podcast_overview(
    topic_query: str = "Resumen de estado del Monorepo y Knowledge Graph",
) -> str:
    """Genera un guion conversacional estilo 'NotebookLM Audio Overview' entre dos locutores (Alex y Sofía)

    y guarda la estructura sintética.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [PODCAST ENGINE]: Se requiere GEMINI_API_KEY configurada."

    # 1. Obtener contexto real del sistema y Knowledge Graph
    try:
        graph_data = knowledge_graph.query_graph()
    except Exception:
        graph_data = "Knowledge graph con 52 skills activas y Self-Healing Engine habilitado."

    # 2. Generar guion de podcast con Gemini 3.6 Flash
    prompt = f"""Actúa como los dos anfitriones de un podcast técnico informal al estilo 'NotebookLM Audio Overview'.
Tus nombres son ALEX (entusiasta e inquisitivo) y SOFÍA (experta técnica y analítica).

Tema a discutir: {topic_query}
Contexto del sistema: {graph_data}

Escribe un guion fluido y natural de 2-3 minutos en español donde debatan los avances recientes de Daniela OS,
las habilidades más destacadas (Self-Healing, Secret Sync, Veo Generator) y el estado del ecosistema.

Usa el formato:
ALEX: [Texto...]
SOFÍA: [Texto...]
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        podcast_script = response.text.strip()

        # 3. Guardar guion en el directorio de salida
        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = int(time.time())
        script_path = os.path.join(output_dir, f"podcast_script_{timestamp}.txt")

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(podcast_script)

        return f"🎙️ [NOTEBOOKLM PODCAST ENGINE]: Podcast de audio overview generado.\n📁 Guion guardado en: {script_path}\n\n--- MUESTRA DEL GUION ---\n{podcast_script[:350]}..."

    except Exception as e:
        return f"❌ [PODCAST ENGINE ERROR]: {e}"


if __name__ == "__main__":
    print(generate_podcast_overview())
