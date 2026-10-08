import subprocess


def speak_neural(text, whisper=False):
    # Ajustes finos de tono y velocidad para maximizar naturalidad en Termux TTS
    pitch = "0.8" if whisper else "1.0"
    rate = "0.85" if whisper else "1.05"

    cmd = ["termux-tts-speak", "-p", pitch, "-r", rate, "-l", "es-ES", text]
    subprocess.run(cmd, check=False)
    return f"🎙️ **VOZ NEURAL EXPRESIVA**: {text}"


if __name__ == "__main__":
    speak_neural("Hola Ale, esta es mi voz optimizada.")
