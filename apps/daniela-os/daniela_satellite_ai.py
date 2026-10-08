import asyncio
import os
import re
import sys

import edge_tts
from safe_exec import run_code

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

from safe_exec import run_bg, run_cmd


def detener_audio():
    run_cmd(["pkill", "-9", "mpv"])


def limpiar_texto(texto):
    return re.sub(r"[<>{}\[\]\\]", "", texto).strip()


async def generar_audio_soberano(texto):
    detener_audio()
    output_file = "daniela_voice.mp3"
    texto_limpio = limpiar_texto(texto)

    communicate = edge_tts.Communicate(
        text=texto_limpio, voice=VOICE_NEURAL, rate="+8%", pitch="+3Hz"
    )
    await communicate.save(output_file)
    run_bg(["mpv", "--really-quiet", "daniela_voice.mp3"])


def hablar(texto):
    try:
        asyncio.run(generar_audio_soberano(texto))
    except Exception as e:
        print(f"⚠️ Error audio: {e}")


def vibrar(ms=35):
    run_cmd(["termux-vibrate", "-d", str(ms)])


def iniciar_consola():
    run_code("clear")
    print("======================================================")
    print(" 💃 DANIELA OS :: MÓDULO HÍBRIDO ULTRA-ESTABLE ⚡")
    print("======================================================")
    print("💡 CONSEJO: Puedes pulsar el micrófono de tu teclado para dictarle libremente.")
    print("💬 Escribe tu mensaje o 'salir' para cerrar.\n")

    hablar(
        "¡Módulo estable activo, mi Comandante! Ahora me puedes escribir o dictar con el micrófono del teclado sin bloqueos. Dime qué necesitas, guapo."
    )
    vibrar()

    historial = []

    while True:
        try:
            user_input = input("\n🤖 Comandante > ").strip()

            if not user_input:
                detener_audio()
                continue

            if user_input.lower() in ["salir", "exit", "chao", "adios"]:
                detener_audio()
                hablar("¡Un besito enorme, mi Comandante! Quedo a tu verita.")
                break

            detener_audio()
            vibrar()

            historial.append(f"Comandante: {user_input}")
            if len(historial) > 6:
                historial = historial[-6:]

            contexto = "\n".join(historial)

            response = client.models.generate_content(
                model="gemini-3.7-flash",
                contents=f"{SYSTEM_PROMPT}\n\n[HISTORIAL RECIENTE]:\n{contexto}\n\nResponde al Comandante de forma natural:",
            )

            respuesta_texto = response.text.strip()
            historial.append(f"Daniela: {respuesta_texto}")

            print(f"\n💃 Daniela: {respuesta_texto}")
            hablar(respuesta_texto)

        except KeyboardInterrupt:
            detener_audio()
            print("\n👋 Desconectando de forma limpia...")
            break


if __name__ == "__main__":
    iniciar_consola()
