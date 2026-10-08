import json
import os
import subprocess
import threading
import time

from safe_exec import run_code

# --- CONFIGURACIÓN ---
CONTACTO_EMERGENCIA = "+34600000000"  # <--- EDITA TU NÚMERO AQUÍ
# ---------------------


def luz_estroboscopica():
    """Parpadeo disuasorio de linterna."""
    for _ in range(20):
        run_code("termux-torch on")
        time.sleep(0.15)
        run_code("termux-torch off")
        time.sleep(0.15)
    run_code("termux-torch off")


def alarma_sonora():
    """Fuerza el volumen al máximo y emite tono de sirena táctico."""
    run_code("termux-volume music 15")
    # Genera un tono sintetizado agudo de sirena con TTS
    run_code(
        'termux-tts-speak -l es_ES -r 1.8 -p 1.5 "¡ALERTA DE EMERGENCIA! PROTOCOLO DE SEGURIDAD ACTIVADO."'
    )


def ejecutar_protocolo_sos():
    print("🚨 [CÓDIGO ROJO] Lanzando protocolo SOS completo...")

    # 1. Ejecutar disuasión visual y sonora en paralelo
    threading.Thread(target=luz_estroboscopica).start()
    threading.Thread(target=alarma_sonora).start()

    # 2. Grabación de evidencia en segundo plano (1 minuto de audio ambiental)
    ts = time.strftime("%Y%m%d_%H%M%S")
    archivo_audio = os.path.expanduser(f"~/daniela-os/evidencia_sos/sos_{ts}.wav")
    subprocess.Popen(
        ["termux-microphone-record", "-l", "60", "-f", archivo_audio],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"🎙️ Grabando evidencia de audio en {archivo_audio}...")

    # 3. Triangulación de coordenadas GPS
    try:
        raw_loc = subprocess.check_output(
            ["termux-location", "-p", "gps", "-r", "once"], stderr=subprocess.DEVNULL
        ).decode("utf-8")
        loc = json.loads(raw_loc)
        lat, lon = loc.get("latitude"), loc.get("longitude")
        maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        mensaje = f"🚨 EMERGENCIA SOS: Alejandro necesita ayuda. Ubicación actual: {maps_link}"
    except Exception:
        mensaje = "🚨 EMERGENCIA SOS: Alejandro necesita ayuda. No se pudo obtener la ubicación GPS actual."

    # 4. Envío de SMS táctico
    print(f"📲 Enviando señal de auxilio a {CONTACTO_EMERGENCIA}...")
    run_code(f'termux-sms-send -n {CONTACTO_EMERGENCIA} "{mensaje}"')

    # 5. Respuesta háptica
    run_code("termux-vibrate -d 1500")
    print("✅ Protocolo SOS ejecutado con éxito.")


if __name__ == "__main__":
    ejecutar_protocolo_sos()
