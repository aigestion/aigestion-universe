import os
import re
import signal
import sys
import time

import requests
import speech_recognition as sr
from google.genai import types
from safe_exec import run_cmd, run_code

from google import genai


def forzar_salida(sig, frame):
    run_cmd(["killall", "-9", "mpv", "termux-microphone-record"])
    sys.exit(0)


signal.signal(signal.SIGINT, forzar_salida)

key = os.environ.get("GEMINI_API_KEY", "")
if not key and os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "GEMINI_API_KEY" in line:
                key = line.split("=")[1].strip().strip('"').strip("'")
client = genai.Client(api_key=key)

# Historial de contexto conversacional
historial = []

SYSTEM_INSTRUCTION = """
Eres Daniela, la asistente IA táctica personal de Ale.
- Háblale a Ale directamente por su nombre ("Ale").
- Ale está en Los Abrigos, Tenerife.
- Mantienes el contexto de la conversación. Sé fluida, profesional, concisa y rápida.
- Sin emojis ni caracteres especiales. Responde en 1 o 2 frases.
"""


def obtener_precio(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=3).json()
        price = res["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return f"{ticker}: {price} USD"
    except Exception:
        return None


def hablar(texto):
    texto_limpio = re.sub(r"[^\w\sáéíóúÁÉÍÓÚñÑ,.\?!]", "", texto)
    print(f"\n🔊 Daniela: {texto_limpio}")
    run_cmd(
        [
            "edge-tts",
            "--voice",
            "es-ES-ElviraNeural",
            "--text",
            texto_limpio,
            "--write-media",
            "resp.mp3",
        ]
    )
    run_cmd(["mpv", "--no-video", "--ao=opensles", "--volume=200", "resp.mp3"])


def escuchar_adaptativo(tiempo_maximo=12):
    """Graba audio dinámicamente y corta rápido si hay silencio"""
    for f in ["cmd.wav", "cmd_clean.wav"]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass

    # Grabación con ráfaga flexible
    run_cmd(["termux-microphone-record", "-f", "cmd.wav", "-l", str(tiempo_maximo)])

    r = sr.Recognizer()
    r.pause_threshold = 1.2  # Corta la grabación 1.2s después de que te calles

    # Espera activa y conversión limpia
    time.sleep(4.5)
    run_cmd(["termux-microphone-record", "-q"])
    run_cmd(["ffmpeg", "-i", "cmd.wav", "-ar", "16000", "-ac", "1", "cmd_clean.wav", "-y"])

    try:
        with sr.AudioFile("cmd_clean.wav") as source:
            # Ajuste dinámico del ruido ambiental
            r.adjust_for_ambient_noise(source, duration=0.3)
            audio = r.record(source)
            texto = r.recognize_google(audio, language="es-ES").lower()
            return texto
    except Exception:
        return ""


def consultar_gemini(orden):
    global historial

    # Detección de bolsa automática
    datos_extra = []
    if "palantir" in orden:
        datos_extra.append(obtener_precio("PLTR"))
    elif "apple" in orden:
        datos_extra.append(obtener_precio("AAPL"))
    elif "tesla" in orden:
        datos_extra.append(obtener_precio("TSLA"))
    elif "nvidia" in orden:
        datos_extra.append(obtener_precio("NVDA"))

    info_financiera = " | ".join([d for d in datos_extra if d])

    # Mantener el contexto corto (últimas 8 entradas)
    if len(historial) > 8:
        historial = historial[-8:]

    contexto_str = "\n".join(historial)

    prompt = f"""
[ESTADO Y DATOS TÁCTICOS]
Ubicación: Los Abrigos, Tenerife.
Hora: {time.strftime("%H:%M")}
Datos del entorno: {info_financiera if info_financiera else "N/A"}

[HISTORIAL RECIENTE]
{contexto_str}

[ORDEN DE ALE]
Ale: {orden}
"""
    try:
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
        )
        respuesta = response.text.strip()

        # Guardar en la memoria corta
        historial.append(f"Ale: {orden}")
        historial.append(f"Daniela: {respuesta}")

        return respuesta
    except Exception as e:
        return f"Tropiezo táctico: {e}"


# --- BUCLE DE CONTROL ---
run_code("clear")
print("==================================================")
print("🤖 DANIELA OS - ADAPTIVE VOICE & CONTEXT ENGINE")
print("==================================================")
hablar("Sistema adaptativo listo. Puedes hablar con naturalidad, Ale.")

while True:
    orden = escuchar_adaptativo(tiempo_maximo=10)
    if orden:
        print(f'🗣️ Ale: "{orden}"')
        if any(p in orden for p in ["adiós", "hasta luego", "descansa"]):
            hablar("Hasta pronto, Ale.")
            break

        respuesta = consultar_gemini(orden)
        hablar(respuesta)
