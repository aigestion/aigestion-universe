import asyncio
import os
import subprocess
import time

import edge_tts
import requests

# Voces HD por idioma
VOICES = {
    "es": "es-MX-DaliaNeural",
    "en": "en-US-AnaNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
}

RAM_DIR = "/data/data/com.termux/files/usr/tmp/daniela_ram"
RAW_M4A = os.path.join(RAM_DIR, "interpreter_mic.m4a")
RAM_AUDIO_WAV = os.path.join(RAM_DIR, "interpreter_input.wav")
TTS_OUTPUT = os.path.join(RAM_DIR, "interpreter_out.mp3")

WHISPER_BIN = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
MODEL_BASE = os.path.expanduser("~/whisper.cpp/models/ggml-base.bin")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")


async def speak_translation(text, target_lang):
    """Sintetiza y reproduce el texto traducido en el idioma destino."""
    voice = VOICES.get(target_lang, "en-US-AnaNeural")
    os.makedirs(RAM_DIR, exist_ok=True)
    communicate = edge_tts.Communicate(text, voice, rate="+5%")
    await communicate.save(TTS_OUTPUT)
    if os.path.exists(TTS_OUTPUT):
        os.system(f"mpv --no-terminal --really-quiet {TTS_OUTPUT} >/dev/null 2>&1")


def translate_text(text, source_lang, target_lang):
    """Traducción de alta calidad contextual usando OpenRouter / Gemini Flash."""
    prompt = (
        f"Eres un intérprete simultáneo profesional. Traduce el siguiente texto del idioma {source_lang} "
        f"al idioma {target_lang}. Devuelve ÚNICAMENTE la traducción directa sin notas ni comentarios.\n\nTexto: '{text}'"
    )

    if OPENROUTER_KEY:
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "google/gemini-2.5-flash:free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=3.0)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
    return text  # Fallback si no hay red


def record_audio(duration=4.0):
    """Captura el audio del micrófono con filtro de reducción de ruido."""
    os.makedirs(RAM_DIR, exist_ok=True)
    for f in [RAW_M4A, RAM_AUDIO_WAV]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    subprocess.run(
        ["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(0.1)
    subprocess.run(
        ["termux-microphone-record", "-f", RAW_M4A],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(duration)
    subprocess.run(
        ["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(0.1)

    if os.path.exists(RAW_M4A) and os.path.getsize(RAW_M4A) > 1000:
        dsp_filter = (
            "highpass=f=150,lowpass=f=3800,afftdn=nr=12,volume=2.5,speechnorm=e=3.0:r=0.00001:l=1"
        )
        cmd_conv = [
            "ffmpeg",
            "-y",
            "-i",
            RAW_M4A,
            "-af",
            dsp_filter,
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            RAM_AUDIO_WAV,
        ]
        subprocess.run(cmd_conv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(RAM_AUDIO_WAV)
    return False


def transcribe_audio():
    """Transcribe el audio usando Whisper detectando el idioma automáticamente."""
    if not os.path.exists(RAM_AUDIO_WAV):
        return None
    cmd_stt = [
        WHISPER_BIN,
        "-m",
        MODEL_BASE,
        "-f",
        RAM_AUDIO_WAV,
        "-t",
        "8",
        "-np",
        "-nt",
        "--auto-detect",
    ]
    try:
        res = subprocess.run(cmd_stt, capture_output=True, text=True, timeout=6.0)
        texto = res.stdout.strip()
        for unwanted in ["[BLANK_AUDIO]", "[MÚSICA]", "[NOISE]", "Subtítulos creados por"]:
            texto = texto.replace(unwanted, "")
        return texto.strip()
    except Exception:
        return None


def run_interpreter_session(lang_a="es", lang_b="en", rounds=1):
    """Ejecuta un ciclo de traducción bidireccional."""
    print(f"🌐 MODO INTÉRPRETE ACTIVO ({lang_a.upper()} ↔ {lang_b.upper()})")
    print("🎙️ Escuchando... ¡Habla ahora en cualquiera de los dos idiomas!")

    if record_audio(duration=4.0):
        texto_original = transcribe_audio()
        if texto_original and len(texto_original) > 2:
            print(f'\n🗣️ Escuchado: "{texto_original}"')

            # Detectar si el texto parece estar en español o inglés (lógica heurística / LLM)
            words_es = [
                "hola",
                "que",
                "como",
                "esta",
                "buenos",
                "dias",
                "sistema",
                "gracias",
                "por",
                "favor",
            ]
            if any(w in texto_original.lower() for w in words_es):
                source, target = lang_a, lang_b
            else:
                source, target = lang_b, lang_a

            print(f"🔄 Traduciendo de {source.upper()} -> {target.upper()}...")
            traduccion = translate_text(texto_original, source, target)
            print(f'🤖 Traducción: "{traduccion}"')

            # Reproducción de la traducción por voz HD
            asyncio.run(speak_translation(traduccion, target))
            return f"Traducción completada: {traduccion}"
        else:
            print("⚠️ No se detectaron palabras claras.")
    return "Error al capturar audio."


if __name__ == "__main__":
    run_interpreter_session()
