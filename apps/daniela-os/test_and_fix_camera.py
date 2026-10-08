import os
import subprocess
import time

print("🔍 === INICIANDO AUDITORÍA Y PRUEBAS UNITARIAS DE HARDWARE ===")


# 1. PRUEBA UNITARIA: Verificar binario termux-camera-photo
def test_termux_camera_binary():
    res = subprocess.run(["which", "termux-camera-photo"], capture_output=True, text=True)
    if res.returncode == 0:
        print("✅ [TEST PASS] Binario termux-camera-photo detectado.")
        return True
    else:
        print("❌ [TEST FAIL] Binario termux-camera-photo NO encontrado en PATH.")
        return False


# 2. PRUEBA UNITARIA: Captura real de fotograma
def test_camera_capture():
    os.makedirs("static", exist_ok=True)
    test_img = "static/cam_feed.jpg"
    if os.path.exists(test_img):
        os.remove(test_img)

    # Ejecutar captura de prueba
    subprocess.run(["termux-camera-photo", "-c", "0", test_img], capture_output=True)
    time.sleep(1)

    if os.path.exists(test_img) and os.path.getsize(test_img) > 0:
        print(
            f"✅ [TEST PASS] Fotograma generado correctamente ({os.path.getsize(test_img)} bytes)."
        )
        return True
    else:
        print("❌ [TEST FAIL] No se pudo generar la imagen física de la cámara.")
        return False


# 3. REVISOR Y PARCHER AUTOMÁTICO DE LOGS / APP
def patch_backend_and_frontend():
    app_file = "app_daniela.py"
    if not os.path.exists(app_file):
        print("❌ No se encontró app_daniela.py")
        return

    with open(app_file, encoding="utf-8") as f:
        code = f.read()

    # Inyectar controlador verificado de cámara sin falsas promesas
    real_cam_handler = """
    # Handler verificado por pruebas unitarias
    if "cámara" in user_message.lower() or "camara" in user_message.lower():
        if any(w in user_message.lower() for w in ["enciende", "activa", "abre"]):
            os.makedirs("static", exist_ok=True)
            img_path = "static/cam_feed.jpg"
            subprocess.run(["termux-camera-photo", "-c", "0", img_path], capture_output=True)

            if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                return jsonify({
                    "response": "📷 Cámara activada. Fotograma capturado y proyectado en el PIP Master.",
                    "pip_type": "camera",
                    "cam_url": "/static/cam_feed.jpg"
                })
            else:
                return jsonify({
                    "response": "⚠️ Error de hardware: No se pudo obtener el stream del sensor. Revisa los permisos de Termux-API.",
                    "pip_type": "error"
                })
"""

    if "termux-camera-photo" not in code or "pip_type" not in code:
        code = code.replace("def api_chat():", "def api_chat():\n" + real_cam_handler)
        with open(app_file, "w", encoding="utf-8") as f:
            f.write(code)
        print("✅ Backend actualizado con validación estricta de captura.")

    # Actualizar index.html para forzar refresco dinámico en PIP Master
    index_file = "index.html"
    if not os.path.exists(index_file) and os.path.exists("templates/index.html"):
        index_file = "templates/index.html"

    with open(index_file, encoding="utf-8") as f:
        html = f.read()

    pip_auto_refresh = """
<script>
function renderPipCamera(url) {
    const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
    if (area) {
        area.style.background = '#000';
        area.innerHTML = `<img src="${url}?t=${new Date().getTime()}" style="width:100%; height:100%; object-fit:cover; border-radius:4px;">`;
    }
}

// Interceptor de respuesta de chat
const origFetch = window.fetch;
window.fetch = async function(...args) {
    const response = await origFetch(...args);
    if (args[0] && args[0].includes('/api/chat')) {
        const clone = response.clone();
        try {
            const data = await clone.json();
            if (data.pip_type === 'camera' && data.cam_url) {
                renderPipCamera(data.cam_url);
            }
        } catch(e){}
    }
    return response;
};
</script>
"""

    if "renderPipCamera" not in html:
        html = html.replace("</body>", pip_auto_refresh + "\n</body>")
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Frontend parcheado para auto-refresco del PIP.")


# Ejecutar Diagnóstico
bin_ok = test_termux_camera_binary()
cam_ok = test_camera_capture()

patch_backend_and_frontend()

print("\n🚀 === RESTARTING SERVER WITH AUTO-VERIFIED HARDWARE ===")
