import os

# 1. Reescribir lógica en app_daniela.py
app_file = "app_daniela.py"
if os.path.exists(app_file):
    with open(app_file, encoding="utf-8") as f:
        code = f.read()

    # Inyección amplia: cualquier mención a cámara dispara el hardware
    broad_handler = """
    # Inyección amplia para cámara
    if any(w in user_message.lower() for w in ["cámara", "camara", "foto", "captura"]):
        import subprocess
        os.makedirs("static", exist_ok=True)
        img_path = "static/cam_feed.jpg"

        # Ejecutar captura directa en Termux
        subprocess.run(["termux-camera-photo", "-c", "0", img_path], capture_output=True)

        if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
            return jsonify({
                "response": "📷 Captura de cámara ejecutada correctamente. Proyectando imagen en PIP Master.",
                "pip_type": "camera",
                "cam_url": "/static/cam_feed.jpg"
            })
        else:
            return jsonify({
                "response": "⚠️ Error: No se pudo capturar la imagen. Comprueba los permisos de cámara en Termux-API.",
                "pip_type": "error"
            })
"""

    if "broad_handler" not in code:
        code = code.replace("def api_chat():", "def api_chat():\n" + broad_handler)
        with open(app_file, "w", encoding="utf-8") as f:
            f.write(code)
        print("✅ Backend actualizado con disparador amplio de cámara.")

# 2. Asegurar JS de inyección en index.html
index_file = "index.html"
if not os.path.exists(index_file) and os.path.exists("templates/index.html"):
    index_file = "templates/index.html"

if os.path.exists(index_file):
    with open(index_file, encoding="utf-8") as f:
        html = f.read()

    js_inject = """
<script>
// Forzar renderizado en el recuadro PIP Master
function setPipImage(url) {
    const pipDisplay = document.getElementById('pipDisplayArea') || document.querySelector('.pip-window div') || document.querySelector('.pip-content');
    if (pipDisplay) {
        pipDisplay.innerHTML = `<img src="${url}?t=${new Date().getTime()}" style="width:100%; height:100%; object-fit:cover; border-radius:4px;">`;
    }
}

// Escuchar evento de botón de cámara directo en la UI
document.addEventListener('DOMContentLoaded', () => {
    const camBtn = document.querySelector('button img[src*="camera"]')?.parentElement || document.querySelector('.controls-bar button:nth-child(2)');
    if (camBtn) {
        camBtn.onclick = () => {
            fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: 'cámara' })
            }).then(r => r.json()).then(data => {
                if (data.cam_url) setPipImage(data.cam_url);
            });
        };
    }
});
</script>
"""
    if "setPipImage" not in html:
        html = html.replace("</body>", js_inject + "\n</body>")
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Frontend actualizado con forzado de PIP.")
