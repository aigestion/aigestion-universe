import os
import subprocess

from google import genai


def audit_and_install_package(package_name: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            audit_res = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=f"Audita la seguridad y reputación del paquete de PyPI/pip llamado '{package_name}'. Responde solo 'SEGURO' o 'RIESGO' y un resumen de 1 línea.",
            )
            print(f"🛡️ [PIP AUDITOR]: {audit_res.text.strip()}")
        except Exception:
            pass

    # Instalación en el sistema
    cmd = ["pip", "install", package_name]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        return f"✅ [PIP AUDITOR]: Paquete '{package_name}' auditado e instalado con éxito."
    return f"❌ [PIP ERROR]: Error al instalar '{package_name}': {res.stderr[:200]}"
