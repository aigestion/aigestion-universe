import os

path = os.path.expanduser("~/daniela-os/index.html")
with open(path) as f:
    content = f.read()

# Código de Red Neuronal con Sinapsis e Impulsos
synaptic_code = """
        // --- 1. IMAGEN DANIELA ESTÁTICA EN EL NÚCLEO ---
        const textureLoader = new THREE.TextureLoader();
        const danielaTex = textureLoader.load('daniela.png');
        const planeGeo = new THREE.PlaneGeometry(2.0, 2.0);
        const planeMat = new THREE.MeshBasicMaterial({
            map: danielaTex,
            transparent: true,
            opacity: 0.95,
            side: THREE.DoubleSide
        });
        const danielaHolo = new THREE.Mesh(planeGeo, planeMat);
        scene.add(danielaHolo);

        // --- 2. CONEXIONES SINÁPTICAS (LÍNEAS NEURONALES) ---
        const lineMat = new THREE.LineBasicMaterial({
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.25
        });

        // Crear red de conexiones aleatorias entre nodos cercanos
        const linesGeo = new THREE.BufferGeometry();
        const linePositions = [];
        const pArray = particlesGeo.attributes.position.array;

        for (let i = 0; i < count * 3; i += 9) {
            linePositions.push(
                pArray[i], pArray[i+1], pArray[i+2],
                pArray[i+3], pArray[i+4], pArray[i+5]
            );
        }
        linesGeo.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
        const neuralNetwork = new THREE.LineSegments(linesGeo, lineMat);
        scene.add(neuralNetwork);

        // --- 3. ANIMACIÓN DE DISPAROS SINÁPTICOS (NEURAL FLASHES) ---
        function animate3D() {
            requestAnimationFrame(animate3D);
            sphereMesh.rotation.y += 0.0025;
            sphereMesh.rotation.x += 0.0008;
            neuralNetwork.rotation.y += 0.0025;
            neuralNetwork.rotation.x += 0.0008;

            // Impulsos eléctricos / Disparos neuronales dinámicos
            const time = Date.now() * 0.003;
            lineMat.opacity = 0.15 + Math.sin(time * 4) * 0.1;

            if (Math.random() > 0.85) {
                // Ráfaga sináptica
                lineMat.color.setHex(0x38bdf8);
                lineMat.opacity = 0.6 + Math.random() * 0.4;
                particlesMat.size = 0.06;
            } else if (Math.random() > 0.96) {
                # Chispazo de alta energía (nodo activo)
                lineMat.color.setHex(0x38bdf8);
                particlesMat.size = 0.08;
            } else {
                lineMat.color.setHex(0x0284c7);
                particlesMat.size = 0.04;
            }

            renderer.render(scene, camera);
        }
"""

if "function animate3D() {" in content:
    pre_part = content.split("function animate3D() {")[0]
    post_part = content.split("animate3D();")[1]
    content = pre_part + synaptic_code + "\n        animate3D();" + post_part

with open(path, "w") as f:
    f.write(content)

print("🧠 Conexión Neuronal con disparos sinápticos inyectada.")
