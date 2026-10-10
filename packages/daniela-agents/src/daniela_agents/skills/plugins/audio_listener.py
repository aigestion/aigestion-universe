import os
import subprocess
import time
from google import genai

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

BASE_DIR = os.path.expanduser("~/daniela-os")
AUDIO_FILE = os.path.join(BASE_DIR, "audio_snap.wav")

def run(context):
    cmd = context.lower()
    
    # Extraer duración en segundos si se especifica (ej: "escucha 10" o "graba 5")
    duration = 5
    words = context.split()
    for word in words:
        if word.isdigit():
            duration = min(int(word), 30) # Límite de seguridad: 30 segundos
            break

    try:
        # Purga de grabación anterior si existe
        if os.path.exists(AUDIO_FILE):
            os.remove(AUDIO_FILE)

        # 1. Grabación con termux-microphone-record
        rec_cmd = ['termux-microphone-record', '-f', AUDIO_FILE, '-l', str(duration), '-e', 'wav']
        subprocess.run(rec_cmd, check=True)
        
        # Espera activa de seguridad durante el proceso de grabación
        time.sleep(duration + 0.5)

        # 2. Finalizar la grabación de forma limpia
        subprocess.run(['termux-microphone-record', '-q'], capture_output=True)

        if not os.path.exists(AUDIO_FILE) or os.path.getsize(AUDIO_FILE) == 0:
            return "❌ [AUDIO LISTENER]: No se pudo generar el archivo de audio. Verifica los permisos de micrófono en Termux:API."

        # 3. Procesamiento multimodal del audio con Gemini
        audio_file_uploaded = client.files.upload(file=AUDIO_FILE)
        
        prompt = (
            "Escucha con atención la siguiente grabación de audio. "
            "Proporciona una transcripción exacta de lo que se escucha "
            "y describe brevemente los sonidos de fondo o el tono del hablante."
        )

        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=[audio_file_uploaded, prompt]
        )

        # Limpieza del archivo subido en la nube
        try:
            client.files.delete(name=audio_file_uploaded.name)
        except Exception:
            pass

        return f"🎙️ *[AUDIO LISTENER - {duration}s]*\n\n{response.text}"

    except FileNotFoundError:
        return "❌ [AUDIO LISTENER]: No se encuentra 'termux-microphone-record'. Revisa que termux-api esté instalado."
    except Exception as e:
        # Asegurar detener el micrófono en caso de error
        subprocess.run(['termux-microphone-record', '-q'], capture_output=True)
        return f"❌ [AUDIO LISTENER]: Error en la captura/procesamiento: {str(e)}"
