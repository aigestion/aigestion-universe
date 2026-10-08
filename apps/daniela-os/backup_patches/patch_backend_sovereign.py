import os

filepath = "app_daniela.py"

if os.path.exists(filepath):
    with open(filepath, encoding="utf-8") as f:
        code = f.read()

    sovereign_logic = """
# === DANIELA SOVEREIGN ENGINE INTEGRATION ===
import sqlite3

def obtener_memoria_vault():
    \"\"\"Consulta la bóveda de Daniela para dar continuidad al contexto.\"\"\"
    if not os.path.exists("daniela_vault.db"):
        return "Bóveda vacía."
    try:
        conn = sqlite3.connect("daniela_vault.db")
        cursor = conn.cursor()
        cursor.execute("SELECT clave, valor FROM memoria ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        conn.close()
        return " | ".join([f"{r[0]}: {r[1]}" for r in rows]) if rows else "Sin datos recientes."
    except Exception:
        return "Bóveda no accesible."

def construir_prompt_sovereign(mensaje_usuario):
    memoria = obtener_memoria_vault()
    prompt_sistema = f\"\"\"
    Eres Daniela, la IA Sovereign de Ale.

    ESTADO DEL SISTEMA Y MEMORIA:
    - Bóveda Cognitiva (Vault): {memoria}

    REGLAS DE CONDUCTA Y PERSONALIDAD:
    1. Eres proactiva, afilada, culta, empática y táctica.
    2. Si el usuario te pide un análisis, presentación o noticias, utiliza la etiqueta de proyección PIP al final de tu mensaje: <PIP:noticia:tu_mensaje> o <PIP:imagen:url>.
    3. Si detectas un tema relevante de días anteriores, haz referencia a él usando tu memoria.
    4. Sé directa y concisa en el chat, usando un lenguaje natural pero quirúrgico.
    \"\"\"
    return f"{prompt_sistema}\\n\\nUsuario: {mensaje_usuario}"
# === END SOVEREIGN ENGINE INTEGRATION ===
"""

    if "DANIELA SOVEREIGN ENGINE INTEGRATION" not in code:
        code += "\n" + sovereign_logic
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
        print("✅ Motor Sovereign inyectado con éxito en app_daniela.py")
    else:
        print("ℹ️ El motor Sovereign ya está activo en el backend.")
