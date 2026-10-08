import os
import subprocess
import time

from google import genai


def audit_codebase(target_path: str = None) -> str:
    """Audita los cambios recientes de Git o un archivo objetivo en busca de deuda técnica y mejoras de arquitectura."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ [SOFTWARE ARCHITECT]: Se requiere GEMINI_API_KEY configurada."

    try:
        # Obtener diff o estado de git
        try:
            diff_output = subprocess.check_output(
                ["git", "diff", "HEAD~1"], cwd=os.path.expanduser("~/daniela-os"), text=True
            )[:3000]
        except Exception:
            diff_output = "No se pudo obtener git diff. Revisando archivos base."

        client = genai.Client(api_key=api_key)
        prompt = f"""Actúa como el Autonomous Software Architect de Daniela OS.
Revisa el siguiente código/cambios recientes en el repositorio:

{diff_output}

Realiza una evaluación técnica ejecutiva:
1. Deuda técnica y vulnerabilidades de seguridad detectadas.
2. Sugerencias de refactorización y optimización de rendimiento.
3. Score de Calidad de Código (0-100%).

Responde en formato Markdown estructurado."""

        res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        report = res.text.strip()

        # Guardar reporte de auditoría
        output_dir = os.path.expanduser("~/daniela-os/output")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"architect_audit_{int(time.time())}.md")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)

        return f"📐 [AUTONOMOUS SOFTWARE ARCHITECT]: Auditoría de código finalizada.\n📁 Reporte: {filepath}\n\n{report[:350]}..."

    except Exception as e:
        return f"❌ [SOFTWARE ARCHITECT ERROR]: {e}"


if __name__ == "__main__":
    print(audit_codebase())
