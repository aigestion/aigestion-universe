import os

os.makedirs("templates", exist_ok=True)

html_code = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>DANIELA OS :: HUD 3D FUTURISTA</title>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>

    <style>
        :root {
            --cyan-glow: #00f3ff;
            --blue-metallic: #0a192f;
            --hud-border: #1e3a8a;
            --text-font: 'Orbitron', sans-serif;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
        }

        body {
            width: 100vw;
            height: 100vh;
            background-color: #020617;
            color: #e2e8f0;
            font-family: 'Rajdhani', sans-serif;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        /* Top HUD Bar Metallic */
        .hud-header {
            position: absolute;
            top: 12px;
            left: 12px;
            right: 12px;
            height: 60px;
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 58, 138, 0.4) 100%);
            border: 1px solid rgba(0, 243, 255, 0.4);
            border-radius: 12px;
            box-shadow: inset 0 0 15px rgba(0, 243, 255, 0.2), 0 8px 25px rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 16px;
            z-index: 10;
            backdrop-filter: blur(10px);
        }

        .hud-title {
            font-family: var(--text-font);
            font-size: 15px;
            font-weight: 900;
            color: var(--cyan-glow);
            letter-spacing: 2px;
            text-shadow: 0 0 10px rgba(0, 243, 255, 0.8);
        }

        .hud-status {
            font-family: var(--text-font);
            font-size: 10px;
            padding: 4px 10px;
            border-radius: 20px;
            border: 1px solid #ff0055;
            color: #ff0055;
            letter-spacing: 1px;
            background: rgba(255, 0, 85, 0.1);
            transition: all 0.3s ease;
        }

        .hud-status.activo {
            border-color: var(--cyan-glow);
            color: var(--cyan-glow);
            background: rgba(0, 243, 255, 0.15);
            box-shadow: 0 0 12px var(--cyan-glow);
        }

        /* 3D Canvas Container */
        #webgl-orb {
            position: absolute;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 1;
        }

        /* Bottom Control Panel */
        .hud-footer {
            position: absolute;
            bottom: 20px;
            left: 12px;
            right: 12px;
            height: 64px;
            background: linear-gradient(0deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 58, 138, 0.5) 100%);
            border: 1px solid rgba(0, 243, 255, 0.4);
            border-radius: 32px;
            display: flex;
            align-items: center;
            padding: 0 8px;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.2);
            z-index: 10;
            backdrop-filter: blur(12px);
        }

        .voice-btn {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: radial-gradient(circle, var(--cyan-glow) 0%, #0077ff 100%);
            border: none;
            color: #000;
            font-family: var(--text-font);
            font-size: 10px;
            font-weight: 900;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 15px var(--cyan-glow);
            cursor: pointer;
        }

        .cmd-input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #fff;
            font-family: 'Rajdhani', sans-serif;
            font-size: 16px;
            padding: 0 16px;
            letter-spacing: 1px;
        }

        .cmd-input::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }

        .send-btn {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(0, 243, 255, 0.3);
            color: var(--cyan-glow);
            font-family: var(--text-font);
            font-size: 11px;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }
    </style>
</head>
<body>

    <header class="hud-header">
        <div class="hud-title">⚡ DANIELA OS</div>
        <div id="hud-status" class="hud-status">○ REPOSO</div>
    </header>

    <div id="webgl-orb"></div>

    <footer class="hud-footer">
        <button class="voice-btn" onclick="activarVoz()">Danie</button>
        <input type="text" id="cmd-input" class="cmd-input" placeholder="COMANDO DE VOZ / TEXTO..." autocomplete="off">
        <button class="send-btn" onclick="enviarComando()">A.I.</button>
    </footer>

    <script src="/static/daniela_os_core_hud.js"></script>
    <script src="/static/daniela_wakeword.js"></script>
    <script src="/static/daniela_haptics.js"></script>

    <script>
        let scene, camera, renderer, orb, innerOrb;

        function init3D() {
            const container = document.getElementById('webgl-orb');
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.z = 4;

            renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            container.appendChild(renderer.domElement);

            // Esfera exterior de malla
            const geometry = new THREE.IcosahedronGeometry(1.5, 3);
            const material = new THREE.MeshBasicMaterial({
                color: 0x00f3ff,
                wireframe: true,
                transparent: true,
                opacity: 0.35
            });
            orb = new THREE.Mesh(geometry, material);
            scene.add(orb);

            // Núcleo brillante interior
            const innerGeo = new THREE.SphereGeometry(0.8, 32, 32);
            const innerMat = new THREE.MeshBasicMaterial({
                color: 0x0077ff,
                wireframe: true,
                transparent: true,
                opacity: 0.75
            });
            innerOrb = new THREE.Mesh(innerGeo, innerMat);
            scene.add(innerOrb);

            animate();
        }

        function animate() {
            requestAnimationFrame(animate);
            if (orb) {
                orb.rotation.x += 0.003;
                orb.rotation.y += 0.005;
            }
            if (innerOrb) {
                innerOrb.rotation.y -= 0.008;
            }
            renderer.render(scene, camera);
        }

        function activarVoz() {
            if (window.actualizarEstadoHUD) window.actualizarEstadoHUD(true);
            if (window.vibrarTelefono) window.vibrarTelefono('sintonizacion');
        }

        function enviarComando() {
            const input = document.getElementById('cmd-input');
            if (input.value.trim() !== '') {
                if (window.vibrarTelefono) window.vibrarTelefono('confirmacion');
                input.value = '';
            }
        }

        window.addEventListener('resize', () => {
            if (camera && renderer) {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            }
        });

        window.onload = init3D;
    </script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_code)

print("✨ [DANIELA OS]: Interface futurista 3D compilada en Termux.")
