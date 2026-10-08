import os

repo_dir = os.path.expanduser("~/aig-monorepo/pixela8/app/agents")
bot_path = os.path.join(repo_dir, "telegram_bot.py")

with open(bot_path, encoding="utf-8") as f:
    content = f.read()

# Inyectar import del autocoder si no está
if "from agent_autocode import AutoCoderAgent" not in content:
    old_imp = "from agent_coder import CoderAgent"
    new_imp = "from agent_coder import CoderAgent\nfrom agent_autocode import AutoCoderAgent"
    content = content.replace(old_imp, new_imp)

    old_init = "coder = CoderAgent()"
    new_init = "coder = CoderAgent()\nautocoder = AutoCoderAgent()"
    content = content.replace(old_init, new_init)

# Inyectar el comando handler antes de main()
handler_code = """
async def autocode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = " ".join(context.args)
    if "|" not in args:
        await update.message.reply_text("⚠️ Uso correcto:\n`/autocode <nombre_archivo.py> | <descripción de lo que debe hacer>`")
        return

    parts = args.split("|", 1)
    filename = parts[0].strip()
    description = parts[1].strip()

    if not filename.endswith(".py"):
        filename += ".py"

    await update.message.reply_text(f"🧬 **Iniciando Auto-Coding Loop para `{filename}`...**\nLa IA está escribiendo y validando el código.")
    res = autocoder.generate_and_apply_code(description, filename)
    await update.message.reply_text(res, parse_mode="Markdown")
"""

if "def autocode_handler" not in content:
    content = content.replace("def main():", f"{handler_code}\ndef main():")

    # Añadir el command handler en main
    old_handler = 'app.add_handler(CommandHandler("code", code_handler))'
    new_handler = (
        f'{old_handler}\n    app.add_handler(CommandHandler("autocode", autocode_handler))'
    )
    content = content.replace(old_handler, new_handler)

with open(bot_path, "w", encoding="utf-8") as f:
    f.write(content)

print("🤖 telegram_bot.py actualizado con el bucle Auto-Code.")
