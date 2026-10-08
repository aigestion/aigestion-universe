import os

bot_path = os.path.expanduser("~/aig-monorepo/pixela8/app/agents/telegram_bot.py")

with open(bot_path, encoding="utf-8") as f:
    content = f.read()

# Añadir import si no está
if "from agent_voice import VoiceAgent" not in content:
    content = content.replace(
        "from agent_vision import VisionAgent",
        "from agent_vision import VisionAgent\nfrom agent_voice import VoiceAgent",
    )
    content = content.replace(
        "vision = VisionAgent()", "vision = VisionAgent()\nvoice = VoiceAgent()"
    )

# Añadir handler de voz si no está
voice_handler_code = """
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎙️ **Agente de Voz procesando audio...**")
    voice_file = await update.message.voice.get_file()
    temp_audio_path = os.path.expanduser("~/aig-monorepo/temp_voice.ogg")
    await voice_file.download_to_drive(temp_audio_path)

    res = voice.process_voice_note(temp_audio_path)
    secretary.save_note("VOICE_NOTE", "Nota de voz recibida y registrada.")
    secretary.add_to_roadmap("Nota de voz procesada en campo", user_name="Telegram_User")

    await update.message.reply_text(f"🎙️ **Resultado Voz:**\\n{res}")
    if os.path.exists(temp_audio_path):
        os.remove(temp_audio_path)
"""

if "def voice_handler" not in content:
    content = content.replace("def main():", f"{voice_handler_code}\ndef main():")
    content = content.replace(
        "app.add_handler(MessageHandler(filters.PHOTO, photo_handler))",
        "app.add_handler(MessageHandler(filters.PHOTO, photo_handler))\n    app.add_handler(MessageHandler(filters.VOICE, voice_handler))",
    )

with open(bot_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✨ telegram_bot.py actualizado con soporte para notas de voz.")
