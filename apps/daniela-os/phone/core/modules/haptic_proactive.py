import subprocess
import time


def trigger_vibration(severity="info"):
    try:
        if severity == "critical":
            subprocess.run(["termux-vibrate", "-d", "300", "-f"], check=False)
            time.sleep(0.15)
            subprocess.run(["termux-vibrate", "-d", "300", "-f"], check=False)
        else:
            subprocess.run(["termux-vibrate", "-d", "400"], check=False)
    except Exception:
        pass


def notify_user_proactively(message, severity="info"):
    trigger_vibration(severity)
    subprocess.run(["termux-tts-speak", "Hola Ale. " + str(message)], check=False)
    return "📳 Transmisión háptica y vocal enviada."
