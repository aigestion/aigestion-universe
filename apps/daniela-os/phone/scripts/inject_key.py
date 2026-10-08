import os
import re

daniela_path = os.path.expanduser("~/apps/aig/daniela-os/daniela_os.py")
key = os.getenv("GEMINI_API_KEY", "")

with open(daniela_path, encoding="utf-8") as f:
    code = f.read()

config_line = f'genai.configure(api_key="{key}")'

if "genai.configure" in code:
    code = re.sub(r"genai\.configure\(.*?\)", config_line, code)
else:
    code = code.replace(
        "import google.generativeai as genai", f"import google.generativeai as genai\n{config_line}"
    )

with open(daniela_path, "w", encoding="utf-8") as f:
    f.write(code)

print("✅ Key AIzaSyAGTx... inyectada exitosamente en daniela_os.py")
