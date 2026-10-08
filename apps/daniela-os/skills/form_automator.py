import json
import os
import time

from google import genai


def fill_form(target_url: str, form_data: dict) -> str:
    """Analiza un formulario y genera los comandos/pasos para rellenarlo con los datos provistos."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [FORM AUTOMATOR]: Se requiere GEMINI_API_KEY configurada."

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""Actúa como un agente de automatización de formularios web.
URL del formulario: {target_url}
Datos a rellenar: {json.dumps(form_data)}

Analiza la estructura del formulario (o simula la navegación) y:
1. Identifica los selectores CSS/IDs para cada campo.
2. Genera el script de llenado (JS / Playwright style).
3. Confirma la acción de 'submit'.

Responde en formato JSON estructurado con los pasos a seguir."""

        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        plan = res.text.strip()

        # Registro en el output
        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"form_fill_{int(time.time())}.json")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(plan)

        return f"📝 [WEB FORM AUTOMATOR]: Plan de automatización generado.\n🔗 URL: {target_url}\n📁 Plan guardado: {filepath}\n\n{plan[:500]}..."

    except Exception as e:
        return f"❌ [FORM AUTOMATOR ERROR]: {e}"


if __name__ == "__main__":
    print(
        fill_form(
            "https://aigestion.net/contacto", {"nombre": "Daniela", "email": "test@aigestion.net"}
        )
    )
