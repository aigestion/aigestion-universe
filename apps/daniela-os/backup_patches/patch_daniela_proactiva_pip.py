import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

proactive_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    const pipArea = document.getElementById('pipDisplayArea');

    // 1. Contenidos Proactivos Automáticos (Noticias / Matrix / Expresión)
    const contenidosProactivos = [
        '<div style="padding:10px; font-size:0.7rem; color:#00ffcc;"><strong style="color:#ff0055;">⚡ DANIELA NEWS:</strong> Monitorizando novedades IA y legislación fiscal en España...</div>',
        '<div style="font-family:monospace; font-size:0.65rem; color:#39ff14; text-align:left; padding:6px;">[DANIELA OS]<br>Status: ONLINE<br>Tailscale: Protegido<br>Voz: Lista</div>',
        '<div style="padding:10px; font-size:0.7rem; color:#a855f7;"><b>💡 TIP DANIELA:</b> Pulsa + para proyectar cualquier documento en esta pantalla.</div>'
    ];

    let indexProactivo = 0;

    // 2. Bucle Proactivo: Se ejecuta cada 12 segundos si la cámara no está activa
    setInterval(() => {
        if (!pipArea) return;
        const tieneVideo = pipArea.querySelector('video');
        const tieneIframe = pipArea.querySelector('iframe');

        // Si no hay cámara ni vídeo de YouTube activo, cambiar la pantalla proactiva
        if (!tieneVideo && !tieneIframe) {
            pipArea.innerHTML = contenidosProactivos[indexProactivo];
            indexProactivo = (indexProactivo + 1) % contenidosProactivos.length;
        }
    }, 12000);
});
</script>
"""

if "contenidosProactivos" not in html:
    html = html.replace("</body>", proactive_script + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Motor Daniela Proactiva PIP inyectado.")
else:
    print("ℹ️ El motor proactivo ya estaba instalado.")
