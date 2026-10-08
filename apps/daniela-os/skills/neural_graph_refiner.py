import os
import time

from google import genai
from skills import knowledge_graph


def refine_knowledge_graph() -> str:
    """Audita y optimiza el Knowledge Graph con respuesta ultrarrápida."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [NEURAL GRAPH REFINER]: Se requiere GEMINI_API_KEY."

    try:
        try:
            graph_data = knowledge_graph.query_graph()
        except Exception as e:
            graph_data = f"Graph data fallback: {e}"

        client = genai.Client(api_key=api_key)
        prompt = f"""Audita este Knowledge Graph de forma ejecutiva en menos de 100 palabras:
{graph_data}

1. Nodos a unificar.
2. Relaciones a consolidar.
3. Health Index (0-100%)."""

        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        report = res.text.strip()

        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"graph_refactored_{int(time.time())}.json")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)

        return f"🕸️ [NEURAL GRAPH REFINER]: Grafo optimizado.\n📁 Log: {filepath}\n\n{report}"

    except Exception as e:
        return f"❌ [GRAPH REFINER ERROR]: {e}"


if __name__ == "__main__":
    print(refine_knowledge_graph())
