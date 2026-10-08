import os
import re

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

# 1. Eliminar scripts de ondas/canvas previos
html = re.sub(r"<script>.*?pureVideoCanvas.*?</script>", "", html, flags=re.DOTALL)
html = html.replace("<!-- pure_video -->", "")

# 2. Inyectar reproductor de vídeo real HTML5
real_video_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
    if (!area) return;

    // Reproductor multimedia real con controles
    area.innerHTML = `
        <div style="width:100%; height:100%; background:#000; display:flex; flex-direction:column; justify-content:center; align-items:center; position:relative;">
            <video id="pipRealVideo" controls autoplay loop style="width:100%; height:100%; object-fit:contain; background:#000;">
                <source src="/media/presentacion_notebooklm.mp4" type="video/mp4">
                Tu navegador no soporta el formato de vídeo.
            </video>
            <div id="pipFallbackMessage" style="display:none; position:absolute; color:#ffb700; font-family:monospace; font-size:0.7rem; text-align:center; padding:10px; background:rgba(0,0,0,0.85); border:1px solid #ff0055; border-radius:4px;">
                ⚠️ <b>SIN ARCHIVO DE VÍDEO DETECTADO</b><br>
                Coloca tu vídeo en: <br><code style="color:#00ffcc;">static/media/presentacion_notebooklm.mp4</code>
            </div>
        </div>
    `;

    const vid = document.getElementById('pipRealVideo');
    if (vid) {
        vid.onerror = () => {
            document.getElementById('pipFallbackMessage').style.display = 'block';
        };
    }
});
</script>
"""

if "pipRealVideo" not in html:
    html = html.replace("</body>", real_video_script + "\n<!-- real_video -->\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ PIP Master actualizado con reproductor de vídeo real HTML5.")
