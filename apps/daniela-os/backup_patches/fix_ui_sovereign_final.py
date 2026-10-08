import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

ui_fix_script = """
<style>
/* Contenedor relativo sobre la imagen de Daniela */
.daniela-img-container {
    position: relative;
    width: 100%;
    display: block;
}

/* Ticker translúcido encima de la imagen */
#ticker-overlay-daniela {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    background: rgba(8, 8, 10, 0.85);
    border-top: 1px solid #00ffcc;
    border-bottom: 1px solid #00ffcc;
    overflow: hidden;
    padding: 6px 0;
    z-index: 20;
    box-sizing: border-box;
}

#ticker-text-daniela {
    display: inline-block;
    white-space: nowrap;
    color: #00ffcc;
    font-family: monospace;
    font-size: 0.78rem;
    animation: marquee-daniela 18s linear infinite;
}

@keyframes marquee-daniela {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
</style>

<script>
document.addEventListener('DOMContentLoaded', () => {
    // 1. LIMPIEZA Y PRESENTACIÓN EN PIP MASTER
    const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
    if (area) {
        area.innerHTML = `
            <div style="padding:10px; color:#00ffcc; font-family:monospace; font-size:0.7rem; height:100%; box-sizing:border-box; overflow-y:auto; background:#08080a; text-align:left;">
                <div style="color:#ff0055; font-weight:bold; font-size:0.8rem; border-bottom:1px solid #00ffcc; padding-bottom:3px; margin-bottom:6px;">⚡ PROPUESTA SOVEREIGN v10.5</div>

                <div style="background:#111318; border:1px solid #00ffcc; padding:5px; margin-bottom:5px; border-radius:3px;">
                    <b style="color:#ffb700;">1. Self-Healing Ticker</b><br>
                    <span style="color:#ccc;">Auto-mejora a 1-clic en Sandbox con Git Rollback.</span>
                </div>

                <div style="background:#111318; border:1px solid #00ffcc; padding:5px; margin-bottom:5px; border-radius:3px;">
                    <b style="color:#ffb700;">2. Sovereign Glass HUD</b><br>
                    <span style="color:#ccc;">Resplandor adaptativo según uso de procesador.</span>
                </div>

                <div style="background:#111318; border:1px solid #00ffcc; padding:5px; margin-bottom:5px; border-radius:3px;">
                    <b style="color:#ffb700;">3. Stealth OLED Mode</b><br>
                    <span style="color:#ccc;">Negro puro (#000000) si batería &lt;20% o noche.</span>
                </div>

                <div style="background:#111318; border:1px solid #00ffcc; padding:5px; margin-bottom:5px; border-radius:3px;">
                    <b style="color:#ffb700;">4. Voice Morphing SSML</b><br>
                    <span style="color:#ccc;">Prosodia táctica para avisos y tono empático en reposo.</span>
                </div>
            </div>
        `;
    }

    // 2. TICKER DE TEXTO FLOTANTE SOBRE LA IMAGEN
    const img = document.querySelector('img[src*="aigestion"]') || document.querySelector('img');
    if (img && !document.getElementById('ticker-overlay-daniela')) {
        const parent = img.parentNode;
        const wrapper = document.createElement('div');
        wrapper.className = 'daniela-img-container';

        parent.insertBefore(wrapper, img);
        wrapper.appendChild(img);

        const tickerDiv = document.createElement('div');
        tickerDiv.id = 'ticker-overlay-daniela';
        tickerDiv.innerHTML = '<div id="ticker-text-daniela">⚡ DANIELA OS LIVE: Sistema nominal | Modo Zen activo (Familia priorizada) | Sugerencia: Revisa la propuesta v10.5 en el PIP</div>';
        wrapper.appendChild(tickerDiv);
    }

    // 3. ROTADOR DE TEXTO EN VIVO SOBRE LA IMAGEN
    const avisos = [
        "⚡ DANIELA OS LIVE: Sistema nominal | Modo Zen activo | Sugerencia: Revisa la propuesta v10.5 en el PIP",
        "💡 SUGERENCIA: ¿Aplicamos el Módulo 1 (Self-Healing) o Módulo 3 (Ahorro OLED) a la interfaz?",
        "🟢 ESTADO: Batería estable | Conexión Tailscale limpia | Gemini 3.7 activo",
        "🛡️ MODO ZEN: Solo Fati, Mamá, José cuevas y a-gorde pueden activar notificaciones de voz"
    ];

    let idx = 0;
    setInterval(() => {
        const txt = document.getElementById('ticker-text-daniela');
        if (txt) {
            txt.innerText = avisos[idx];
            idx = (idx + 1) % avisos.length;
        }
    }, 10000);
});
</script>
"""

# Reemplazar e inyectar
if "fix_ui_sovereign_final" not in html:
    html = html.replace("</body>", ui_fix_script + "\n<!-- fix_ui_sovereign_final -->\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Ajuste visual final inyectado correctamente.")
else:
    print("ℹ️ El ajuste visual ya está aplicado.")
