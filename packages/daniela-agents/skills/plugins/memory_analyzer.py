import os
import json
from google import genai

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

BASE_DIR = os.path.expanduser("~/daniela-os")
VAULT_FILE = os.path.join(BASE_DIR, "memory_vault.json")

def run(context):
    if not os.path.exists(VAULT_FILE):
        return "🧠 [MEMORY ANALYZER]: La bóveda de memoria está vacía. No hay eventos para analizar."

    try:
        with open(VAULT_FILE, 'r') as f:
            vault_data = json.load(f)

        if not vault_data:
            return "🧠 [MEMORY ANALYZER]: Bóveda de memoria sin registros almacenados."

        # Tomar los últimos 15 eventos para optimización de tokens
        recent_events = vault_data[-15:]
        events_summary = json.dumps(recent_events, indent=2)

        prompt = (
            "Eres el núcleo analítico de Daniela OS. Analiza los siguientes registros "
            "de la bóveda de memoria (eventos, geolocalización, alertas) y proporciona "
            "un resumen ejecutivo sintetizado. Destaca patrones de movimiento, alertas de seguridad "
            "y sugerencias tácticas para el Comandante.\n\n"
            f"REGISTROS DE MEMORIA:\n{events_summary}"
        )

        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt
        )

        return f"🧠 *[REFLEXIÓN NEURONAL - ANÁLISIS DE BÓVEDA]*\n\n{response.text}"

    except Exception as e:
        return f"❌ [MEMORY ANALYZER]: Error al procesar memoria: {str(e)}"
