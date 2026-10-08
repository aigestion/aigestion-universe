import os
import sqlite3
import subprocess

import requests

ENV_DB = os.path.expanduser("~/apps/aig/data/env.db")
AUDIO_CACHE = os.path.expanduser("~/daniela_voice.mp3")


def get_api_key():
    if os.path.exists(ENV_DB):
        try:
            conn = sqlite3.connect(ENV_DB)
            c = conn.cursor()
            c.execute(
                "SELECT value FROM env_vars WHERE key IN ('GEMINI_API_KEY', 'GOOGLE_API_KEY') LIMIT 1"
            )
            row = c.fetchone()
            conn.close()
            if row:
                return row[0]
        except Exception:
            pass
    return os.getenv("GOOGLE_API_KEY")


def play_google_hd_voice(text, whisper_mode=False):
    api_key = get_api_key()
    try:
        pitch = "-4st" if whisper_mode else "0st"
        speaking_rate = "0.85" if whisper_mode else "1.0"
        ssml_text = (
            f"<speak><prosody pitch='{pitch}' rate='{speaking_rate}'>{text}</prosody></speak>"
        )

        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
        payload = {
            "input": {"ssml": ssml_text},
            "voice": {"languageCode": "es-ES", "name": "es-ES-Wavenet-C", "ssmlGender": "FEMALE"},
            "audioConfig": {"audioEncoding": "MP3"},
        }
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code == 200:
            import base64

            audio_data = base64.b64decode(r.json()["audioContent"])
            with open(AUDIO_CACHE, "wb") as f:
                f.write(audio_data)
            subprocess.run(["mpv", "--really-quiet", AUDIO_CACHE], check=False)
            return f"🔊 **VOZ GOOGLE HD** ({'Susurro' if whisper_mode else 'Normal'}): {text}"
    except Exception:
        pass

    pitch_param = "0.7" if whisper_mode else "1.1"
    rate_param = "0.8" if whisper_mode else "1.0"
    subprocess.run(
        ["termux-tts-speak", "-p", pitch_param, "-r", rate_param, "-l", "es-ES", text], check=False
    )
    return f"🗣️ **VOZ LOCAL**: {text}"
