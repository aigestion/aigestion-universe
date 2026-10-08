import os
import re

env_file = os.path.expanduser("~/daniela-os/.env")
app_file = os.path.expanduser("~/daniela-os/daniela_os.py")

if os.path.exists(env_file):
    with open(env_file, encoding="utf-8", errors="ignore") as f:
        env_content = f.read()

    match = re.search(r"AIzaSy[A-Za-z0-9_-]{35}", env_content)
    if match:
        key = match.group(0)
        with open(app_file, encoding="utf-8") as f:
            code = f.read()

        config_str = f'genai.configure(api_key="{key}")'
        if "genai.configure" in code:
            code = re.sub(r"genai\.configure\(.*?\)", config_str, code)
        else:
            code = code.replace(
                "import google.generativeai as genai",
                f"import google.generativeai as genai\n{config_str}",
            )

        with open(app_file, "w", encoding="utf-8") as f:
            f.write(code)

        print("✅ KEY GEMINI CONFIGURADA CORRECTAMENTE")
    else:
        print("❌ No se encontró el patrón AIzaSy en ~/daniela-os/.env")
else:
    print("❌ No existe el archivo ~/daniela-os/.env")
