import os

from safe_exec import run_cmd

# 1. Recuperar plantilla limpia desde templates o git
if os.path.exists("templates/index.html"):
    with open("templates/index.html", encoding="utf-8") as f:
        html = f.read()
elif os.path.exists("daniela_os.py.bak"):
    run_cmd(["git", "checkout", "--", "index.html"])
    with open("index.html", encoding="utf-8") as f:
        html = f.read()

# 2. Desactivar PIN de bloqueo
html = html.replace("#pinOverlay {", "#pinOverlay { display: none !important; ")

# 3. Inyectar CSS y JS Limpio para Foto y Botones
master_script = """
<style>
  /* Fuerza el renderizado de la foto guardada en el cuadro superior */
  .canvas, .studio, div[class*="studio"] {
    background-image: url('/static/daniela_foto.jpg') !important;
    background-size: cover !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
  }
</style>

<input type="file" id="danielaNativeInput" accept="image/*" style="display:none !important;">

<script>
document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('danielaNativeInput');

    // Manejar clic en SUBIR FOTO
    document.addEventListener('click', (e) => {
        const target = e.target.closest('*');
        if (!target) return;
        const txt = (target.innerText || '').trim();

        if (txt.includes('SUBIR FOTO')) {
            e.preventDefault();
            e.stopPropagation();
            fileInput.click();
            return;
        }

        // Atajos de botones inferiores
        const chatInput = document.querySelector('input[type="text"]') || document.querySelector('textarea');
        if (chatInput) {
            if (txt.includes('Portal PYME')) { chatInput.value = '/canvas '; chatInput.focus(); }
            else if (txt.includes('Diagrama Flujo')) { chatInput.value = '/diagram '; chatInput.focus(); }
            else if (txt.includes('Pack Ventas')) { chatInput.value = '/content '; chatInput.focus(); }
            else if (txt.includes('Swarm')) { chatInput.value = '/swarm '; chatInput.focus(); }
        }
    });

    // Subir imagen al servidor
    fileInput.addEventListener('change', async () => {
        if (!fileInput.files.length) return;
        const file = fileInput.files[0];
        try {
            const res = await fetch('/upload', { method: 'POST', body: file });
            if (res.ok) {
                alert('📸 Foto oficial de Daniela actualizada.');
                location.reload();
            } else {
                alert('Error al subir la foto.');
            }
        } catch(err) {
            alert('Error de red al subir la imagen.');
        }
    });
});
</script>
"""

if "danielaNativeInput" not in html:
    html = (
        html.replace("</body>", master_script + "\n</body>")
        if "</body>" in html
        else html + master_script
    )

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Interface AIGestion Sovereign v10.0 restaurada y configurada.")
