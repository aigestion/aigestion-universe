import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

mic_only_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Buscar el botón flotante del micrófono
    const allEls = Array.from(document.querySelectorAll('button, div'));
    const micBtn = allEls.find(el =>
        (el.innerText && (el.innerText.includes('🎙️') || el.innerText.includes('🎤'))) ||
        (el.className && typeof el.className === 'string' && el.className.includes('mic'))
    );

    if (micBtn) {
        micBtn.style.position = 'fixed';
        micBtn.style.zIndex = '999999';
        micBtn.style.touchAction = 'none';

        micBtn.addEventListener('touchmove', (e) => {
            e.preventDefault();
            e.stopPropagation(); // Evita que se mueva la pantalla o el contenedor
            const touch = e.touches[0];

            // Centrar el botón bajo el dedo
            micBtn.style.left = (touch.clientX - 25) + 'px';
            micBtn.style.top = (touch.clientY - 25) + 'px';
        }, { passive: false });
    }
});
</script>
"""

if "stopPropagation()" not in html:
    html = html.replace("</body>", mic_only_script + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Arrastre aislado: Solo el micrófono es movible.")
else:
    print("ℹ️ Ajuste de micrófono único ya aplicado.")
