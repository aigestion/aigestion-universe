import os

app_file = "app_daniela.py"
if os.path.exists(app_file):
    with open(app_file, encoding="utf-8") as f:
        code = f.read()

    # Endpoint dedicado e infalible para captura de cámara
    cam_endpoint = """
@app.route('/api/camera', methods=['GET', 'POST'])
def api_camera_trigger():
    import subprocess
    os.makedirs("static", exist_ok=True)
    img_path = "static/cam_feed.jpg"

    # Capturar imagen desde el sensor de Termux
    subprocess.run(["termux-camera-photo", "-c", "0", img_path], capture_output=True)

    if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
        return jsonify({
            "status": "ok",
            "message": "📷 Cámara física activada.",
            "url": "/static/cam_feed.jpg"
        })
    return jsonify({"status": "error", "message": "No se pudo acceder a la cámara"}), 500
"""

    if "/api/camera" not in code:
        # Inyectar antes del bloque main
        if "if __name__" in code:
            code = code.replace("if __name__", cam_endpoint + "\nif __name__")
        else:
            code += "\n" + cam_endpoint

        with open(app_file, "w", encoding="utf-8") as f:
            f.write(code)
        print("✅ Endpoint /api/camera creado en app_daniela.py")

# Actualizar el HTML para que el botón de cámara llame a la cámara real e inyecte la imagen
index_file = "index.html"
if not os.path.exists(index_file) and os.path.exists("templates/index.html"):
    index_file = "templates/index.html"

if os.path.exists(index_file):
    with open(index_file, encoding="utf-8") as f:
        html = f.read()

    js_camera_override = """
<script>
function triggerRealCamera() {
    const pipDisplay = document.querySelector('.pip-window .pip-content') || document.getElementById('pipDisplayArea');
    if (pipDisplay) {
        pipDisplay.innerHTML = '<span style="color:#00ffcc; font-size:0.8rem;">📷 Capturando imagen...</span>';
    }

    fetch('/api/camera', { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok' && pipDisplay) {
            pipDisplay.innerHTML = `<img src="${data.url}?t=${new Date().getTime()}" style="width:100%; height:100%; object-fit:cover;">`;
        } else if (pipDisplay) {
            pipDisplay.innerHTML = '<span style="color:#ff0055; font-size:0.75rem;">⚠️ Error de sensor</span>';
        }
    })
    .catch(err => {
        if (pipDisplay) pipDisplay.innerHTML = '<span style="color:#ff0055; font-size:0.75rem;">⚠️ Error de conexión</span>';
    });
}

// Vincular el botón del icono de la cámara
document.addEventListener('DOMContentLoaded', () => {
    const camBtn = document.querySelector('.controls-bar button img')?.parentElement || document.querySelectorAll('.controls-bar button')[0];
    if (camBtn) {
        camBtn.setAttribute('onclick', 'triggerRealCamera()');
    }
});
</script>
"""
    if "triggerRealCamera" not in html:
        html = html.replace("</body>", js_camera_override + "\n</body>")
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Frontend vinculado directamente al endpoint de cámara.")
