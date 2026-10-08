import os

from google import genai

key = os.environ.get("GEMINI_API_KEY", "")
if not key and os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "GEMINI_API_KEY" in line:
                key = line.split("=")[1].strip().strip('"').strip("'")

if not key:
    print("❌ No hay API Key cargada.")
    exit()

client = genai.Client(api_key=key)

print("🔍 Buscando modelos disponibles...")
try:
    for m in client.models.list():
        if "generateContent" in getattr(m, "supported_actions", []):
            print(f"✅ Modelo disponible: {m.name}")
except Exception as e:
    print(f"❌ Error al listar modelos: {e}")

print("\n🧪 Probando respuesta con gemini-2.0-flash...")
try:
    res = client.models.generate_content(
        model="gemini-2.0-flash", contents="Hola, respóndeme en una frase si me escuchas."
    )
    print(f"🔊 Respuesta recibida: {res.text.strip()}")
except Exception as e:
    print(f"⚠️ Falló gemini-2.0-flash: {e}")
    print("🧪 Probando con gemini-1.5-flash...")
    try:
        res = client.models.generate_content(
            model="gemini-1.5-flash", contents="Hola, respóndeme en una frase si me escuchas."
        )
        print(f"🔊 Respuesta recibida: {res.text.strip()}")
    except Exception as e2:
        print(f"❌ Falló también gemini-1.5-flash: {e2}")
