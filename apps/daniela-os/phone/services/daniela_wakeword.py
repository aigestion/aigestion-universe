import os
import subprocess
import time

import requests
from daniela_stt_offline import transcribe_ram_audio

RAM_AUDIO_RAW = "/data/data/com.termux/files/usr/tmp/daniela_ram/input_raw.wav"
ROUTER_URL = "http://127.0.0.1:8001/api/hybrid/chat"


def listen_and_process(duration=4):
    os.makedirs(os.path.dirname(RAM_AUDIO_RAW), exist_ok=True)
    if os.path.exists(RAM_AUDIO_RAW):
        os.remove(RAM_AUDIO_RAW)

    # Indicar inicio de escucha con vibración breve
    subprocess.run(
        ["termux-vibrate", "-d", "60"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print("\n🎙️ Escuchando... (Habla tu comando para Daniela)")

    # Grabar a RAM
    subprocess.run(
        ["termux-microphone-record", "-f", RAM_AUDIO_RAW, "-l", str(duration)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(duration + 0.1)
    subprocess.run(
        ["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # Transcribir en local con Whisper.cpp
    text = transcribe_ram_audio()
    if not text or len(text.strip()) < 2:
        print("⚠️ No se detectó ninguna instrucción clara.")
        return

    print(f'🗣️ Dijiste: "{text}"')

    # Enviar consulta al Router Híbrido
    try:
        res = requests.post(ROUTER_URL, json={"prompt": text}, timeout=6.0)
        if res.status_code == 200:
            data = res.json()
            response_text = data.get("response", "Sin respuesta.")
            source = data.get("source", "Edge")

            print(f"[{source}] 🤖 Daniela: {response_text}")

            # Síntesis de Voz Asíncrona (TTS)
            subprocess.Popen(
                ["termux-tts-speak", "-l", "es", "-p", "1.1", response_text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception as e:
        print(f"❌ Error al comunicar con el router: {e}")


if __name__ == "__main__":
    listen_and_process()
