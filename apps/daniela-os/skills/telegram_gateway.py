import asyncio
import os

import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_ID = os.environ.get("TELEGRAM_USER_ID", "")
LOCAL_API_URL = os.environ.get("LOCAL_API_URL", "http://localhost:8085/api/chat")


async def _query_daniela_async(message: str) -> str:
    """Consulta asíncrona no bloqueante hacia el core de Daniela OS."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(LOCAL_API_URL, json={"message": message})
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "🤖 Comando procesado sin salida.")
            else:
                return f"❌ Error en el core ({resp.status_code})."
    except Exception:
        return "⚠️ Error de conexión asíncrona con Daniela OS."


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Acceso denegado. ID no autorizado.")
        return
    await update.message.reply_text(
        f"🧠 Daniela Telegram Gateway v2.0 (Modo Asíncrono)\nID: {user_id}"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        return

    text = update.message.text
    # Respuesta inmediata / feedback mientras procesa
    msg = await update.message.reply_text("⏳ Procesando...")
    response_text = await _query_daniela_async(text)
    await msg.edit_text(response_text)


def start_telegram_bot():
    if not TELEGRAM_TOKEN:
        return "⚠️ [TELEGRAM 2.0]: No se encontró 'TELEGRAM_BOT_TOKEN' en el entorno."

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Iniciar loop en segundo plano sin colisionar
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(app.run_polling())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(app.run_polling())

    return "🚀 [TELEGRAM GATEWAY v2.0]: Bot asíncrono y optimizado en ejecución."


if __name__ == "__main__":
    print(start_telegram_bot())
