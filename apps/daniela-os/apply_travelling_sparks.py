import os

path = os.path.expanduser("~/daniela-os/index.html")
with open(path) as f:
    html = f.read()

synapses_pulse_js = """
        // --- RED NEURONAL CON IMPULSOS DE ENERGÍA VIAJEROS & CHISPAZOS SUTILES ---
        const pArray = particlesGeo.attributes.position.array;
        const numParticles = count;

        // Construir aristas / axones entre neuronas cercanas
        const connections = [];
        const linePositions = [];

        for (let i = 0; i < numParticles; i++) {
            const ix = pArray[i*3], iy = pArray[i*3+1], iz = pArray[i*3+2];
            for (let j = i + 1; j < numParticles; j++) {
                const jx = pArray[j*3], jy = pArray[j*3+1], jz = pArray[j*3+2];
                const dx = ix - jx, dy = iy - jy, dz = iz - jz;
                const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
                if (dist < 0.85) {
                    connections.push({ p1: i, p2: j, dist: dist });
                    linePositions.push(ix, iy, iz, jx, jy, jz);
                }
            }
        }

        // Estructura de red de conexiones (axones)
        const linesGeo = new THREE.BufferGeometry();
        linesGeo.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
        const lineMat = new THREE.LineBasicMaterial({
            color: 0x0284c7,
            transparent: true,
            opacity: 0.15,
            blending: THREE.AdditiveBlending
        });
        const neuralNetwork = new THREE.LineSegments(linesGeo, lineMat);
        scene.add(neuralNetwork);

        // Chispas viajeras individuales (Action Potentials / Impulsos Viajeros)
        const numSparks = 18;
        const sparkGeo = new THREE.BufferGeometry();
        const sparkPositions = new Float32Array(numSparks * 3);
        sparkGeo.setAttribute('position', new THREE.BufferAttribute(sparkPositions, 3));

        const sparkMat = new THREE.PointsMaterial({
            size: 0.08,
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.9,
            blending: THREE.AdditiveBlending
        });
        const sparkMesh = new THREE.Points(sparkGeo, sparkMat);
        scene.add(sparkMesh);

        // Inicializar impulsos viajeros
        const pulses = [];
        for (let k = 0; k < numSparks; k++) {
            const conn = connections[Math.floor(Math.random() * connections.length)] || { p1: 0, p2: 1 };
            pulses.push({
                conn: conn,
                progress: Math.random(),
                speed: 0.012 + Math.random() * 0.02,
                sparkIdx: k
            });
        }

        // --- ANIMACIÓN DE IMPULSOS DE ENERGÍA Y CHISPAZOS INDIVIDUALES ---
        function animate3D() {
            requestAnimationFrame(animate3D);

            // Rotación suave del campo neuronal
            sphereMesh.rotation.y += 0.002;
            sphereMesh.rotation.x += 0.0006;
            neuralNetwork.rotation.y += 0.002;
            neuralNetwork.rotation.x += 0.0006;
            sparkMesh.rotation.y += 0.002;
            sparkMesh.rotation.x += 0.0006;

            // Actualizar trayectoria de cada chispa individual entre neuronas
            const sparkPosArr = sparkGeo.attributes.position.array;

            for (let k = 0; k < numSparks; k++) {
                const p = pulses[k];
                p.progress += p.speed;

                if (p.progress >= 1.0) {
                    // El impulso llegó a su neurona destino: saltar a una nueva conexión adyacente
                    p.progress = 0;
                    const nextConn = connections[Math.floor(Math.random() * connections.length)];
                    if (nextConn) p.conn = nextConn;
                    p.speed = 0.012 + Math.random() * 0.02;
                }

                const i1 = p.conn.p1, i2 = p.conn.p2;
                const x1 = pArray[i1*3], y1 = pArray[i1*3+1], z1 = pArray[i1*3+2];
                const x2 = pArray[i2*3], y2 = pArray[i2*3+1], z2 = pArray[i2*3+2];

                // Posición interpolada del impulso viajero
                sparkPosArr[k*3] = x1 + (x2 - x1) * p.progress;
                sparkPosArr[k*3+1] = y1 + (y2 - y1) * p.progress;
                sparkPosArr[k*3+2] = z1 + (z2 - z1) * p.progress;
            }

            sparkGeo.attributes.position.needsUpdate = true;

            // Micro-flicker sutil en la intensidad del impulso
            sparkMat.opacity = 0.75 + Math.sin(Date.now() * 0.008) * 0.2;

            renderer.render(scene, camera);
        }
"""

if "function animate3D() {" in html:
    pre = html.split("function animate3D() {")[0]
    post = html.split("animate3D();")[1]
    with open(path, "w") as f:
        f.write(pre + synapses_pulse_js + "        animate3D();" + post)
    print("✅ Impulsos viajeros inyectados.")
