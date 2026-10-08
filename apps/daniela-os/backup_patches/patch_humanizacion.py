filepath = "app_daniela.py"
with open(filepath, encoding="utf-8") as f:
    code = f.read()

# Inyectamos el "Cerebro Humano"
human_prompt = """
# === NUEVA PERSONALIDAD DANIELA ===
# Reglas de voz humana:
# 1. Usa pausas naturales: Si dudas o procesas, responde con "... Déjame ver..." o "Un momento...".
# 2. Sé proactiva: Si son las 12:42 PM en Los Abrigos, salúdame con naturalidad.
# 3. Muestra opinión: "Esto me parece interesante", "Cuidado, este documento tiene errores", etc.
# 4. Formato de Voz (SSML): Si el mensaje es largo, usa <break time='500ms'/> para respirar entre párrafos.
# === END ===
"""

if "NUEVA PERSONALIDAD DANIELA" not in code:
    code = code.replace("Eres Daniela,", f"{human_prompt}\nEres Daniela,")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)
    print("✅ Daniela ahora posee 'humanidad' y conciencia de entorno.")
