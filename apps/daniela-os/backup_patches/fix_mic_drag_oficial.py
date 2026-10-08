import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

mic_drag_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Localizar el micrófono flotante (por icono o clase)
    const allEls = Array.from(document.querySelectorAll('*'));
    const micBtn = allEls.find(el =>
        (el.innerText && el.innerText.includes('🎙️')) ||
        (el.innerText && el.innerText.includes('🎤')) ||
        (el.className && typeof el.className === 'string' && el.className.includes('mic'))
    );

    if (micBtn) {
        micBtn.style.position = 'fixed';
        micBtn.style.zIndex = '999999';
        micBtn.style.touchAction = 'none';

        let initialX = 0, initialY = 0, currentX = 0, currentY = 0;

        micBtn.addEventListener('touchstart', (e) => {
            initialX = e.touches[0].clientX - currentX;
            initialY = e.touches[0].clientY - currentY;
        }, { passive: true });

        micBtn.addEventListener('touchmove', (e) => {
            currentX = e.touches[0].clientX - initialX;
            currentY = e.touches[0].clientY - initialY;
            micBtn.style.transform = `translate3d(${currentX}px, ${currentY}px, 0)`;
        }, { passive: true });
    }
});
</script>
"""

if "initialX = e.touches[0].clientX - currentX" not in html:
    html = html.replace("</body>", mic_drag_script + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Arrastre táctil de micrófono activado con éxito.")
else:
    print("ℹ️ El manejador táctil del micrófono ya está instalado.")
