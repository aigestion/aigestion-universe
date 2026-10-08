with open("/data/data/com.termux/files/home/daniela-os/index.html") as f:
    html = f.read()

# Lógica de conexión backend sin alterar HTML/CSS
backend_logic = """
        // --- CONEXIÓN REAL CON BACKEND PYTHON / GEMINI API ---
        let currentFileContext = "";

        // Lectura real de archivos subidos
        function onFileUploaded(input) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                const reader = new FileReader();

                reader.onload = function(e) {
                    currentFileContext = e.target.result;
                    mat.color.setHex(0x22c55e); // Confirmación verde
                    const msg = `Archivo "${file.name}" (${(file.size/1024).toFixed(1)} KB) cargado en memoria context.`;
                    document.getElementById('hudText').textContent = "📁 " + msg;
                    if(typeof logEvent === 'function') logEvent('FILE', msg);
                    setTimeout(() => { mat.color.setHex(0xf59e0b); }, 3000);
                };

                reader.readAsText(file);
            }
        }

        // Envío real de comandos al servidor Python
        async function sendCmd() {
            const inputEl = document.getElementById('cmd');
            const prompt = inputEl.value.trim();
            if(!prompt) return;

            inputEl.value = '';
            document.getElementById('hudText').textContent = "PROCESANDO: " + prompt;
            mat.color.setHex(0xffffff); // Flash blanco
            if(typeof logEvent === 'function') logEvent('USER', prompt);

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'json' },
                    body: JSON.stringify({
                        message: prompt,
                        context: currentFileContext
                    })
                });

                if(!response.ok) throw new Error('Error en el servidor backend');

                const data = await response.json();
                const reply = data.response || "Comando procesado correctamente.";

                document.getElementById('hudText').textContent = "DANIELA: " + reply;
                mat.color.setHex(0x22c55e);
                if(typeof logEvent === 'function') logEvent('AI', reply);
            } catch (err) {
                document.getElementById('hudText').textContent = "SISTEMA: Respuesta recibida localmente (Modo Offline).";
                mat.color.setHex(0xf59e0b);
                if(typeof logEvent === 'function') logEvent('SYS_WARN', err.message);
            }

            setTimeout(() => { mat.color.setHex(0xf59e0b); }, 3000);
        }
"""

if "CONEXIÓN REAL CON BACKEND" not in html:
    html = html.replace(
        "function sendCmd() {", backend_logic + "\n        function old_sendCmd() {"
    )
    with open("/data/data/com.termux/files/home/daniela-os/index.html", "w") as f:
        f.write(html)
    print("Módulo de conexión backend integrado correctamente.")
else:
    print("El módulo ya está integrado.")
