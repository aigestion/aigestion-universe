import os
from google import genai

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

BASE_DIR = os.path.expanduser("~/daniela-os")

def run(context):
    # Extraer el nombre/ruta del archivo desde el comando
    target = context
    for prefix in ["analiza", "analizar", "lee", "leer", "file_analyzer", "cat"]:
        if target.lower().startswith(prefix):
            target = target[len(prefix):].strip()
            break

    if not target:
        return "❌ [FILE ANALYZER]: Indica qué archivo deseas analizar. Ejemplo: 'analiza app_daniela.py' o 'lee tasks.json'."

    # Resolver ruta (si es relativa, se asume dentro de ~/daniela-os)
    filepath = target if os.path.isabs(target) else os.path.join(BASE_DIR, target)

    if not os.path.exists(filepath):
        return f"❌ [FILE ANALYZER]: No se encontró el archivo en `{filepath}`."

    if os.path.isdir(filepath):
        # Si es un directorio, listar su contenido
        files = os.listdir(filepath)
        return f"📁 [FILE ANALYZER]: El objetivo es un directorio (`{target}`). Contenido ({len(files)} elementos):\n" + "\n".join([f"• {f}" for f in files[:15]])

    try:
        # Verificar tamaño para no saturar memoria (Límite: 500 KB para texto)
        size_kb = os.path.getsize(filepath) / 1024
        if size_kb > 500:
            return f"⚠️ [FILE ANALYZER]: El archivo pesa {size_kb:.1f} KB. Para evitar latencia, solo se analizan archivos menores a 500 KB."

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Si el archivo es corto, devolver fragmento + análisis corto
        prompt = (
            f"Analiza el siguiente archivo local ('{os.path.basename(filepath)}'). "
            f"Proporciona un resumen táctico de su propósito, componentes clave y si detectas algún error o mejora posible:\n\n"
            f"```\n{content[:4000]}\n```"
        )

        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt
        )

        return f"📂 [FILE ANALYZER - `{os.path.basename(filepath)}` ({size_kb:.1f} KB)]:\n\n{response.text}"

    except Exception as e:
        return f"❌ [FILE ANALYZER]: Error al procesar el archivo: {str(e)}"
