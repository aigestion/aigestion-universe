import os

bot_path = os.path.expanduser("~/aig-monorepo/pixela8/app/agents/telegram_bot.py")

code = """#!/usr/bin/env python3
import os, sys, time, subprocess, threading, tarfile, asyncio
from flask import Flask, request, jsonify

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)

from config import TELEGRAM_TOKEN
from agent_devops import DevOpsAgent
from agent_secretary import SecretaryAgent
from agent_coder import CoderAgent
from agent_autocode import AutoCoderAgent
from agent_worker import WorkerAgent
from agent_vision import VisionAgent

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

devops = DevOpsAgent()
secretary = SecretaryAgent()
coder = CoderAgent()
autocoder = AutoCoderAgent()
worker = WorkerAgent()
vision = VisionAgent()

BACKUP_PATH = os.path.expanduser("~/aig-monorepo/daniela_backup.tar.gz")
ROADMAP_PATH = os.path.expanduser("~/aig-monorepo/ROADMAP.md")

def speak(text: str):
    try:
        subprocess.run(["termux-tts-speak", text], check=False)
    except Exception:
        pass

flask_app = Flask(__name__)

@flask_app.route('/n8n-webhook', methods=['POST'])
def n8n_webhook():
    data = request.json or {}
    msg = data.get("message", "Evento n8n.")
    if data.get("speak", False):
        speak(msg)
    return jsonify({"status": "success", "received": msg}), 200

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🗺️ Roadmap", callback_data="btn_roadmap"), InlineKeyboardButton("⚡ Git Sync", callback_data="btn_sync")],
        [InlineKeyboardButton("🔋 Telemetría", callback_data="btn_health"), InlineKeyboardButton("📊 Procesos TOP", callback_data="btn_top")],
        [InlineKeyboardButton("📦 Backup DB", callback_data="btn_backup"), InlineKeyboardButton("📅 Briefing", callback_data="btn_briefing")]
    ]
    await update.message.reply_text(
        "🐝 **¡Daniela Swarm v9.0 + Visión OCR!**\\n\\n"
        "• `/code <pregunta>`\\n"
        "• `/autocode archivo.py | desc`\\n"
        "• `/sync` | `/health` | `/top`\\n"
        "• `/recuerda` | `/busca`\\n"
        "📷 *Mándame una foto para analizarla y extraer OCR.*",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("⚠️ Uso: `/code explica la clase RAG`")
        return
    await update.message.reply_text("💻 **Agente Coder consultando IA + RAG...**")
    res = coder.ask_code_assistant(prompt)
    await update.message.reply_text(f"💻 **Respuesta Coder:**\\n\\n{res[:3500]}")

async def autocode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = " ".join(context.args)
    if "|" not in args:
        await update.message.reply_text("⚠️ Uso: `/autocode script.py | descripcion` ")
        return
    parts = args.split("|", 1)
    filename = parts[0].strip()
    description = parts[1].strip()
    if not filename.endswith(".py"): filename += ".py"
    await update.message.reply_text(f"🧬 **Auto-Coding para `{filename}`...**")
    res = autocoder.generate_and_apply_code(description, filename)
    await update.message.reply_text(res, parse_mode="Markdown")

async def sync_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 **Iniciando Git Sync...**")
    res = devops.run_git_sync()
    speak("Sincronización Git realizada.")
    await update.message.reply_text(res)

async def health_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bat = devops.get_battery_status()
    await update.message.reply_text(f"📱 **TELEMETRÍA:**\\n• Batería: **{bat.get('percentage')}%** ({bat.get('status')})\\n• Temp: **{bat.get('temperature')}°C**")

async def top_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    output = devops.get_top_processes()
    await update.message.reply_text(f"📊 **Procesos Termux:**\\n```\\n{output}\\n```", parse_mode="Markdown")

async def recuerda_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("⚠️ Uso: `/recuerda Nota importante` ")
        return
    secretary.save_note("USER_NOTE", text)
    secretary.add_to_roadmap(text, user_name="Telegram_User")
    speak("Nota guardada.")
    await update.message.reply_text(f"🧠 **Secretario:** Nota guardada:\\n«{text}»")

async def busca_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("⚠️ Uso: `/busca nota` ")
        return
    results = secretary.search_note(query)
    if not results:
        await update.message.reply_text(f"🔍 Sin resultados para «{query}».")
        return
    msg = f"🔍 **Resultados:**\\n\\n" + "\\n".join([f"• **[{ts}]** {content}" for ts, content in results])
    await update.message.reply_text(msg)

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👁️ **Agente Visión descargando y analizando imagen...**")
    photo_file = await update.message.photo[-1].get_file()
    temp_img_path = os.path.expanduser("~/aig-monorepo/temp_vision.jpg")
    await photo_file.download_to_drive(temp_img_path)

    caption = update.message.caption or "Analiza esta imagen con detalle, extrae texto (OCR) y resume su contenido."
    res = vision.analyze_image(temp_img_path, prompt=caption)

    secretary.save_note("VISION_OCR", f"Análisis foto ({caption}): {res[:200]}...")
    await update.message.reply_text(f"👁️ **Análisis Visión:**\\n\\n{res}")
    if os.path.exists(temp_img_path):
        os.remove(temp_img_path)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "btn_sync":
        await query.edit_message_text("🔄 **Sincronizando...**")
        res = devops.run_git_sync()
        await query.edit_message_text(f"✅ {res}")
    elif query.data == "btn_top":
        output = devops.get_top_processes(limit=8)
        await query.edit_message_text(f"📊 **Procesos:**\\n```\\n{output}\\n```", parse_mode="Markdown")
    elif query.data == "btn_backup":
        await query.edit_message_text("📦 Usa `/backup` para recibir la base de datos.")
    elif query.data == "btn_health":
        bat = devops.get_battery_status()
        await query.edit_message_text(f"🔋 **Batería:** {bat.get('percentage')}% | 🌡️ **Temp:** {bat.get('temperature')}°C")
    elif query.data == "btn_briefing":
        speak("Swarm activo y listo.")
        await query.edit_message_text("📅 **Briefing:** Daniela Swarm + Visión operativa.")
    elif query.data == "btn_roadmap":
        if os.path.exists(ROADMAP_PATH):
            with open(ROADMAP_PATH, "r", encoding="utf-8") as f:
                await query.edit_message_text(f"🗺️ **ROADMAP:**\\n\\n{f.read()[:3500]}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_name = update.effective_user.first_name
    secretary.save_note("CHAT_LOG", f"{user_name}: {user_text}")
    await update.message.reply_text(f"🐝 **Daniela Swarm:** Tarea registrada:\\n📝 «{user_text}»")

def main():
    if not TELEGRAM_TOKEN:
        print("⚠️ Token no configurado.")
        return
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", start))
    app.add_handler(CommandHandler("code", code_handler))
    app.add_handler(CommandHandler("autocode", autocode_handler))
    app.add_handler(CommandHandler("sync", sync_handler))
    app.add_handler(CommandHandler("health", health_handler))
    app.add_handler(CommandHandler("top", top_handler))
    app.add_handler(CommandHandler("recuerda", recuerda_handler))
    app.add_handler(CommandHandler("busca", busca_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🐝 [Daniela Swarm v9.0 + Visión] ¡Desplegado!")
    app.run_polling()

if __name__ == "__main__":
    main()
"""

with open(bot_path, "w", encoding="utf-8") as f:
    f.write(code)

print("✨ [BOT UPDATE] telegram_bot.py escrito de forma limpia y completa.")
