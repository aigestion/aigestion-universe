import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

script_cam_fix = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Función única para encender cámara en PIP MASTER
    window.pipActivarCamara = async function() {
        const area = document.getElementById('pipDisplayArea');
        if (!area) return;

        // Si ya hay un video transmitiendo, apagarlo
        const oldVideo = area.querySelector('video');
        if (oldVideo && oldVideo.srcObject) {
            oldVideo.srcObject.getTracks().forEach(t => t.stop());
            area.innerHTML = '<div style="color:#00ffcc; padding:10px;">Esperando selección...</div>';
            return;
        }

        area.innerHTML = '<div style="color:#00ffcc; padding:10px;">Cargando cámara...</div>';

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "environment" },
                audio: false
            });

            area.innerHTML = '';
            const video = document.createElement('video');
            video.autoplay = true;
            video.playsInline = true;
            video.muted = true;
            video.style.cssText = 'width:100%; height:100%; object-fit:cover; border-radius:6px;';
            video.srcObject = stream;
            area.appendChild(video);

            const inputArea = document.querySelector('input[type="text"]') || document.querySelector('textarea');
            if (inputArea) inputArea.value = '[Cámara en vivo activa en PIP Master] ';
        } catch(err) {
            area.innerHTML = '<div style="color:#ff0055; padding:8px; font-size:0.65rem;">⚠️ Permiso denegado/Error cámara</div>';
        }
    };

    // Vincular botón cámara inferior (junto al botón +)
    const btnCamInferior = document.getElementById('btnCamPip');
    if (btnCamInferior) {
        btnCamInferior.onclick = (e) => {
            e.preventDefault();
            window.pipActivarCamara();
        };
    }
});
</script>
"""

if "pipActivarCamara = async" not in html:
    html = html.replace("</body>", script_cam_fix + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Disparador de cámara conectado directamente al PIP Master.")
else:
    print("ℹ️ El enlace directo ya estaba instalado.")
