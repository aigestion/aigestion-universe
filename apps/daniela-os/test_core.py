import os

from dotenv import load_dotenv
from google.genai import types

from google import genai

load_dotenv(os.path.expanduser("~/.env"))
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


def test_daniela():
    print("🧪 Verificando motor de Inteligencia con Gemini 3.7 Flash...")
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(system_instruction="Eres Daniela, la IA de Daniela OS.")

    try:
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents="Hola Daniela, confirma tu modelo de IA activo.",
            config=config,
        )
        print(f"🤖 Respuesta recibida: {response.text}")
        print("✅ PRUEBA PASADA: Motor 3.7 operativo.")
    except Exception as e:
        print(f"⚠️ Error al probar 3.7: {e}")


test_daniela()
