import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

if os.path.exists(filepath):
    with open(filepath, encoding="utf-8") as f:
        html = f.read()

    # CSS y JS para adjuntar archivos y captura/compartir pantalla
    multimodal_patch = """
    <style>
      .multimodal-bar {
        display: flex;
        gap: 6px;
        margin-top: 6px;
        margin-bottom: 6px;
      }
      .btn-tactico {
        flex: 1;
        background: rgba(12, 16, 26, 0.85);
        border: 1px solid var(--cyan, #00ffcc);
        color: var(--cyan, #00ffcc);
        padding: 8px 4px;
        font-size: 0.75rem;
        font-weight: bold;
        border-radius: 6px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
      }
      .btn-tactico:active {
        background: rgba(0, 255, 204, 0.2);
      }
    </style>

    <input type="file" id="chatFileInput" style="display:none !important;" multiple>

    <script>
    document.addEventListener('DOMContentLoaded', () => {
        // Localizar el área de control del chat (donde están Limpiar Chat y Modalidad Audio)
        const controlArea = document.querySelector('.multimodal-bar-container') || document.querySelector('button, div').parentElement;

        // Crear la barra de controles tácticos multimodales si no existe
        if (!document.getElementById('multimodalControls')) {
            const bar = document.createElement('div');
            bar.id = 'multimodalControls';
            bar.className = 'multimodal-bar';

            bar.innerHTML = `
                <button type="button" class="btn-tactico" id="btnUploadFile">
                    📎 ADJUNTAR ARCHIVO
                </button>
                <button type="button" class="btn-tactico" id="btnShareScreen">
                    📱 COMPARTIR PANTALLA
                </button>
            `;

            // Insertar justo encima del área de entrada de texto
            const inputBox = document.querySelector('input[type="text"]') || document.querySelector('textarea');
            if (inputBox && inputBox.parentElement) {
                inputBox.parentElement.insertBefore(bar, inputBox);
            }
        }

        // Lógica de Subida de Archivos al Chat
        const fileInput = document.getElementById('chatFileInput');
        const uploadBtn = document.getElementById('btnUploadFile');
        if (uploadBtn) {
            uploadBtn.onclick = () => fileInput.click();
            fileInput.onchange = async () => {
                if (!fileInput.files.length) return;
                const file = fileInput.files[0];
                const formData = new FormData();
                formData.append('file', file);

                try {
                    const res = await fetch('/upload', { method: 'POST', body: file });
                    if (res.ok) {
                        const input = document.querySelector('input[type="text"]') || document.querySelector('textarea');
                        if (input) input.value += ` [Archivo adjunto: ${file.name}]`;
                        alert(`✅ Archivo ${file.name} cargado en el chat.`);
                    }
                } catch(e) {
                    alert('Error enviando el archivo al chat.');
                }
            };
        }

        // Lógica de Compartir Pantalla en Android / Chrome
        const shareBtn = document.getElementById('btnShareScreen');
        if (shareBtn) {
            shareBtn.onclick = async () => {
                try {
                    const mediaStream = await navigator.mediaDevices.getDisplayMedia({
                        video: { cursor: "always" },
                        audio: false
                    });
                    alert('📱 Compartiendo pantalla con Daniela activado.');

                    // Detener la transmisión al cerrar
                    mediaStream.getVideoTracks()[0].onended = () => {
                        alert('Transmisión de pantalla finalizada.');
                    };
                } catch (err) {
                    alert('No se pudo acceder a la captura de pantalla: ' + err.message);
                }
            };
        }
    });
    </script>
    """

    if "btnShareScreen" not in html:
        html = (
            html.replace("</body>", multimodal_patch + "\n</body>")
            if "</body>" in html
            else html + multimodal_patch
        )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Botones de Adjuntar Archivo y Compartir Pantalla agregados.")
    else:
        print("ℹ️ Los botones ya están presentes en la interfaz.")
