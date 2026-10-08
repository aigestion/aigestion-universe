import math
import os
import re
import subprocess
import time

import requests
from daniela_stt_offline import record_audio_clean, transcribe_ram_audio
from gtts import gTTS

ROUTER_URL = "http://127.0.0.1:8001/api/hybrid/chat"
RAM_AUDIO_TTS = "/data/data/com.termux/files/usr/tmp/daniela_ram/speech.mp3"
SHAKE_THRESHOLD = 16.0  # Umbral de aceleración G (Aceleración normal en reposo ≈ 9.8 m/s²)


def force_release_mic():
    try:
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


def trigger_voice_session():
    print("\n⚡ [GESTO ACTIVADO] Agitado detectado -> Escuchando a Daniela...", flush=True)
    subprocess.run(
        ["termux-vibrate", "-d", "120"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    if record_audio_clean(3.5):
        force_release_mic()
        raw_text = transcribe_ram_audio()
        if raw_text and len(raw_text.strip()) > 2:
            print(f'🗣️ Tú: "{raw_text}"', flush=True)
            try:
                res = requests.post(ROUTER_URL, json={"prompt": raw_text}, timeout=6.0)
                if res.status_code == 200:
                    resp = res.json().get("response", "")
                    print(f"🤖 Daniela: {resp}", flush=True)
                    speak_hd(resp)
            except Exception as e:
                print(f"❌ Error Router: {e}", flush=True)
        else:
            print("⚠️ No se detectó comando claro.", flush=True)
    force_release_mic()


def start_shake_listener():
    print("=" * 60, flush=True)
    print("📱 DANIELA OS - ACTIVACIÓN POR GESTO (REGEX STREAM)", flush=True)
    print("      Esperando sacudida del Pixel 8...", flush=True)
    print("=" * 60, flush=True)

    pkill_cmd = ["pkill", "-f", "termux-sensor"]
    subprocess.run(pkill_cmd, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    proc = subprocess.Popen(
        ["termux-sensor", "-s", "accelerometer", "-delay", "medium"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    last_shake = 0
    # Buscar patrones de tres flotantes seguidos dentro de "values": [x, y, z]
    val_pattern = re.compile(r"(-?\d+\.\d+),\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)")

    try:
        for line in iter(proc.stdout.readline, ""):
            match = val_pattern.search(line)
            if match:
                x, y, z = map(float, match.groups())
                mag = math.sqrt(x * x + y * y + z * z)
                now = time.time()
                if mag > SHAKE_THRESHOLD and (now - last_shake) > 3.5:
                    last_shake = now
                    trigger_voice_session()
    except Exception as e:
        print(f"❌ Error en stream: {e}", flush=True)
    finally:
        proc.terminate()


if __name__ == "__main__":
    start_shake_listener()
