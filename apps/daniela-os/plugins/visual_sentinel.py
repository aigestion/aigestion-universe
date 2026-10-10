import subprocess
import os
import json
import time
from google import genai

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

BASE_DIR = os.path.expanduser("~/daniela-os")
BASE_IMG = os.path.join(BASE_DIR, "environment_base.jpg")
CURRENT_IMG = os.path.join(BASE_DIR, "environment_current.jpg")
VAULT_FILE = os.path.join(BASE_DIR, "memory_vault.json")

def trigger_tactical_alarm(message):
    # 1. Notificación Push en Android
    try:
        subprocess.run([
            'termux-notification',
            '--title', '🚨 [ALERTA VISUAL SENTINEL]',
            '--content', message,
            '--priority', 'high',
            '--sound'
        ], timeout=5)
    except Exception:
        pass

    # 2. Advertencia por Voz (TTS)
    try:
        subprocess.run([
            'termux-tts-speak',
            f"Atención. Alerta de seguridad. {message}"
        ], timeout=5)
    except Exception:
        pass

def capture_photo(target_path, camera_id="1"):
    if os.path.exists(target_path):
        try: os.remove(target_path)
        except Exception:
            pass
    
    cmd = ['termux-camera-photo', '-c', str(camera_id), target_path]
    process = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
    return process.returncode == 0 and os.path.exists(target_path)

def save_alert_to_vault(analysis_text):
    vault = []
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, 'r') as f:
                vault = json.load(f)
        except Exception:
            vault = []
    
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "visual_alert",
        "analysis": analysis_text
    }
    vault.append(entry)
    with open(VAULT_FILE, 'w') as f:
        json.dump(vault, f, indent=4)

def run(context):
    cmd = context.lower()

    if "base" in cmd or "set" in cmd:
        if capture_photo(BASE_IMG, camera_id="1"):
            return "📸 [VISUAL SENTINEL]: Fotografía base del entorno establecida con éxito."
        return "❌ [VISUAL SENTINEL]: Error al capturar la imagen base."

    if not os.path.exists(BASE_IMG):
        return "⚠️ [VISUAL SENTINEL]: Imagen base inexistente. Ejecuta 'visual_sentinel base' primero."

    if not capture_photo(CURRENT_IMG, camera_id="1"):
        return "❌ [VISUAL SENTINEL]: Error al tomar captura actual."

    try:
        base_file = client.files.upload(file=BASE_IMG)
        current_file = client.files.upload(file=CURRENT_IMG)
        
        prompt = (
            "Compara ambas imágenes. Determina si hay alteraciones físicas críticas, intrusos o personas no autorizadas. "
            "Responde iniciando con 'ANOMALIA_DETECTADA: ' seguido de un resumen corto de 1 frase si hay cambios importantes. "
            "Si no hay cambios relevantes, responde iniciando con 'ENTORNO_SEGURO: '."
        )
        
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=[base_file, current_file, prompt]
        )
        
        text = response.text.strip()

        if "ANOMALIA_DETECTADA" in text:
            summary = text.replace("ANOMALIA_DETECTADA:", "").strip()
            trigger_tactical_alarm(summary)
            save_alert_to_vault(text)
            return f"🚨 *[SENTINEL - ANOMALÍA DETECTADA]*\n\n{text}"
        else:
            return f"👁️ *[SENTINEL - ENTORNO ESTABLE]*\n\n{text}"

    except Exception as e:
        return f"❌ [VISUAL SENTINEL]: Error de análisis: {str(e)}"
