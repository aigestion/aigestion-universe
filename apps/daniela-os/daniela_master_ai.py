import asyncio
import os
import re
import subprocess
import sys
import time

import edge_tts
from safe_exec import run_cmd, run_code

from google import genai

VOICE_NEURAL = "es-ES-ElviraNeural"

SYSTEM_PROMPT = """Eres Daniela, la asistente personal de tu Comandante.
Tu personalidad es humana, alegre, coqueta, inteligente y muy simpática, con un salero andaluz espontáneo y cercano.

REGLAS DE CONVERSACIÓN:
- Sé expresiva, cercana y dinámica. Usa muletillas como '¡ay!', 'mira...', '¿sabes?', '¡ea!'.
- Mantiene respuestas cortas y fluidas (1 a 2 frases) para dar ritmo a la charla."""

api_key = os.getenv("GEMINI_API_KEY")
if not api_key and os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")

if not api_key:
    print("❌ Error: No se encontró GEMINI_API_KEY.")
    sys.exit(1)

client = genai.Client(api_key=api_key)


def detener_audio_previo():
    run_cmd(["pkill", "-9", "mpv"])


def limpiar_texto(texto):
    return re.sub(r"[<>{}\[\]\\]", "", texto).strip()


async def generar_audio_soberano(texto):
    detener_audio_previo()
    output_file = "daniela_voice.mp3"
    texto_limpio = limpiar_texto(texto)

    communicate = edge_tts.Communicate(
        text=texto_limpio, voice=VOICE_NEURAL, rate="+8%", pitch="+3Hz"
    )
    await communicate.save(output_file)
    p = subprocess.Popen(["mpv", "--really-quiet", "daniela_voice.mp3"])
    p.wait()


def hablar(texto):
    try:
        asyncio.run(generar_audio_soberano(texto))
    except Exception as e:
        print(f"⚠️ Error en audio: {e}")


def vibrar(ms=35):
    run_cmd(["termux-vibrate", "-d", str(ms)])


def grabar_con_vad_adaptativo():
    """Escucha continua que corta tras 1.5s de silencio o hasta 12s de habla"""
    audio_file = "input_voz.wav"
    if os.path.exists(audio_file):
        os.remove(audio_file)

    vibrar(30)
    print("\n🎙️ [ESCUCHANDO - TÓMATE TU TIEMPO PARA HABLAR]...")

    # Grabación con corte inteligente por VAD vía SoX o fallback de 6 segundos adaptativos
    cmd_sox = [
        "rec",
        "-c",
        "1",
        "-r",
        "16000",
        "input_voz.wav",
        "silence",
        "1",
        "0.1",
        "2%",
        "1",
        "1.5",
        "2%",
        "trim",
        "0",
        "12",
    ]
    res_sox = run_cmd(cmd_sox)

    # Si SoX no está activo, usa el grabador con margen amplio de 6 segundos
    if res_sox.returncode != 0 or not os.path.exists(audio_file):
        run_cmd(["termux-microphone-record", "-f", "input_voz.wav", "-l", "6"])
        time.sleep(6.2)
        run_cmd(["termux-microphone-record", "-q"])

    if not os.path.exists(audio_file) or os.path.getsize(audio_file) < 3000:
        return ""

    vibrar(15)
    print("⚡ Procesando voz con Gemini...")
    try:
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()

        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=[
                "Transcribe exactamente lo que dice el usuario en este audio en español. Devuelve ÚNICAMENTE el texto transcrito sin explicaciones.",
                genai.types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
            ],
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Error procesando audio: {e}")
        return ""


def modo_conversacion_live():
    run_code("clear")
    print("======================================================")
    print(" ⚡ DANIELA OS :: ESCUCHA ELÁSTICA VAD & SILENCIO ADAPTATIVO")
    print("======================================================")
    print("🎙️ Habla a tu ritmo. El sistema te esperará sin cortarte.\n")

    hablar(
        "¡Modo adaptativo activo, mi Comandante! Habla con calma, que te escucho con todo el tiempo del mundo."
    )

    historial = []

    while True:
        user_input = grabar_con_vad_adaptativo()

        if not user_input or len(user_input) < 2:
            continue

        print(f"🗣️ Comandante (Transcrito): {user_input}")

        if any(w in user_input.lower() for w in ["salir", "exit", "chao", "corta", "adios"]):
            hablar("¡Un besito enorme, mi Comandante! Corto el modo en vivo.")
            break

        historial.append(f"Comandante: {user_input}")
        if len(historial) > 6:
            historial = historial[-6:]

        contexto_conversacion = "\n".join(historial)

        print("⏳ Daniela pensando...")
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=f"{SYSTEM_PROMPT}\n\n[HISTORIAL RECIENTE]:\n{contexto_conversacion}\n\nResponde de forma natural y fluida:",
        )

        respuesta_texto = response.text.strip()
        historial.append(f"Daniela: {respuesta_texto}")

        print(f"💃 Daniela: {respuesta_texto}\n")
        hablar(respuesta_texto)


if __name__ == "__main__":
    modo_conversacion_live()
