import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

# 1. Eliminar la llamada de prueba al vídeo de Youtube
if "test_pip_stream" in html:
    import re

    html = re.sub(r"<script>.*?test_pip_stream.*?</script>", "", html, flags=re.DOTALL)
    html = html.replace("<!-- test_pip_stream -->", "")

# 2. Resetear el contenedor del PIP Master a estado silencioso y listo
clean_pip_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
    if (area) {
        area.innerHTML = `
            <div id="pipMediaContainer" style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#08080a; border-radius:6px; overflow:hidden;">
                <div style="color:#00ffcc; font-family:monospace; font-size:0.75rem; text-align:center; padding:15px;">
                    🎬 <b style="color:#ff0055;">PIP MASTER MULTIMEDIA</b><br><br>
                    <span style="color:#aaa; font-size:0.68rem;">Esperando flujo multimedia...</span><br>
                    <span style="color:#ffb700; font-size:0.65rem;">[ NotebookLM Podcasts / Demos de Fuentes / Vídeos ]</span>
                </div>
            </div>
        `;
    }
});
</script>
"""

# Reemplazar e inyectar limpieza
if "fix_silence_pip" not in html:
    html = html.replace("</body>", clean_pip_script + "\n<!-- fix_silence_pip -->\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Música de prueba eliminada. PIP Master en silencio y listo.")
else:
    print("ℹ️ El PIP Master ya está limpio y silencioso.")
