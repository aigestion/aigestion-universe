with open("index.html", encoding="utf-8") as f:
    html = f.read()

script_mic_exacto = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Buscar el botón circular flotante del micrófono por sus características exactas
    const btns = Array.from(document.querySelectorAll('*'));
    const micBtn = btns.find(el => {
        const style = window.getComputedStyle(el);
        return (style.borderRadius === '50%' || el.className.includes('mic')) && el.offsetWidth < 80 && el.offsetHeight > 0;
    });

    if (micBtn) {
        micBtn.style.touchAction = 'none'; // Evita que la pantalla/scroll se mueva al arrastrar
        micBtn.style.position = 'fixed';
        micBtn.style.zIndex = '999999';

        let isDragging = false;
        let offsetX = 0, offsetY = 0;

        micBtn.addEventListener('touchstart', (e) => {
            isDragging = true;
            const touch = e.touches[0];
            const rect = micBtn.getBoundingClientRect();
            offsetX = touch.clientX - rect.left;
            offsetY = touch.clientY - rect.top;
        }, { passive: false });

        micBtn.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            e.preventDefault(); // Detiene el movimiento de la pantalla
            const touch = e.touches[0];
            micBtn.style.left = (touch.clientX - offsetX) + 'px';
            micBtn.style.top = (touch.clientY - offsetY) + 'px';
            micBtn.style.bottom = 'auto';
            micBtn.style.right = 'auto';
        }, { passive: false });

        micBtn.addEventListener('touchend', () => { isDragging = false; });
    }
});
</script>
"""

if "touchAction = 'none'" not in html:
    html = html.replace("</body>", script_mic_exacto + "\n</body>")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Restaurado y arreglado solo el botón de micrófono.")
