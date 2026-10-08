import os

app_path = "app_daniela.py"
if os.path.exists(app_path):
    with open(app_path, encoding="utf-8") as f:
        code = f.read()

    # Inyección para tomar foto/stream real con termux-camera-photo o servidor de vídeo
    camera_logic = """
    if "cámara" in user_message.lower() or "camara" in user_message.lower():
        if any(w in user_message.lower() for w in ["enciende", "activa", "abre"]):
            import subprocess
            # Tomar captura real para refrescar el visor o iniciar stream
            os.system("termux-camera-photo -c 0 static/cam_feed.jpg &")
            return jsonify({
                "response": "📷 Cámara física activada. Capturando entorno...",
                "pip_action": "stream_cam"
            })
"""
    if "termux-camera-photo" not in code:
        code = code.replace("def api_chat():", "def api_chat():\n" + camera_logic)
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(code)
        print("✅ Control de cámara real inyectado.")

index_path = "index.html"
if not os.path.exists(index_path) and os.path.exists("templates/index.html"):
    index_path = "templates/index.html"

with open(index_path, encoding="utf-8") as f:
    html = f.read()

pip_cam_script = """
<script>
function checkCamFeed() {
    const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
    if (area) {
        area.innerHTML = `<img src="/static/cam_feed.jpg?t=${new Date().getTime()}" style="width:100%; height:100%; object-fit:cover; border-radius:4px;">`;
    }
}
</script>
"""

if "checkCamFeed" not in html:
    html = html.replace("</body>", pip_cam_script + "\n</body>")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Visor de cámara vinculado en el frontend.")
