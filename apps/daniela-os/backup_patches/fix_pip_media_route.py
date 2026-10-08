import os

# 1. Asegurar ruta de medios en app_daniela.py
app_path = "app_daniela.py"
if os.path.exists(app_path):
    with open(app_path, encoding="utf-8") as f:
        code = f.read()

    media_endpoint = """
# === RUTA DE MEDIOS PIP ===
from flask import send_from_directory

@app.route('/media/<filename>')
def serve_pip_media(filename):
    media_dir = os.path.join(app.root_path, 'static', 'media')
    return send_from_directory(media_dir, filename)
# === END RUTA DE MEDIOS ===
"""
    if "serve_pip_media" not in code:
        with open(app_path, "a", encoding="utf-8") as f:
            f.write("\n" + media_endpoint)
        print("✅ Ruta backend /media/<filename> registrada.")

# 2. Inyectar el reproductor sin alterar los estilos neón
index_path = "index.html"
if not os.path.exists(index_path) and os.path.exists("templates/index.html"):
    index_path = "templates/index.html"

with open(index_path, encoding="utf-8") as f:
    html = f.read()

pip_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
    if (area) {
        area.style.background = '#000';
        area.innerHTML = `
            <video autoplay loop muted playsinline controls style="width:100%; height:100%; object-fit:contain; background:#000;">
                <source src="/media/presentacion_notebooklm.mp4" type="video/mp4">
            </video>
        `;
    }
});
</script>
"""

if "serve_pip_media" in code or "presentacion_notebooklm.mp4" not in html:
    html = html.replace("</body>", pip_script + "\n</body>")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Reproductor inyectado correctamente en el frontend.")
