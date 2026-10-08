import os

from auto_agent import inspect_server_errors
from docs_engine import search_local_docs
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from google import genai
from tools import get_system_status

load_dotenv(os.path.expanduser("~/.env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Daniela OS // Canal Táctico Operativo.\nComandos: /estado, /errores, /busca [termino]"
    )


async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_system_status()
    await update.message.reply_text(
        f"📊 Estado:\nRAM: {status['ram_porcentaje']}\nBatería: {status['bateria']['porcentaje']}\nGit: {status['git']['commit']}"
    )


async def errores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log = inspect_server_errors()
    await update.message.reply_text(f"🔍 Diagnóstico:\n{log}")


async def busca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Uso: /busca <termino>")
        return
    res = search_local_docs(query)
    await update.message.reply_text(f"📑 Resultados:\n{res[:1000]}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=f"Eres Daniela OS. Responde al operador vía Telegram: {user_text}",
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")


if __name__ == "__main__":
    if TELEGRAM_TOKEN:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("estado", estado))
        app.add_handler(CommandHandler("errores", errores))
        app.add_handler(CommandHandler("busca", busca))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("🤖 Bot de Telegram actualizado...")
        app.run_polling()
