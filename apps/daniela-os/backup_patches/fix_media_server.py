import os

filepath = "app_daniela.py"
if os.path.exists(filepath):
    with open(filepath, encoding="utf-8") as f:
        code = f.read()

    media_route = """
# === SERVIDOR DE MEDIOS MULTIMEDIA (NOTEBOOKLM / PIP) ===
from flask import send_from_directory

# Crear carpeta de medios si no existe
os.makedirs("static/media", exist_ok=True)

@app.route('/media/<path:filename>')
def serve_media(filename):
    return send_from_directory('static/media', filename)
# === END SERVIDOR DE MEDIOS ===
"""

    if "SERVIDORES DE MEDIOS MULTIMEDIA" not in code and "/media/<path:filename>" not in code:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write("\n" + media_route)
        print("✅ Ruta /media registrada. Flask ya puede servir vídeos y podcasts.")
    else:
        print("ℹ️ La ruta /media ya estaba configurada.")
