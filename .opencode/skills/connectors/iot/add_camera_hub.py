import re

with open('/data/data/com.termux/files/home/daniela-os/index.html') as f:
    html = f.read()

# 1. Input oculto exclusivo para captura directa con la cámara
cam_input = '<input type="file" id="cameraDirectInput" accept="image/*" capture="environment" style="display:none" onchange="onCameraCaptured(this)">'
if 'id="cameraDirectInput"' not in html:
    html = html.replace('<input type="file" id="universalFileInput"', cam_input + '\n        <input type="file" id="universalFileInput"')

# 2. Estructura del Menú Radial de la Cámara
cam_radial_html = """
        <!-- Menú Radial Táctico de la Cámara -->
        <div class="radial-menu" id="cameraHub">
            <div class="radial-node node-top" onclick="triggerCamNode('direct')">📸 FOTO DIRECTA</div>
            <div class="radial-node node-right" onclick="triggerCamNode('ocr')">🔍 OCR / CÓDIGO</div>
            <div class="radial-node node-bottom" onclick="triggerCamNode('gallery')">🖼️ GALERÍA</div>
            <div class="radial-node node-left" onclick="triggerCamNode('aig')">🤖 aig VISION</div>
        </div>
"""
if 'id="cameraHub"' not in html:
    html = html.replace('</main>', cam_radial_html + '\n    </main>')

# 3. Lógica JS para el control del menú de la cámara
cam_logic_js = """
        // --- CONTROL DEL MENÚ TÁCTICO DE CÁMARA ---
        let camHubOpen = false;

        function toggleCameraHub() {
            // Cerrar menú + si está abierto
            if (typeof hubOpen !== 'undefined' && hubOpen) {
                toggleRadialHub();
            }

            camHubOpen = !camHubOpen;
            const camHub = document.getElementById('cameraHub');
            const camBtn = document.querySelectorAll('.hud-btn')[1]; // Segundo botón (Cámara)

            if (camHubOpen) {
                camHub.style.display = 'flex';
                camHub.classList.add('open');
                if (camBtn) camBtn.classList.add('active');
                if (typeof mat !== 'undefined') mat.color.setHex(0xa855f7); // Color púrpura táctico
                document.getElementById('hudText').textContent = "VISOR MULTIMODAL: Selecciona un modo de captura de imagen.";
            } else {
                camHub.classList.remove('open');
                camHub.style.display = 'none';
                if (camBtn) camBtn.classList.remove('active');
                if (typeof mat !== 'undefined') mat.color.setHex(0xf59e0b);
            }
        }

        function triggerCamNode(type) {
            toggleCameraHub();
            const hudText = document.getElementById('hudText');

            if (type === 'direct') {
                document.getElementById('cameraDirectInput').click();
            } else if (type === 'gallery') {
                document.getElementById('universalFileInput').click();
            } else if (type === 'ocr') {
                hudText.textContent = "🔍 MODO OCR: Selecciona o toma una imagen con texto/código para auditar.";
                document.getElementById('cameraDirectInput').click();
            } else if (type === 'aig') {
                hudText.textContent = "🤖 aig VISION: Listo para procesar diagramas e interfaces.";
                document.getElementById('universalFileInput').click();
            }
        }

        function onCameraCaptured(input) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                if (typeof mat !== 'undefined') mat.color.setHex(0x22c55e);
                document.getElementById('hudText').textContent = "📸 CAPTURA RECIBIDA: " + file.name + " (" + (file.size/1024).toFixed(1) + " KB)";
                if (typeof logEvent === 'function') logEvent('VISION', "Imagen capturada: " + file.name);
                setTimeout(() => { if (typeof mat !== 'undefined') mat.color.setHex(0xf59e0b); }, 3000);
            }
        }
"""

if "CONTROL DEL MENÚ TÁCTICO DE CÁMARA" not in html:
    html = html.replace('function triggerScan()', cam_logic_js + '\n        function triggerScan_old()')
    # Reemplazar la acción onclick del botón de la cámara por la nueva función
    html = re.sub(r'<button class="hud-btn"[^>]*onclick="triggerScan\(\)"[^>]*>📸</button>', '<button class="hud-btn" onclick="toggleCameraHub()" title="Visor Táctico">📸</button>', html)

    with open('/data/data/com.termux/files/home/daniela-os/index.html', 'w') as f:
        f.write(html)
    print("Menú táctico de cámara integrado con éxito.")
else:
    print("El menú de cámara ya estaba integrado.")
