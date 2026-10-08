import time

import speech_recognition as sr
from safe_exec import run_cmd, run_code


def escuchar_centinela():
    r = sr.Recognizer()
    while True:
        # Graba ráfagas cortas para detectar la palabra "Daniela"
        run_cmd(["termux-microphone-record", "-f", "trigger.wav", "-l", "2"])
        time.sleep(2.2)
        run_cmd(["termux-microphone-record", "-q"])
        run_cmd(
            ["ffmpeg", "-i", "trigger.wav", "-ar", "16000", "-ac", "1", "trigger_clean.wav", "-y"]
        )

        try:
            with sr.AudioFile("trigger_clean.wav") as source:
                audio = r.record(source)
                texto = r.recognize_google(audio, language="es-ES").lower()
                if "daniela" in texto:
                    print("✅ ¡Activación detectada! Despertando sistema...")
                    run_code("python ~/daniela-os/conversar_daniela.py")
        except Exception:
            continue


if __name__ == "__main__":
    escuchar_centinela()
