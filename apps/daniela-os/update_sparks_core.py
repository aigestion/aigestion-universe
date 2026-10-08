import os

path = os.path.expanduser("~/daniela-os/index.html")
with open(path) as f:
    content = f.read()

# 1. Reducir escala de la cámara/esfera para encajar 100% en pantalla
content = content.replace("camera.position.z = 5;", "camera.position.z = 6.2;")
content = content.replace("camera.position.z = 4.8;", "camera.position.z = 6.2;")

# 2. Inyectar imagen de Daniela estática y chispazos en las partículas
spark_code = """
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

        // --- 2. CHISPAZOS CIBERNÉTICOS EN LAS PARTÍCULAS ---
        function animate3D() {
            requestAnimationFrame(animate3D);
            sphereMesh.rotation.y += 0.003;
            sphereMesh.rotation.x += 0.001;

            // Efecto Chispazo / Flickering cibernético
            particlesMat.opacity = 0.6 + Math.random() * 0.4;
            if (Math.random() > 0.92) {
                particlesMat.size = 0.07 + Math.random() * 0.05; // Pulso/Chispazo
            } else {
                particlesMat.size = 0.04;
            }

            renderer.render(scene, camera);
        }
"""

if "function animate3D() {" in content:
    pre_part = content.split("function animate3D() {")[0]
    post_part = content.split("animate3D();")[1]
    content = pre_part + spark_code + "\n        animate3D();" + post_part

with open(path, "w") as f:
    f.write(content)

print("✅ Chispazos e Imagen Estática integrados con éxito.")
