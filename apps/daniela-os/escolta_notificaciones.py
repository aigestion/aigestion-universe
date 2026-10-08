import json
import subprocess
import time

from safe_exec import run_code

# Apps prioritarias que Daniela te leerá al oído
APPS_IMPORTANTES = ["whatsapp", "telegram", "gmail", "messages", "signal"]


def check_bluetooth_audio():
    """Comprueba si hay auriculares Bluetooth conectados."""
    try:
        audio_info = subprocess.check_output(
            ["dumpsys", "audio"], stderr=subprocess.DEVNULL
        ).decode("utf-8")
        if "DEVICE_OUT_BLUETOOTH_A2DP" in audio_info or "bt_headset" in audio_info.lower():
            return True
    except Exception:
        pass
    return False


def leer_notificaciones_urgentes():
    if not check_bluetooth_audio():
        print("ℹ️ Sin auriculares Bluetooth. Lectura por voz omitida por privacidad.")
        return

    try:
        # Obtener notificaciones activas del sistema
        raw_notifs = subprocess.check_output(
            ["termux-notification-list"], stderr=subprocess.DEVNULL
        ).decode("utf-8")
        notificaciones = json.loads(raw_notifs)
    except Exception:
        print("⚠️ Asegúrate de haber dado permiso de lectura de notificaciones a Termux.")
        return

    for notif in notificaciones:
        app_pkg = notif.get("packageName", "").lower()
        title = notif.get("title", "")
        content = notif.get("content", "")

        # Verificar si la notificación pertenece a una app importante y tiene contenido
        if any(app in app_pkg for app in APPS_IMPORTANTES) and content:
            # Vibración corta de aviso en los cascos
            run_code("termux-vibrate -d 60")

            # Limpiar comillas para la síntesis de voz
            clean_title = title.replace("'", "")
            clean_content = content.replace("'", "")

            mensaje = f"Notificación de {clean_title}: {clean_content}"
            print(f"🎧 Leyendo al oído: {mensaje}")

            # Ajustar volumen multimedia y leer por voz al oído
            run_code("termux-volume music 8")
            run_code(f"termux-tts-speak -l es '{mensaje}'")

            # Pequeña pausa entre notificaciones
            time.sleep(1)


if __name__ == "__main__":
    leer_notificaciones_urgentes()
