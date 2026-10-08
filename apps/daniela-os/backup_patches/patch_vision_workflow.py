filepath = "index.html"
with open(filepath, encoding="utf-8") as f:
    html = f.read()

vision_script = """
<script>
// --- MOTOR DE VISIÓN Y DOCUMENTACIÓN ---
let visionInterval = null;

// B: MODO CENTINELA (Visión)
async function pipActivarCentinela() {
    await pipActivarCamara();
    const area = document.getElementById('pipDisplayArea');

    visionInterval = setInterval(async () => {
        const video = area.querySelector('video');
        if(!video) return;

        const canvas = document.createElement('canvas');
        canvas.width = 320; canvas.height = 240;
        canvas.getContext('2d').drawImage(video, 0, 0, 320, 240);
        const imgData = canvas.toDataURL('image/jpeg');

        // Enviar a backend
        const res = await fetch('/analyze_frame', {
            method: 'POST', body: JSON.stringify({image: imgData}),
            headers: {'Content-Type': 'application/json'}
        });
        const result = await res.json();
        console.log("Daniela Vision:", result.analysis);
    }, 5000); // Análisis cada 5 segundos
}

// C: ANALISTA TÁCTICO (Documentos)
document.getElementById('plusFileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    // Notificar proceso
    window.danielaMostrarEnPIP('html', '<div style="padding:10px;">Analizando documento...</div>');

    const res = await fetch('/analyze_doc', { method: 'POST', body: formData });
    const data = await res.json();

    // Proyectar resumen en PIP
    window.danielaMostrarEnPIP('html', `<div style="color:#fff;">${data.summary}</div>`, 'Análisis Doc');
});
</script>
"""

if "visionInterval" not in html:
    html = html.replace("</body>", vision_script + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Motor de Visión (B) y Análisis Táctico (C) instalados.")
