import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

pip_proactivo_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    const area = document.getElementById('pipDisplayArea');
    const inputArea = document.querySelector('input[type="text"]') || document.querySelector('textarea');
    const plusInput = document.getElementById('plusFileInput') || document.getElementById('chatFileInput');

    // 1. FUNCIÓN GLOBAL: Permite a Daniela proyectar cualquier elemento en el PIP
    window.danielaMostrarEnPIP = function(tipo, contenido, descripcion = '') {
        if (!area) return;
        area.innerHTML = '';

        if (tipo === 'imagen') {
            area.innerHTML = `<img src="${contenido}" style="width:100%; height:100%; object-fit:contain; border-radius:6px;">`;
        } else if (tipo === 'youtube') {
            const embed = contenido.replace('watch?v=', 'embed/');
            area.innerHTML = `<iframe src="${embed}?autoplay=1" style="width:100%; height:100%; border:none; border-radius:6px;"></iframe>`;
        } else if (tipo === 'html' || tipo === 'noticia') {
            area.innerHTML = `<div style="padding:8px; font-size:0.7rem; color:#00ffcc; text-align:left;">${contenido}</div>`;
        }

        if (descripcion && inputArea) {
            inputArea.value = `[Proyectando en PIP: ${descripcion}] ` + inputArea.value;
        }
    };

    // 2. DETECTOR DE ARCHIVOS SUBIDOS: Carga en PIP y da contexto a Daniela
    if (plusInput) {
        plusInput.addEventListener('change', async () => {
            if (!plusInput.files.length) return;
            const file = plusInput.files[0];

            if (file.type.startsWith('image/')) {
                const url = URL.createObjectURL(file);
                window.danielaMostrarEnPIP('imagen', url, file.name);
            } else {
                window.danielaMostrarEnPIP('html', `<div style="color:#00ffcc; padding:10px;">📄 <b>Documento Cargado:</b><br>${file.name}</div>`, file.name);
            }
        });
    }

    // 3. MOTOR PROACTIVO EN REPOSO (Rotador audiovisual cuando no hay cámara ni reproducción)
    const avisosProactivos = [
        '<div style="padding:8px; font-size:0.68rem; color:#00ffcc; text-align:left;"><strong style="color:#ff0055;">⚡ DANIELA PROACTIVA:</strong> Monitorizando sistema. Escribe o sube un documento para analizarlo.</div>',
        '<div style="font-family:monospace; font-size:0.65rem; color:#39ff14; text-align:left; padding:8px;">[AIGestion Node]<br>Status: ONLINE 🟢<br>Tailscale: Activo<br>Gemini 3.7: Conectado</div>',
        '<div style="padding:8px; font-size:0.68rem; color:#a855f7; text-align:left;"><b>💡 CONSEJO TÁCTICO:</b> Arrastra el micrófono flotante para reubicarlo donde no te estorbe.</div>'
    ];

    let indexPro = 0;
    setInterval(() => {
        if (!area) return;
        const tieneVideo = area.querySelector('video');
        const tieneIframe = area.querySelector('iframe');
        const tieneImagen = area.querySelector('img');

        // Solo rotar información si la pantalla no está siendo ocupada por video, cámara o archivo
        if (!tieneVideo && !tieneIframe && !tieneImagen) {
            area.innerHTML = avisosProactivos[indexPro];
            indexPro = (indexPro + 1) % avisosProactivos.length;
        }
    }, 10000);
});
</script>
"""

if "danielaMostrarEnPIP" not in html:
    html = html.replace("</body>", pip_proactivo_script + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Motor proactivo y comunicación multimodal inyectados en PIP Master.")
else:
    print("ℹ️ El motor proactivo ya estaba presente.")
