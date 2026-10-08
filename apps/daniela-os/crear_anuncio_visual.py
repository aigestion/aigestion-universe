import os

MEDIA_DIR = os.path.expanduser("~/daniela-os/media")

# Crear la landing del Anuncio Comercial Táctico
html_anuncio = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daniela OS - Anuncio Comercial Táctico</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background-color: #05070d; color: #00ffff; font-family: 'Segoe UI', Tahoma, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; text-align: center; }
        h1 { font-size: 1.8rem; margin-bottom: 8px; color: #ffffff; text-shadow: 0 0 12px #00ffff; }
        p { color: #ff00ff; font-size: 0.95rem; margin-bottom: 20px; letter-spacing: 1px; }

        .video-container { position: relative; width: 100%; max-width: 380px; aspect-ratio: 9/16; background: #000; border: 2px solid #00ffff; border-radius: 16px; overflow: hidden; box-shadow: 0 0 30px rgba(0, 255, 255, 0.3); margin-bottom: 20px; }
        video { width: 100%; height: 100%; object-fit: cover; }

        .controls { display: flex; gap: 10px; width: 100%; max-width: 380px; flex-wrap: wrap; }
        button { flex: 1; padding: 14px; border: none; border-radius: 10px; font-weight: bold; font-size: 0.9rem; cursor: pointer; text-transform: uppercase; transition: all 0.2s ease; }
        .btn-play { background: linear-gradient(135deg, #00ffff, #0088ff); color: #000; box-shadow: 0 0 15px rgba(0, 255, 255, 0.4); }
        .btn-switch { background: #161f33; color: #ff00ff; border: 1px solid #ff00ff; }
        button:active { transform: scale(0.96); }
    </style>
</head>
<body>

    <h1>DANIELA OS</h1>
    <p>AIGESTION.NET — CIBER-EJECUTIVO</p>

    <div class="video-container">
        <video id="player" controls playsinline preload="auto">
            <source src="/vids_master_real.mp4" type="video/mp4">
            Tu navegador no soporta el formato de vídeo.
        </video>
    </div>

    <div class="controls">
        <button class="btn-play" onclick="playVideo()">▶ REPRODUCIR ANUNCIO VISUAL</button>
        <button class="btn-switch" onclick="toggleSource()">🔄 CAMBIAR ARCHIVO</button>
    </div>

    <script>
        const player = document.getElementById('player');
        let currentSrc = '/vids_master_real.mp4';

        function playVideo() {
            player.play();
            if (player.requestFullscreen) {
                player.requestFullscreen();
            } else if (player.webkitRequestFullscreen) {
                player.webkitRequestFullscreen();
            }
        }

        function toggleSource() {
            if (currentSrc === '/vids_master_real.mp4') {
                currentSrc = '/storyboard_android.mp4';
            } else {
                currentSrc = '/vids_master_real.mp4';
            }
            player.src = currentSrc;
            player.play();
        }
    </script>
</body>
</html>
"""

with open(os.path.join(MEDIA_DIR, "anuncio.html"), "w", encoding="utf-8") as f:
    f.write(html_anuncio)

print("✨ [ANUNCIO LISTO]: Interfaz visual con control táctil generada correctamente.")
