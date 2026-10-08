import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

direct_pip_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        const area = document.getElementById('pipDisplayArea');
        if (!area) return;

        area.innerHTML = `
            <div style="padding:10px; color:#00ffcc; font-family:monospace; font-size:0.75rem; height:100%; overflow-y:auto; box-sizing:border-box; background:#08080a;">
                <h4 style="color:#ff0055; margin:0 0 8px 0; font-size:0.85rem; border-bottom:1px solid #00ffcc; padding-bottom:4px;">⚡ PROPUESTA SOVEREIGN v10.5</h4>
                <p style="margin:4px 0; color:#ffb700;"><b>1. Self-Healing Ticker</b></p>
                <p style="margin:0 0 8px 0; color:#ccc;">Auto-mejora interactiva a 1-clic con prueba sandbox y Git Rollback.</p>

                <p style="margin:4px 0; color:#ffb700;"><b>2. Sovereign Glass HUD</b></p>
                <p style="margin:0 0 8px 0; color:#ccc;">Resplandor neón adaptativo al uso del procesador y pulso de estado.</p>

                <p style="margin:4px 0; color:#ffb700;"><b>3. Stealth OLED Mode</b></p>
                <p style="margin:0 0 8px 0; color:#ccc;">Negro puro (#000000) nocturno o batería &lt;20% para ahorro extremo.</p>

                <p style="margin:4px 0; color:#ffb700;"><b>4. Voice Morphing SSML</b></p>
                <p style="margin:0 0 8px 0; color:#ccc;">Prosodia táctica rápida para avisos y tono relajado en descansos.</p>
            </div>
        `;
    }, 500);
});
</script>
"""

if "PROPUESTA SOVEREIGN v10.5" not in html:
    html = html.replace("</body>", direct_pip_script + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Presentación inyectada directamente en la pantalla del PIP Master.")
else:
    print("ℹ️ La presentación directa ya estaba en index.html.")
