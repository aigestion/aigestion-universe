import os
import re

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

# 1. Limpiar scripts previos que inyectaban texto en pipDisplayArea
html = re.sub(r"window\.proyectarPresentacionAuto\s*=\s*function.*?\};", "", html, flags=re.DOTALL)

# 2. Inyectar contenedor de vídeo puro y limpio
pure_video_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
        if (!area) return;

        // Limpieza absoluta de texto
        area.innerHTML = `
            <div style="width:100%; height:100%; background:#000; position:relative; overflow:hidden;">
                <canvas id="pureVideoCanvas" style="width:100%; height:100%; display:block;"></canvas>
            </div>
        `;

        const canvas = document.getElementById('pureVideoCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        let t = 0;

        function drawVideoFrame() {
            canvas.width = canvas.clientWidth || 300;
            canvas.height = canvas.clientHeight || 150;

            // Renderizado puro de vídeo abstracto / animación visual
            ctx.fillStyle = '#05070a';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Ondas de vídeo dinámicas
            ctx.lineWidth = 2;
            for (let i = 0; i < 5; i++) {
                ctx.strokeStyle = `hsla(${(t + i * 40) % 360}, 100%, 50%, 0.8)`;
                ctx.beginPath();
                for (let x = 0; x < canvas.width; x += 5) {
                    let y = Math.sin((x + t * 3 + i * 20) * 0.03) * 15 + (canvas.height / 2);
                    if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                }
                ctx.stroke();
            }

            t++;
            requestAnimationFrame(drawVideoFrame);
        }
        drawVideoFrame();
    }, 300);
});
</script>
"""

if "pureVideoCanvas" not in html:
    html = html.replace("</body>", pure_video_script + "\n<!-- pure_video -->\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ PIP Master reconfigurado a señal de vídeo puro.")
