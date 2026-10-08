import json
import subprocess
import time

from safe_exec import run_code


def haptic_feedback(pattern="short"):
    """Vibración háptica según el contexto."""
    if pattern == "short":
        run_code("termux-vibrate -d 80")
    elif pattern == "alert":
        run_code("termux-vibrate -d 150")
        time.sleep(0.1)
        run_code("termux-vibrate -d 150")


def speak(text):
    """Síntesis de voz nativa en español."""
    haptic_feedback("short")
    # Limpiar comillas simples para evitar errores de consola
    clean_text = text.replace("'", "")
    run_code(f"termux-tts-speak -l es '{clean_text}'")


def check_zone(lat, lon):
    """Evalúa las coordenadas e identifica el entorno actual."""
    if lat == 0 and lon == 0:
        return "⚠️ Sin señal GPS", "desconocido"

    # Coordenadas Base (Tenerife / Tu ubicación actual)
    BASE_LAT, BASE_LON = 28.0309, -16.5945

    # Margen de aproximación de ~150 metros
    if abs(lat - BASE_LAT) < 0.0015 and abs(lon - BASE_LON) < 0.0015:
        return "📍 Base Táctica Principal (Home)", "home"
    else:
        return "🌐 Sector Externo / En Desplazamiento", "outdoors"


def get_telemetry():
    """Captura batería y coordenadas exactas vía Termux API."""
    telemetry = {}

    # Telemetría de Batería
    try:
        bat_raw = subprocess.check_output(["termux-battery-status"]).decode("utf-8")
        telemetry["battery"] = json.loads(bat_raw)
    except Exception:
        telemetry["battery"] = {"percentage": 0, "status": "UNKNOWN"}

    # Telemetría de Geolocalización
    try:
        loc_raw = subprocess.check_output(
            ["termux-location", "-p", "network", "-r", "once"], timeout=5
        ).decode("utf-8")
        telemetry["location"] = json.loads(loc_raw)
    except Exception:
        telemetry["location"] = {"latitude": 0, "longitude": 0}

    return telemetry


def run_daniela_mobile():
    data = get_telemetry()
    bat_pct = data["battery"].get("percentage", 100)
    lat = data["location"].get("latitude", 0)
    lon = data["location"].get("longitude", 0)

    zona_nombre, zona_id = check_zone(lat, lon)

    print("\n==========================================")
    print("      DANIELA OS - CONTEXTO MÓVIL         ")
    print("==========================================")
    print(f"🔋 Batería: {bat_pct}%")
    print(f"📍 Coordenadas: {lat}, {lon}")
    print(f"🛡️ Contexto Espacial: {zona_nombre}")
    print("==========================================\n")

    # Respuesta contextualizada según la zona y la batería
    if zona_id == "home":
        mensaje = f"Comandante Alejandro, reconozco el sector: Base Táctica Principal. Sistemas al {bat_pct} por ciento. Todo en orden."
    else:
        mensaje = f"Atención Alejandro, te encuentras en un Sector Externo. Batería al {bat_pct} por ciento. Mantengo la vigilancia activa."

    speak(mensaje)


if __name__ == "__main__":
    run_daniela_mobile()
