import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

# Contenido exacto a inyectar dentro del contenedor del PIP
propuesta_html = """<div id="pipDisplayArea" style="width:100%; height:100%; min-height:120px; background:#08080a; padding:8px; box-sizing:border-box; overflow-y:auto; color:#00ffcc; font-family:monospace; font-size:0.75rem;">
    <h4 style="color:#ff0055; margin:0 0 6px 0; font-size:0.8rem; border-bottom:1px solid #00ffcc; padding-bottom:2px;">⚡ PROPUESTA SOVEREIGN v10.5</h4>
    <p style="margin:2px 0; color:#ffb700;"><b>1. Self-Healing Ticker</b></p>
    <p style="margin:0 0 6px 0; color:#ccc; font-size:0.68rem;">Auto-mejora interactiva a 1-clic con prueba sandbox y Git Rollback.</p>

    <p style="margin:2px 0; color:#ffb700;"><b>2. Sovereign Glass HUD</b></p>
    <p style="margin:0 0 6px 0; color:#ccc; font-size:0.68rem;">Resplandor neón adaptativo al uso del procesador y pulso de estado.</p>

    <p style="margin:2px 0; color:#ffb700;"><b>3. Stealth OLED Mode</b></p>
    <p style="margin:0 0 6px 0; color:#ccc; font-size:0.68rem;">Negro puro (#000000) nocturno o batería &lt;20% para ahorro extremo.</p>

    <p style="margin:2px 0; color:#ffb700;"><b>4. Voice Morphing SSML</b></p>
    <p style="margin:0 0 6px 0; color:#ccc; font-size:0.68rem;">Prosodia táctica rápida para avisos y tono relajado en descansos.</p>
</div>"""

# Reemplazar el contenedor vacío
if 'id="pipDisplayArea"' in html:
    # Buscar el cierre del div original o reemplazar el bloque
    import re

    html = re.sub(r'<div id="pipDisplayArea"[^>]*>.*?</div>', propuesta_html, html, flags=re.DOTALL)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Marcado grabado directamente en el HTML del PIP Master.")
else:
    print("⚠️ No se encontró el contenedor id='pipDisplayArea' en la plantilla.")
