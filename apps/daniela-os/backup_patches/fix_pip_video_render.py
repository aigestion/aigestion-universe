import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

# Renderizador de vídeo animado en Canvas para el PIP Master
video_pip_engine = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Sobrescribir el visor para que muestre el reproductor de vídeo animado
    const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
    if (!area) return;

    area.innerHTML = `
        <div style="position:relative; width:100%; height:100%; background:#050508; overflow:hidden;">
            <canvas id="pipVideoCanvas" style="width:100%; height:100%; display:block;"></canvas>
            <div style="position:absolute; bottom:6px; left:8px; right:8px; display:flex; justify-content:space-between; align-items:center; z-index:10;">
                <span style="color:#00ffcc; font-family:monospace; font-size:0.6rem; background:rgba(0,0,0,0.7); padding:2px 4px; border-radius:2px;">⏺ LIVE VIDEO KEYNOTE</span>
                <button onclick="fetch('/apply_suggestion',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:'// patch'})}).then(()=>alert('✅ Propuesta Aprobada'));" style="background:#00ffcc; color:#000; border:none; padding:4px 8px; font-weight:bold; font-size:0.6rem; border-radius:3px; cursor:pointer;">APROBAR</button>
            </div>
        </div>
    `;

    // Motor de Renderizado de Vídeo Holográfico a 60 FPS
    const canvas = document.getElementById('pipVideoCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let frame = 0;
    const slides = [
        "MÓDULO 1: STEALTH OLED",
        "MÓDULO 2: SOVEREIGN GLASS",
        "MÓDULO 3: SELF-HEALING UI"
    ];

    function renderVideo() {
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;

        // Fondo y rejilla Cyberpunk
        ctx.fillStyle = '#080910';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Renderizado de partículas/ondas animadas
        ctx.strokeStyle = 'rgba(0, 255, 204, 0.2)';
        ctx.beginPath();
        for (let x = 0; x < canvas.width; x += 15) {
            let y = Math.sin((x + frame * 2) * 0.05) * 10 + (canvas.height / 2);
            if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke();

        // Texto animado del vídeo
        let currentSlide = slides[Math.floor((frame / 120) % slides.length)];
        ctx.fillStyle = '#00ffcc';
        ctx.font = 'bold 11px monospace';
        ctx.shadowColor = '#00ffcc';
        ctx.shadowBlur = 8;
        ctx.fillText("⚡ DANIELA OS PRESENTACIÓN", 10, 22);

        ctx.fillStyle = '#ff0055';
        ctx.font = 'bold 10px monospace';
        ctx.fillText(currentSlide, 10, 42);

        ctx.fillStyle = '#ffffff';
        ctx.font = '9px monospace';
        ctx.shadowBlur = 0;
        ctx.fillText("Procesando propuesta en vivo...", 10, 60);

        frame++;
        requestAnimationFrame(renderVideo);
    }

    renderVideo();
});
</script>
"""

# Reemplazar e inyectar el motor de vídeo en vivo
if "pipVideoCanvas" not in html:
    html = html.replace("</body>", video_pip_engine + "\n<!-- video_pip_engine -->\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Motor de vídeo en vivo instalado en el PIP Master.")
