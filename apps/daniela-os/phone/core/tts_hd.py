import asyncio
import os
import sys

import edge_tts

# Voz de España (Elvira Neural)
VOICE = "es-ES-ElviraNeural"  # Opción masculina alternativa de España: "es-ES-AlvaroNeural"
RAM_DIR = "/data/data/com.termux/files/usr/tmp/daniela_ram"
OUTPUT_FILE = os.path.join(RAM_DIR, "daniela_hd.mp3")


async def generate_speech(text):
    os.makedirs(RAM_DIR, exist_ok=True)
    communicate = edge_tts.Communicate(text, VOICE, rate="+12%", pitch="+1Hz")
    await communicate.save(OUTPUT_FILE)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        try:
            asyncio.run(generate_speech(text))
            if os.path.exists(OUTPUT_FILE):
                os.system(
                    f"mpv --no-terminal --really-quiet {OUTPUT_FILE} || termux-media-player play {OUTPUT_FILE}"
                )
        except Exception:
            escaped_text = text.replace('"', '\\"')
            os.system(f'termux-tts-speak "{escaped_text}"')
