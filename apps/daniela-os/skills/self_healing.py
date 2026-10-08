import os
import re
import traceback

from skills.telemetry_logger import log_event

from google import genai


def auto_fix_exception(exception_obj: Exception, source_file: str = None) -> str:
    tb_str = "".join(
        traceback.format_exception(type(exception_obj), exception_obj, exception_obj.__traceback__)
    )
    if not source_file:
        match = re.search(r'File "([^"]+\.py)"', tb_str)
        source_file = match.group(1) if match else None

    # 1. Registrar intento en Sheets
    log_event("SELF-HEALING", f"Excepción detectada en {source_file}", "ATTEMPT")

    try:
        with open(source_file) as f:
            code_content = f.read()
    except Exception as e:
        return f"❌ [SELF-HEALING]: Error: {e}"

    api_key = os.environ.get("GEMINI_API_KEY")
    prompt = f"Corrige este error:\n{tb_str}\n\nCódigo:\n{code_content}"

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
    fixed_code = re.search(r"```python\s*(.*?)\s*```", response.text, re.DOTALL).group(1)

    with open(source_file, "w") as f:
        f.write(fixed_code)

    # 2. Registrar éxito en Sheets
    log_event("SELF-HEALING", f"Hot-patch aplicado exitosamente en {source_file}", "SUCCESS")
    return "🛠️ [SELF-HEALING]: Hot-patch aplicado."
