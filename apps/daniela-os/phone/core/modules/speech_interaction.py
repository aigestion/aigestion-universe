import os
import sys

sys.path.append(os.path.expanduser("~/apps/aig/phone/core/modules"))
from google_voice import play_google_hd_voice

USER_NAME = "Ale"


def process_voice_greeting(user_input):
    clean_input = str(user_input).lower().strip()
    is_whisper = any(
        term in clean_input for term in ["susurro", "whisper", "callado", "despacio", "silencio"]
    )

    if "hola daniela" in clean_input or "daniela estas" in clean_input or "estas" in clean_input:
        if is_whisper:
            return play_google_hd_voice(
                f"Sí {USER_NAME}, estoy aquí... cuéntame.", whisper_mode=True
            )
        else:
            return play_google_hd_voice(
                f"Sí {USER_NAME}, estoy aquí, cuéntame.", whisper_mode=False
            )

    return play_google_hd_voice(f"Sí {USER_NAME}, te escucho.", whisper_mode=is_whisper)
