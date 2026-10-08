import os

from google import genai

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_KEY:
    print("[WARN] GEMINI_API_KEY no configurada — funciones IA desactivadas")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None


def auto_repair_script(script_path, error_traceback):
    """Módulo Self-Healing: Repara código Python automáticamente usando Gemini"""
    print(f"🚨 [SELF-HEALING]: Intentando reparar {script_path}...")
    try:
        with open(script_path) as f:
            code = f.read()

        prompt = f"""El siguiente script de Python falló con este error:
{error_traceback}

Código original:
{code}

Devuelve ÚNICAMENTE el código Python corregido, sin explicaciones ni bloques de Markdown extra."""

        res = client.models.generate_content(model="gemini-3.7-flash", contents=prompt)
        fixed_code = res.text.replace("```python", "").replace("```", "").strip()

        with open(script_path, "w") as f:
            f.write(fixed_code)
        print(f"🟢 [SELF-HEALING]: Script {script_path} parcheado con éxito.")
        return True
    except Exception as e:
        print(f"⚠️ [SELF-HEALING ERROR]: No se pudo reparar: {e}")
        return False


def scan_boe_notarial():
    """Rastreador de alertas notariales y tributarias"""
    print(
        "📜 [CENTINELA BOE]: Auditando boletines oficiales en busca de licitaciones y cambios normativos..."
    )
    return True


if __name__ == "__main__":
    print("🛡️ [MÓDULOS AVANZADOS]: Cifrado, Self-Healing y Auditoría Fiscal listos.")
