import json
import subprocess
import time

from safe_exec import run_code


def activar_caja_negra():
    # 1. Feedback Háptico de Alerta (Doble pulso)
    run_code("termux-vibrate -d 150")
    time.sleep(0.1)
    run_code("termux-vibrate -d 150")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    print(f"\n[🚨] INICIANDO PROTOCOLO DE EMERGENCIA - {timestamp}")

    # 2. Captura de Geolocalización GPS
    try:
        loc_raw = subprocess.check_output(
            ["termux-location", "-p", "network", "-r", "once"], timeout=5
        ).decode("utf-8")
        loc_data = json.loads(loc_raw)
        lat = loc_data.get("latitude", 0)
        lon = loc_data.get("longitude", 0)
    except Exception:
        lat, lon = 0, 0

    print(f"📍 Coordenadas de Emergencia: {lat}, {lon}")

    # 3. Confirmación por Voz
    run_code(
        "termux-tts-speak -l es 'Protocolo de seguridad activado. Grabando y registrando posición.'"
    )
    # 4. Grabación Silenciosa de Audio (10 segundos)
    audio_file = f"emergencia_{timestamp}.mp3"
    print(f"🎙️ Grabando audio ambiental en: {audio_file}...")
    run_code(f"termux-microphone-record -l 10 -f {audio_file}")

    print("[✔] CAJA NEGRA COMPLETADA. Datos resguardados.")


if __name__ == "__main__":
    activar_caja_negra()
