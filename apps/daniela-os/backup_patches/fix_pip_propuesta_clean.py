filepath = "index.html"
with open(filepath, encoding="utf-8") as f:
    html = f.read()

pip_propuesta_js = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Buscar el área de display del PIP Master e inyectar el contenido
    const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
    if (area) {
        area.style.overflowY = 'auto';
        area.innerHTML = `
            <div style="padding:10px; color:#00ffcc; font-family:monospace; font-size:0.72rem; text-align:left; background:#08080a; height:100%; box-sizing:border-box;">
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
    }
});
</script>
"""

if "PROPUESTA SOVEREIGN v10.5" not in html:
    html = html.replace("</body>", pip_propuesta_js + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Inyección limpia aplicada sin alterar el backend.")
