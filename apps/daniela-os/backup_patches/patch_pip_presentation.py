import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

presentation_pip_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Proyección de la Presentación Premium en el PIP Master
    window.proyectarPresentacionPIP = function(docUrl) {
        const area = document.getElementById('pipDisplayArea');
        if (!area) return;

        // Limpiar visor PIP e inyectar el Iframe con visor limpio
        area.innerHTML = '';
        const iframe = document.createElement('iframe');
        iframe.src = docUrl ? docUrl.replace('/edit', '/preview') : 'about:blank';
        iframe.style.cssText = 'width:100%; height:100%; border:none; border-radius:6px; background:#111;';

        area.appendChild(iframe);

        // Notificar en la interfaz
        const inputArea = document.querySelector('input[type="text"]') || document.querySelector('textarea');
        if (inputArea) inputArea.value = '[Presentación Sovereign proyectada en PIP Master] ';
    };

    // Auto-ejecución inmediata con la propuesta v10.5 recién creada
    const docID = "1skAWHAFFbSL96X2HznszE-kRpnQ8GVgGFP0YGx3L4zI";
    const embedUrl = `https://docs.google.com/document/d/${docID}/preview`;

    // Proyectar al cargar
    setTimeout(() => {
        window.proyectarPresentacionPIP(embedUrl);
    }, 1000);
});
</script>
"""

if "proyectarPresentacionPIP" not in html:
    html = html.replace("</body>", presentation_pip_script + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Generador y visor PIP Premium conectados correctamente.")
else:
    print("ℹ️ El visor de presentaciones en PIP ya estaba activo.")
