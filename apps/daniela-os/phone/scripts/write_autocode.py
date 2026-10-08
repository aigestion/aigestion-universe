import os

path = os.path.expanduser("~/aig-monorepo/pixela8/app/agents/agent_autocode.py")

code = """#!/usr/bin/env python3
import os, subprocess, requests

try:
    from config import OPENROUTER_API_KEY
except ImportError:
    OPENROUTER_API_KEY = ""

REPO_DIR = os.path.expanduser("~/aig-monorepo")
AGENTS_DIR = os.path.join(REPO_DIR, "pixela8/app/agents")

class AutoCoderAgent:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def generate_and_apply_code(self, task_description: str, filename: str):
        if not self.api_key:
            return "❌ Error: OpenRouter API Key no configurada."

        target_path = os.path.join(AGENTS_DIR, filename)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": "Escribe codigo Python puro en bloques ```python ... ```"},
                {"role": "user", "content": f"Crea {filename}: {task_description}"}
            ],
            "temperature": 0.1
        }

        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            raw = res.json()["choices"][0]["message"]["content"]
            code = raw.split("```python")[1].split("```")[0].strip() if "```python" in raw else raw.strip()

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(code)
            os.chmod(target_path, 0o755)

            chk = subprocess.run(["python3", "-m", "py_compile", target_path], capture_output=True, text=True)
            if chk.returncode != 0:
                os.remove(target_path)
                return f"❌ Error de Sintaxis:\\n```\\n{chk.stderr}\\n```"

            subprocess.run(["git", "-C", REPO_DIR, "add", target_path], check=True)
            subprocess.run(["git", "-C", REPO_DIR, "commit", "-m", f"✨ [Auto-Code] {filename}"], check=False)
            push = subprocess.run(["git", "-C", REPO_DIR, "push"], capture_output=True, text=True, check=False)

            if push.returncode == 0:
                return f"✅ **¡Auto-Coding exitoso!**\\n• Creado: `{filename}` y subido a GitHub."
            return f"⚠️ Creado localmente pero falló el Git Push."

        except Exception as e:
            return f"❌ Error: {e}"
"""

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

os.chmod(path, 0o755)
print("✨ [Auto-Code Agent] Escrito de forma segura y sin conflictos de Bash.")
