import os
import subprocess
import time

import requests
from daniela_stt_offline import record_audio_clean, transcribe_ram_audio
from gtts import gTTS

ROUTER_URL = "http://127.0.0.1:8001/api/hybrid/chat"
RAM_AUDIO_TTS = "/data/data/com.termux/files/usr/tmp/daniela_ram/speech.mp3"
WAKE_WORD = "daniela"


def force_release_mic():
    """Libera el micrófono de Android para evitar bloqueos del canal de audio."""
    try:
        subprocess.run(
            ["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


def speak_hd(text: str):
    """Sintetiza y reproduce la respuesta por el canal multimedia."""
    if not text:
        return
    clean_text = text.replace("[", "").replace("]", "").replace("*", "").strip()
    os.makedirs(os.path.dirname(RAM_AUDIO_TTS), exist_ok=True)

    try:
        force_release_mic()
        tts = gTTS(text=clean_text, lang="es", tld="es")
        tts.save(RAM_AUDIO_TTS)
        subprocess.run(
            ["mpv", "--no-terminal", "--ao=opensles", "--volume=130", RAM_AUDIO_TTS],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def process_command(raw_text: str):
    """Envia el comando extraído tras la Wake-Word al Router Edge 8001."""
    # Extraer el texto posterior a la palabra de activación
    lower_text = raw_text.lower()
    if WAKE_WORD in lower_text:
        command = lower_text.split(WAKE_WORD, 1)[1].strip()
    else:
        command = raw_text.strip()

    if not command or len(command) < 2:
        speak_hd("Dime, ¿en qué te puedo ayudar?")
        return

    print(f"\n🧠 Procesando comando: '{command}'...")
    try:
        res = requests.post(ROUTER_URL, json={"prompt": command}, timeout=6.0)
        if res.status_code == 200:
            data = res.json()
            response_text = data.get("response", "Sin respuesta.")
            source = data.get("source", "Edge")

            print(f"[{source}] 🤖 Daniela: {response_text}")
            speak_hd(response_text)
    except Exception as e:
        print(f"❌ Error al comunicar con el Router Edge: {e}")


def run_wake_word_daemon():
    print("=" * 60)
    print("🟢 DANIELA OS - DEMONIO DE ESCUCHA CONTINUA ACTIVADO (PIXEL 8)")
    print("      Escuchando en segundo plano la palabra: 'DANIELA'")
    print("=" * 60)

    while True:
        try:
            # Grabar búfer circular corto de 3 segundos en RAM
            if record_audio_clean(3.0):
                text = transcribe_ram_audio()
                force_release_mic()

                if text and WAKE_WORD in text.lower():
                    print(f"\n⚡ [WAKE-WORD DETECTADA]: '{text}'")
                    # Vibración háptica de confirmación de activación
                    subprocess.run(
                        ["termux-vibrate", "-d", "120"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )

                    # Procesar comando inmediato
                    process_command(text)
                    time.sleep(1.0)
            else:
                force_release_mic()
        except KeyboardInterrupt:
            print("\n🛑 Demonio detenido manualmente.")
            break
        except Exception:
            force_release_mic()
            time.sleep(1.0)


if __name__ == "__main__":
    run_wake_word_daemon()
