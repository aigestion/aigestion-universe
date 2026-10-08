import os
import re
import subprocess
import time

WHISPER_BIN = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
MODEL_PATH = os.path.expanduser("~/whisper.cpp/models/ggml-base.bin")

RAM_RAW = "/data/data/com.termux/files/usr/tmp/daniela_ram/raw.m4a"
RAM_PCM = "/data/data/com.termux/files/usr/tmp/daniela_ram/input_16k.wav"


def record_audio_clean(duration=4.0) -> bool:
    """Captura de audio con normalización frecuencial para la voz humana."""
    os.makedirs(os.path.dirname(RAM_RAW), exist_ok=True)

    for f in [RAM_RAW, RAM_PCM]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    # Grabar con API de Android en formato m4a nativo
    subprocess.run(
        ["termux-microphone-record", "-f", RAM_RAW, "-l", str(int(duration))],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(duration + 0.2)
    subprocess.run(
        ["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(0.15)

    if not os.path.exists(RAM_RAW) or os.path.getsize(RAM_RAW) < 1200:
        return False

    # Filtro FFmpeg: Aumento de voz + Recorte de silencio + Limpieza de agudos/graves
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                RAM_RAW,
                "-af",
                "highpass=f=100,lowpass=f=3600,volume=2.5,silenceremove=start_periods=1:start_threshold=-32dB:start_silence=0.1",
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                RAM_PCM,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=4,
        )
        return os.path.exists(RAM_PCM) and os.path.getsize(RAM_PCM) > 800
    except Exception:
        return False


def clean_transcript(text: str) -> str:
    """Limpia la transcripción eliminando artefactos y alucinaciones comunes."""
    if not text:
        return ""

    # Eliminar corchetes, prefijos y caracteres raros
    text = re.sub(r"^[-\s]+", "", text)
    text = re.sub(r"\[.*?\]", "", text)
    text = text.strip()

    # Descartar respuestas típicas generadas en silencio total
    ghost_phrases = [
        "subtítulos",
        "continuará",
        "gracias por ver",
        "suscríbete",
        "amén",
        "vale la dime",
    ]
    if any(g in text.lower() for g in ghost_phrases) and len(text.split()) < 4:
        return ""

    return text


def transcribe_ram_audio() -> str:
    """Ejecuta inferencia exacta con la aceleración ARM del Tensor G3."""
    if (
        not os.path.exists(RAM_PCM)
        or not os.path.exists(WHISPER_BIN)
        or not os.path.exists(MODEL_PATH)
    ):
        return ""

    # Parámetros optimizados para español fluido y preciso
    cmd = [
        WHISPER_BIN,
        "-m",
        MODEL_PATH,
        "-f",
        RAM_PCM,
        "-l",
        "es",
        "-t",
        "6",
        "-nt",
        "--temperature",
        "0.0",
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        if res.returncode == 0:
            return clean_transcript(res.stdout.strip())
    except Exception:
        pass

    return ""


if __name__ == "__main__":
    print("🎙️ Probando captura mejorada...")
    subprocess.run(
        ["termux-vibrate", "-d", "80"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    if record_audio_clean(4.0):
        t = transcribe_ram_audio()
        print(f'🗣️ Transcripción: "{t}"')
    else:
        print("❌ Audio descartado por ser muy silencioso.")
