import subprocess

def run(context):
    text = context
    for prefix in ["di", "habla", "tts", "speak"]:
        if text.lower().startswith(prefix):
            text = text[len(prefix):].strip()
            break
            
    if not text:
        return "❌ [TTS]: Indica qué quieres que diga. Ejemplo: 'di Hola Comandante'."

    try:
        # Añadido timeout de 5s para evitar bloqueos del sistema
        subprocess.run(['termux-tts-speak', text], timeout=12, capture_output=True)
        return f"🗣️ [TTS]: Mensaje enviado al sintetizador: '{text}'"
    except subprocess.TimeoutExpired:
        return "⚠️ [TTS]: El servicio de voz tardó demasiado y fue interrumpido para evitar bloqueos."
    except FileNotFoundError:
        return "❌ [TTS]: No se encuentra 'termux-tts-speak'. Asegúrate de tener instalada la Termux:API app."
    except Exception as e:
        return f"❌ [TTS]: Error - {str(e)}"
