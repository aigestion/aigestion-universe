import os
import subprocess

import requests
from daniela_stt_offline import record_audio_clean, transcribe_ram_audio
from gtts import gTTS

ROUTER_URL = "http://127.0.0.1:8001/api/hybrid/chat"
RAM_AUDIO_TTS = "/data/data/com.termux/files/usr/tmp/daniela_ram/speech.mp3"


def silence_daniela_immediately():
    """Detiene cualquier audio de Daniela inmediatamente si está hablando."""
    try:
        subprocess.run(
            ["pkill", "-9", "-f", "mpv"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        subprocess.run(
            ["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


def speak_hd(text: str):
    if not text:
        return
    clean_text = text.replace("[", "").replace("]", "").replace("*", "").strip()
    os.makedirs(os.path.dirname(RAM_AUDIO_TTS), exist_ok=True)
    try:
        silence_daniela_immediately()
        tts = gTTS(text=clean_text, lang="es", tld="es")
        tts.save(RAM_AUDIO_TTS)
        subprocess.run(
            ["mpv", "--no-terminal", "--ao=opensles", "--volume=130", RAM_AUDIO_TTS],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def run_duplex_session():
    # INTERRUPCIÓN INMEDIATA: Si Daniela está hablando, se calla al instante
    silence_daniela_immediately()

    print("=" * 50)
    print("🤖 DANIELA OS - MODO CONVERSACIONAL HD (PIXEL 8)")
    print("=" * 50)

    # Vibración corta de confirmación de corte y nueva escucha
    subprocess.run(
        ["termux-vibrate", "-d", "100"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print("🎙️ Escuchando... (Habla claro a tu Pixel 8)")

    if record_audio_clean(4.5):
        silence_daniela_immediately()
        raw_text = transcribe_ram_audio()
        if raw_text and len(raw_text.strip()) > 2:
            print(f'\n🗣️ Tú: "{raw_text}"')
            try:
                res = requests.post(ROUTER_URL, json={"prompt": raw_text}, timeout=10.0)
                if res.status_code == 200:
                    resp_data = res.json()
                    resp = resp_data.get("response", "")
                    src = resp_data.get("source", "")
                    print(f"\n[{src}] 🤖 Daniela: {resp}\n")
                    speak_hd(resp)
            except Exception as e:
                print(f"❌ Error Router: {e}")
        else:
            print("⚠️ No se detectó un comando claro de voz.")
    else:
        print("❌ Error al capturar audio del micrófono.")
    silence_daniela_immediately()


if __name__ == "__main__":
    run_duplex_session()
