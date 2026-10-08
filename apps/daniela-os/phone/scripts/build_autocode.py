import os

repo_dir = os.path.expanduser("~/aig-monorepo/pixela8/app/agents")

autocode_code = """#!/usr/bin/env python3
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
        system_prompt = (
            "Eres un ingeniero de software autónomo. "
            "Escribe un script en Python funcional y autocontenido. "
            "IMPORTANTE: Devuelve ÚNICAMENTE el código Python puro dentro de bloques ```python ... ```."
        )

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Crea {filename}: {task_description}"}
            ],
            "temperature": 0.1
        }

        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            if res.status_code != 200:
                return f"❌ Error OpenRouter HTTP {res.status_code}: {res.text}"

            raw_content = res.json()["choices"][0]["message"]["content"]
            if "```python" in raw_content:
                code_block = raw_content.split("```python")[1].split("```")[0].strip()
            elif "```" in raw_content:
                code_block = raw_content.split("```")[1].split("```")[0].strip()
            else:
                code_block = raw_content.strip()

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(code_block)
            os.chmod(target_path, 0o755)

            syntax_check = subprocess.run(["python3", "-m", "py_compile", target_path], capture_output=True, text=True)
            if syntax_check.returncode != 0:
                os.remove(target_path)
                return f"❌ Sandbox Fallido (Error de Sintaxis):\\n```\\n{syntax_check.stderr}\\n```"

            subprocess.run(["git", "-C", REPO_DIR, "add", target_path], check=True)
            commit_msg = f"✨ [Auto-Code Loop] {filename}"
            subprocess.run(["git", "-C", REPO_DIR, "commit", "-m", commit_msg], check=False)
            push_res = subprocess.run(["git", "-C", REPO_DIR, "push"], capture_output=True, text=True, check=False)

            if push_res.returncode == 0:
                return f"✅ **¡Auto-Coding exitoso!**\\n• Archivo: `pixela8/app/agents/{filename}`\\n• Validado y subido a GitHub."
            else:
                return f"⚠️ Código generado localmente, pero falló Git Push: {push_res.stderr}"

        except Exception as e:
            return f"❌ Excepción: {e}"
"""

with open(os.path.join(repo_dir, "agent_autocode.py"), "w", encoding="utf-8") as f:
    f.write(autocode_code)
os.chmod(os.path.join(repo_dir, "agent_autocode.py"), 0o755)

# Regenerar telegram_bot.py limpio
bot_path = os.path.join(repo_dir, "telegram_bot.py")
with open(bot_path, encoding="utf-8") as f:
    bot_content = f.read()

if "from agent_autocode import AutoCoderAgent" not in bot_content:
    bot_content = bot_content.replace(
        "from agent_coder import CoderAgent",
        "from agent_coder import CoderAgent\nfrom agent_autocode import AutoCoderAgent",
    )
    bot_content = bot_content.replace(
        "coder = CoderAgent()", "coder = CoderAgent()\nautocoder = AutoCoderAgent()"
    )

handler_str = """
async def autocode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = " ".join(context.args)
    if "|" not in args:
        await update.message.reply_text("⚠️ Uso: `/autocode archivo.py | descripcion` ")
        return
    parts = args.split("|", 1)
    filename = parts[0].strip()
    description = parts[1].strip()
    if not filename.endswith(".py"): filename += ".py"
    await update.message.reply_text(f"🧬 **Auto-Coding para `{filename}`...**")
    res = autocoder.generate_and_apply_code(description, filename)
    await update.message.reply_text(res, parse_mode="Markdown")
"""

if "def autocode_handler" not in bot_content:
    bot_content = bot_content.replace("def main():", f"{handler_str}\ndef main():")
    bot_content = bot_content.replace(
        'app.add_handler(CommandHandler("code", code_handler))',
        'app.add_handler(CommandHandler("code", code_handler))\n    app.add_handler(CommandHandler("autocode", autocode_handler))',
    )

with open(bot_path, "w", encoding="utf-8") as f:
    f.write(bot_content)

print("✨ [AUTOCODE BUILD] Módulos generados sin errores.")
