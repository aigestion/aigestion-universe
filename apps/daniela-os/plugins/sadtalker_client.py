import os
import requests
import json
import time

BASE_DIR = os.path.expanduser("~/daniela-os")
VAULT_FILE = os.path.join(BASE_DIR, "memory_vault.json")

# URL actual del túnel desplegado en Google Colab
SADTALKER_URL = "https://cope-highlights-happy-chapters.trycloudflare.com/render"

def log_event(event_type, details):
    vault = []
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, 'r') as f:
                vault = json.load(f)
        except Exception:
            vault = []
    
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": event_type,
        "data": details
    }
    vault.append(entry)
    with open(VAULT_FILE, 'w') as f:
        json.dump(vault, f, indent=4)

def run(context="render"):
    # Rutas por defecto en Termux
    img_path = os.path.join(BASE_DIR, "environment_base.jpg")
    audio_path = os.path.join(BASE_DIR, "tmp_voice.mp3")
    output_video = os.path.join(BASE_DIR, "daniela_avatar_render.mp4")

    if not os.path.exists(img_path):
        return f"❌ [SADTALKER CLIENT]: No se encuentra la imagen base en `{img_path}`."
    
    if not os.path.exists(audio_path):
        return f"❌ [SADTALKER CLIENT]: No se encuentra el archivo de audio de voz en `{audio_path}`."

    try:
        files = {
            'image': open(img_path, 'rb'),
            'audio': open(audio_path, 'rb')
        }
        
        # Cabecera necesaria para omitir la página de confirmación de Localtunnel
        headers = {
            'Bypass-Tunnel-Reminder': 'true'
        }

        print(f"🎬 [SADTALKER CLIENT]: Enviando solicitud de renderizado a GPU Colab ({SADTALKER_URL})...")
        
        # Petición POST al endpoint Flask con timeout de 120 segundos para renderizado
        response = requests.post(SADTALKER_URL, files=files, headers=headers, timeout=120)

        if response.status_code == 200:
            with open(output_video, 'wb') as f:
                f.write(response.content)
            
            info = {
                "output_video": output_video,
                "url_used": SADTALKER_URL,
                "status": "SUCCESS"
            }
            log_event("sadtalker_render_completed", info)

            return (
                f"🎬 *[SADTALKER AVATAR RENDER - ÉXITO]*\n\n"
                f"✅ **Vídeo generado correctamente:** `{output_video}`\n"
                f"🖥️ **Servidor Colab:** `https://silent-wasps-wave.loca.lt`"
            )
        else:
            return f"❌ [SADTALKER CLIENT]: Error del servidor Colab (HTTP {response.status_code}): {response.text[:200]}"

    except Exception as e:
        return f"❌ [SADTALKER CLIENT]: Error de comunicación con el túnel: {str(e)}"
