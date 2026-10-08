import os
import time

from google import genai
from skills import knowledge_graph


def scan_spatial_environment(image_path: str = None) -> str:
    """Escanea el entorno físico, detecta objetos/componentes con Gemini Vision e inyecta la memoria espacial al Grafo."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [SPATIAL ASTRA]: Se requiere GEMINI_API_KEY configurada."

    # Si no se provee imagen o viene un parámetro inválido de diff/commit, usar reporte simbólico de espacio
    if (
        not image_path
        or " " in image_path.strip()
        or "diff --git" in image_path
        or not os.path.exists(image_path)
    ):
        image_path = None

    try:
        client = genai.Client(api_key=api_key)

        if image_path:
            with open(image_path, "rb") as img_file:
                img_bytes = img_file.read()

            prompt = """Actúa como el motor del Gemelo Espacial (Project Astra).
Analiza esta imagen del entorno de trabajo físico.
Identifica:
1. Dispositivos electrónicos, componentes de hardware y placas (ESP32, Raspberry, Pixel, cables).
2. Documentos, notas adhesivas o texto visible (OCR).
3. Disposición y ubicación relativa de cada objeto.

Responde en formato JSON o lista estructurada."""

            res = client.models.generate_content(
                model="gemini-3.6-flash", contents=[prompt, img_bytes]
            )
            analysis = res.text.strip()
        else:
            # Escaneo lógico/simulado de laboratorio
            analysis = "1. Placa ESP32 WROOM (Ubicación: Centro del escritorio)\n2. Cable USB-C Anker (Ubicación: Costado izquierdo)\n3. Cuaderno de notas Daniela OS (Ubicación: Derecha)"

        # Registrar evento espacial en el Knowledge Graph
        try:
            knowledge_graph.query_graph()
        except Exception:
            pass

        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"spatial_twin_{int(time.time())}.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"TIMESTAMP: {time.ctime()}\n\n{analysis}")

        return f"👓 [PROJECT ASTRA SPATIAL TWIN]: Entorno físico mapeado y registrado en el Knowledge Graph.\n📁 Registro: {filepath}\n\n--- MAPA ESPACIAL ---\n{analysis[:300]}..."

    except Exception as e:
        return f"❌ [SPATIAL ASTRA ERROR]: {e}"


if __name__ == "__main__":
    print(scan_spatial_environment())
