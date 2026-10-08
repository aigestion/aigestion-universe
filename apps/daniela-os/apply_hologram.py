import os

path = os.path.expanduser("~/daniela-os/index.html")
with open(path) as f:
    content = f.read()

# Código del Holograma
hologram_code = """
        // --- HOLOGRAMA DANIELA ---
        const textureLoader = new THREE.TextureLoader();
        const danielaTex = textureLoader.load('daniela.png');
        const planeGeo = new THREE.PlaneGeometry(1.8, 1.8);
        const planeMat = new THREE.MeshBasicMaterial({
            map: danielaTex, transparent: true, opacity: 0.9, side: THREE.DoubleSide
        });
        const danielaHolo = new THREE.Mesh(planeGeo, planeMat);
        scene.add(danielaHolo);

        // --- ANIMACIÓN CON HOLOGRAMA ---
        function animate3D() {
            requestAnimationFrame(animate3D);
            sphereMesh.rotation.y += 0.004;
            danielaHolo.rotation.y += 0.004;
            renderer.render(scene, camera);
        }
"""

# Reemplazar la función animate original
if "function animate3D() {" in content:
    content = (
        content.split("function animate3D() {")[0]
        + hologram_code
        + "\n        animate3D();"
        + content.split("animate3D();")[1]
    )

with open(path, "w") as f:
    f.write(content)
print("✅ Holograma inyectado correctamente.")
