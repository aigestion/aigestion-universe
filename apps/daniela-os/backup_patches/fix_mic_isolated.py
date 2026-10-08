import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

isolated_mic_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        // 1. Localizar de forma exacta el botón rosa flotante del micrófono
        const allBtns = Array.from(document.querySelectorAll('button, div, a'));
        const micBtn = allBtns.find(el =>
            el.offsetHeight > 0 &&
            (
                el.innerText.includes('🎙️') ||
                el.innerText.includes('🎤') ||
                (el.className && typeof el.className === 'string' && el.className.includes('mic')) ||
                getComputedStyle(el).borderRadius === '50%'
            )
        );

        if (micBtn) {
            // 2. Extraer el botón al body para aislarlo de cualquier contenedor
            document.body.appendChild(micBtn);

            // 3. Aplicar posición fija independiente
            micBtn.style.position = 'fixed';
            micBtn.style.bottom = '20px';
            micBtn.style.right = '20px';
            micBtn.style.zIndex = '9999999';
            micBtn.style.touchAction = 'none';

            // 4. Lógica de arrastre aislado que congela la pantalla de fondo
            micBtn.addEventListener('touchmove', (e) => {
                e.preventDefault();
                e.stopPropagation();

                const touch = e.touches[0];
                const width = micBtn.offsetWidth || 50;
                const height = micBtn.offsetHeight || 50;

                micBtn.style.left = (touch.clientX - width / 2) + 'px';
                micBtn.style.top = (touch.clientY - height / 2) + 'px';
                micBtn.style.bottom = 'auto';
                micBtn.style.right = 'auto';
            }, { passive: false });
        }
    }, 500);
});
</script>
"""

if "isolated_mic_script" not in html:
    html = html.replace("</body>", isolated_mic_script + "\n<!-- isolated_mic_script -->\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Botón de micrófono aislado y desacoplado del resto de la interfaz.")
else:
    print("ℹ️ El micrófono ya estaba aislado.")
