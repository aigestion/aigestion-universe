import importlib
import subprocess
import json
import os
from google import genai

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

BASE_DIR = os.path.expanduser("~/daniela-os")
SNAP_PATH = os.path.join(BASE_DIR, "security_snap.jpg")

def capture_photo(camera_id="1"):
    if os.path.exists(SNAP_PATH):
        try:
            os.remove(SNAP_PATH)
        except Exception:
            pass
        
    cmd = ['termux-camera-photo', '-c', str(camera_id), SNAP_PATH]
    subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if os.path.exists(SNAP_PATH) and os.path.getsize(SNAP_PATH) > 0:
        return True
    return False

def analyze_intruder():
    if not os.path.exists(SNAP_PATH):
        return "❌ No se capturó la imagen del intruso."

    try:
        uploaded_file = client.files.upload(file=SNAP_PATH)
        prompt = (
            "🚨 ALERTA DE SEGURIDAD: Revisa esta imagen tomada por la cámara frontal. "
            "¿Hay alguna persona visible? Describe quién aparece (rostro, expresión, ropa) "
            "o qué se observa en el entorno. Sé breve, preciso y táctico."
        )

        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=[uploaded_file, prompt]
        )

        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            pass

        return response.text
    except Exception as e:
        return f"Error en análisis de visión: {str(e)}"

def check_movement(threshold=2.5):
    try:
        res = subprocess.run(
            ['termux-sensor', '-n', '1', '-s', 'accelerometer'],
            capture_output=True, text=True, timeout=5
        )
        output = res.stdout.strip()
        if not output:
            return False
        
        data = json.loads(output)
        for sensor_name, values in data.items():
            if "accelerometer" in sensor_name.lower():
                val = values.get("values", [0, 0, 0])
                # Magnitud del vector de movimiento excluyendo la gravedad (~9.8)
                mag = (val[0]**2 + val[1]**2 + val[2]**2)**0.5
                delta = abs(mag - 9.8)
                return delta > threshold
        return False
    except Exception:
        return False

def run(context):
    cmd = context.lower()
    
    # 1. Modo captura inmediata manual (ej: "seguridad", "intruso", "foto_frontal")
    if "snap" in cmd or "foto" in cmd or "intruso" in cmd or context.strip() == "security_cam":
        if capture_photo(camera_id="1"):
            analysis = analyze_intruder()
            
            # Emitir notificación Push
            try:
                notifier = importlib.import_module('plugins.notifier')
                notifier.run("🚨 ALERTA INTRUSO | Captura realizada con cámara frontal")
            except Exception:
                pass

            return f"🥷 *[SENTINEL CAM - ALERTA DE CAPTURA]*\n\n{analysis}"
        else:
            return "❌ [SECURITY CAM]: Error al capturar imagen con la cámara frontal."

    # 2. Modo escaneo de movimiento
    if "scan" in cmd or "movimiento" in cmd:
        moved = check_movement()
        if moved:
            if capture_photo(camera_id="1"):
                analysis = analyze_intruder()
                return f"🚨 *[SENTINEL CAM - MOVIMIENTO DETECTADO]*\n\n{analysis}"
        return "🛡️ [SECURITY CAM]: Entorno estable. No se detectó movimiento anómalo."

    return "❌ [SECURITY CAM]: Comandante, usa 'seguridad foto' para capturar o 'seguridad scan' para verificar movimiento."
