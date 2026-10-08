import os
import sys


def speak_with_emotion(text, emotion="neutral"):
    if emotion == "urgent":
        pass
    elif emotion == "calm":
        pass

    cmd = f'python3 ~/apps/aig/phone/core/tts_hd.py "{text}"'
    os.system(cmd)
    return f"Sintetizado con emoción '{emotion}'."


if __name__ == "__main__":
    txt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Prueba de modulación emocional."
    speak_with_emotion(txt)
