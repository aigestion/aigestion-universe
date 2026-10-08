import asyncio
import os

import edge_tts

AUDIO_OUTPUT = os.path.expanduser("~/daniela-os/speech.mp3")


async def _generate_audio(text, voice="es-ES-AlvaroNeural"):
    clean_text = text.replace("[ALERTA]", "").replace("[SILENCIO]", "")
    # Filtrar tags especiales de estado
    import re

    clean_text = re.sub(r"\[STATE:.*?\]", "", clean_text).strip()

    if not clean_text:
        return None

    communicate = edge_tts.Communicate(clean_text, voice)
    await communicate.save(AUDIO_OUTPUT)
    return AUDIO_OUTPUT


def generate_tts(text):
    """Interfaz síncrona para generar el archivo de voz."""
    try:
        return asyncio.run(_generate_audio(text))
    except Exception as e:
        print(f"Error generando TTS: {e}")
        return None
