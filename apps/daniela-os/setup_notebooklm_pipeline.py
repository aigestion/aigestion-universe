import os
import re

# 1. Asegurar la ruta de medios y script generador en Flask
app_path = "app_daniela.py"
if os.path.exists(app_path):
    with open(app_path, encoding="utf-8") as f:
        code = f.read()

    pipeline_backend = """
# === ENGINE PIPELINE NOTEBOOKLM PIP ===
from flask import send_from_directory, jsonify
import subprocess

@app.route('/media/<path:filename>')
def serve_media_file(filename):
    media_dir = os.path.join(app.root_path, 'static', 'media')
    return send_from_directory(media_dir, filename)

@app.route('/check_video_status')
def check_video_status():
    target = os.path.join(app.root_path, 'static', 'media', 'presentacion_notebooklm.mp4')
    exists = os.path.exists(target) and os.path.getsize(target) > 0
    return jsonify({"ready": exists, "url": "/media/presentacion_notebooklm.mp4"})
# === END ENGINE PIPELINE ===
"""
    if "serve_media_file" not in code:
        with open(app_path, "a", encoding="utf-8") as f:
            f.write("\n" + pipeline_backend)
        print("✅ Backend de streaming y verificación /check_video_status registrado.")

# 2. Inyectar en index.html el contenedor de vídeo ajustado al PIP Master
index_path = "index.html"
if not os.path.exists(index_path) and os.path.exists("templates/index.html"):
    index_path = "templates/index.html"

with open(index_path, encoding="utf-8") as f:
    html = f.read()

pip_player_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
    if (!area) return;

    // Configuración visual estricta del PIP
    area.style.background = '#000000';
    area.style.overflow = 'hidden';
    area.style.display = 'flex';
    area.style.alignItems = 'center';
    area.style.justifyContent = 'center';

    function loadNotebookLMVideo() {
        fetch('/check_video_status')
            .then(res => res.json())
            .then(data => {
                if (data.ready) {
                    area.innerHTML = `
                        <div style="position:relative; width:100%; height:100%; background:#000;">
                            <video id="notebooklmVideo" autoplay loop muted playsinline controls style="width:100%; height:100%; object-fit:contain; border-radius:4px;">
                                <source src="${data.url}?t=${new Date().getTime()}" type="video/mp4">
                                Tu navegador no soporta el formato de vídeo.
                            </video>
                        </div>
                    `;
                } else {
                    area.innerHTML = `
                        <div style="padding:15px; text-align:center; color:#00ffcc; font-family:monospace; font-size:0.75rem;">
                            <div style="margin-bottom:8px; color:#ff0055;">⚙️ <b>PROCESANDO CON NOTEBOOKLM</b></div>
                            <div style="color:#aaa; font-size:0.68rem; margin-bottom:10px;">Sintetizando presentación y fuentes en vídeo...</div>
                            <div style="border:1px solid #00ffcc; height:6px; width:80%; margin:0 auto; background:#111; border-radius:3px; overflow:hidden;">
                                <div style="width:60%; height:100%; background:#00ffcc;"></div>
                            </div>
                        </div>
                    `;
                    setTimeout(loadNotebookLMVideo, 4000);
                }
            })
            .catch(() => {
                setTimeout(loadNotebookLMVideo, 5000);
            });
    }

    loadNotebookLMVideo();
});
</script>
"""

# Limpiar scripts conflictivos inyectados anteriormente
html = re.sub(r"<script>.*?presentacion_notebooklm.*?</script>", "", html, flags=re.DOTALL)

if "loadNotebookLMVideo" not in html:
    html = html.replace("</body>", pip_player_script + "\n</body>")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Visor e interfaz ajustados en el frontend.")
