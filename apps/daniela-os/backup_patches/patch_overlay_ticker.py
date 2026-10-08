import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

overlay_script = """
<style>
/* Contenedor relativo para la imagen de Daniela */
.daniela-img-wrapper {
    position: relative;
    display: inline-block;
    width: 100%;
}

/* Banner transparente superpuesto en la zona inferior de la imagen */
#overlay-ticker {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    background: rgba(0, 0, 0, 0.75);
    border-top: 1px solid #00ffcc;
    border-bottom: 1px solid #00ffcc;
    overflow: hidden;
    padding: 4px 0;
    z-index: 10;
}

#overlay-ticker-text {
    display: inline-block;
    white-space: nowrap;
    color: #00ffcc;
    font-family: monospace;
    font-size: 0.75rem;
    animation: ticker-scroll 20s linear infinite;
}

@keyframes ticker-scroll {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
</style>

<script>
document.addEventListener('DOMContentLoaded', () => {
    // 1. Localizar la imagen principal de Daniela y envolverla si es necesario
    const img = document.querySelector('img[src*="aigestion"]') || document.querySelector('img');
    if (img && !document.getElementById('overlay-ticker')) {
        const parent = img.parentNode;
        const wrapper = document.createElement('div');
        wrapper.className = 'daniela-img-wrapper';

        parent.insertBefore(wrapper, img);
        wrapper.appendChild(img);

        // 2. Crear el ticker superpuesto
        const tickerDiv = document.createElement('div');
        tickerDiv.id = 'overlay-ticker';
        tickerDiv.innerHTML = '<div id="overlay-ticker-text">⚡ DANIELA OS LIVE: Sistema activo | Propuesta v10.5 lista | Batería y Tailscale Nominales</div>';
        wrapper.appendChild(tickerDiv);
    }

    // 3. Rotador de información en vivo y sugerencias
    const mensajesEnVivo = [
        "⚡ PROPUESTA v10.5: Self-Healing Ticker | Sovereign Glass HUD | Stealth OLED | Voice Morphing",
        "💡 SUGERENCIA: Modo Zen activo. Únicamente la familia (Fati, Mamá, José cuevas, a-gorde) puede interrumpir.",
        "🟢 ESTADO: Servidor Termux estable | Tailscale activo | Gemini 3.7 conectado",
        "💡 SUGERENCIA: Sube un archivo con el botón + para proyectar su análisis táctico en el PIP Master"
    ];

    let idx = 0;
    setInterval(() => {
        const textElem = document.getElementById('overlay-ticker-text');
        if (textElem) {
            textElem.innerText = mensajesEnVivo[idx];
            idx = (idx + 1) % mensajesEnVivo.length;
        }
    }, 12000);
});
</script>
"""

if "overlay-ticker" not in html:
    html = html.replace("</body>", overlay_script + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Ticker superpuesto inyectado sobre la imagen de Daniela.")
else:
    print("ℹ️ El Ticker superpuesto ya está presente.")
