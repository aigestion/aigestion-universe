import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

pip_multimedia_engine = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Limpieza total de texto en el PIP
    const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
    if (area) {
        area.innerHTML = `
            <div id="pipMediaContainer" style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#000; border-radius:6px; overflow:hidden;">
                <div style="color:#00ffcc; font-family:monospace; font-size:0.75rem; text-align:center; padding:10px;">
                    🎬 <b>PIP MASTER MULTIMEDIA</b><br>
                    <span style="color:#666; font-size:0.65rem;">Esperando contenido visual o podcast de NotebookLM...</span>
                </div>
            </div>
        `;
    }

    // Función global para que Daniela proyecte VÍDEOS o PODCASTS
    window.proyectarMediaEnPIP = function(urlMedia, tipo = 'video') {
        const container = document.getElementById('pipMediaContainer');
        if (!container) return;

        if (tipo === 'video' || tipo === 'youtube') {
            const embedUrl = urlMedia.includes('youtube.com') ? urlMedia.replace('watch?v=', 'embed/') : urlMedia;
            container.innerHTML = `<iframe src="${embedUrl}?autoplay=1" style="width:100%; height:100%; border:none;" allow="autoplay"></iframe>`;
        } else if (tipo === 'audio' || tipo === 'podcast') {
            container.innerHTML = `
                <div style="padding:15px; text-align:center; width:100%;">
                    <div style="color:#ffb700; font-size:0.8rem; margin-bottom:10px;">🎙️ <b>PODCAST / NOTEBOOKLM AUDIONOTE</b></div>
                    <audio controls autoplay style="width:90%;">
                        <source src="${urlMedia}" type="audio/mpeg">
                        Tu navegador no soporta el reproductor de audio.
                    </audio>
                </div>
            `;
        }
    };
});
</script>
"""

if "proyectarMediaEnPIP" not in html:
    html = html.replace("</body>", pip_multimedia_engine + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ PIP Master configurado como Reproductor Multimedia HD.")
else:
    print("ℹ️ El reproductor multimedia ya está instalado.")
