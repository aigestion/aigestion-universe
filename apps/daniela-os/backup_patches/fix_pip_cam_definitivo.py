import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

pip_cam_fix_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Función global de activación de cámara corregida para Android/Chrome
    window.pipActivarCamara = async function() {
        const area = document.getElementById('pipDisplayArea');
        if (!area) return;

        // Limpiar transmisiones activas previas
        const currentVideo = area.querySelector('video');
        if (currentVideo && currentVideo.srcObject) {
            currentVideo.srcObject.getTracks().forEach(t => t.stop());
            area.innerHTML = '<div style="color:#00ffcc; padding:10px;">Esperando selección...</div>';
            return;
        }

        area.innerHTML = '<div style="color:#00ffcc; padding:8px; font-size:0.7rem;">Iniciando cámara...</div>';

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: { ideal: "environment" },
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                },
                audio: false
            });

            area.innerHTML = '';
            const video = document.createElement('video');
            video.setAttribute('playsinline', '');
            video.setAttribute('webkit-playsinline', '');
            video.autoplay = true;
            video.muted = true;
            video.style.cssText = 'width:100%; height:100%; object-fit:cover; border-radius:6px; background:#000;';
            video.srcObject = stream;

            area.appendChild(video);
            video.play().catch(e => console.log("Autoplay handle:", e));

            const inputArea = document.querySelector('input[type="text"]') || document.querySelector('textarea');
            if (inputArea) inputArea.value = '[Cámara activa en PIP Master] ';
        } catch(err) {
            area.innerHTML = `<div style="color:#ff0055; padding:6px; font-size:0.65rem;">⚠️ Error Cámara: ${err.message}</div>`;
        }
    };

    // Vincular el botón cámara inferior (junto al botón +)
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

if "window.pipActivarCamara = async" not in html:
    html = html.replace("</body>", pip_cam_fix_script + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ PIP Master y cámara reparados.")
else:
    print("ℹ️ Ajustes de cámara ya integrados.")
