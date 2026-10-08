import os
import subprocess
import time

from daniela_stt_offline import transcribe_ram_audio

RAM_AUDIO_RAW = "/data/data/com.termux/files/usr/tmp/daniela_ram/input_raw.wav"


def test_live_stt(duration=3):
    os.makedirs(os.path.dirname(RAM_AUDIO_RAW), exist_ok=True)
    if os.path.exists(RAM_AUDIO_RAW):
        os.remove(RAM_AUDIO_RAW)

    print(f"\n🎙️ Grabando {duration} segundos en RAM... (¡HABLA AHORA!)")
    subprocess.run(
        ["termux-vibrate", "-d", "100"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # Grabación directa a RAM volátil
    subprocess.run(
        ["termux-microphone-record", "-f", RAM_AUDIO_RAW, "-l", str(duration)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(duration + 0.2)
    subprocess.run(
        ["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    if not os.path.exists(RAM_AUDIO_RAW):
        print("❌ Error: No se capturó audio desde el micrófono.")
        return

    size_kb = os.path.getsize(RAM_AUDIO_RAW) / 1024
    print(f"🟢 Audio RAW capturado en RAM: {size_kb:.1f} KB")

    print("⚡ Convirtiendo audio a PCM 16kHz e infiriendo con Whisper.cpp...")
    start = time.time()
    text = transcribe_ram_audio()
    elapsed = round((time.time() - start) * 1000, 1)

    print("--------------------------------------------------")
    print(f'🗣️ TRANSCRIPCIÓN DETECTADA: "{text}"')
    print(f"⏱️ Latencia de Inferencia: {elapsed} ms")
    print("--------------------------------------------------\n")


if __name__ == "__main__":
    test_live_stt()
