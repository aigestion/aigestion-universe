#!/bin/bash
# Script de inyección para Holograma Local 2D en Three.js

sed -i 's/const sphereMesh = new THREE.Points(particlesGeo, particlesMat);/const sphereMesh = new THREE.Points(particlesGeo, particlesMat);\n\n\/\/ Holograma Local Daniela\nconst planeGeo = new THREE.PlaneGeometry(1.8, 1.8);\nconst textureLoader = new THREE.TextureLoader();\nconst danielaTex = textureLoader.load("daniela.png");\nconst planeMat = new THREE.MeshBasicMaterial({ map: danielaTex, transparent: true, opacity: 0.85, side: THREE.DoubleSide });\nconst danielaHolo = new THREE.Mesh(planeGeo, planeMat);\nscene.add(danielaHolo);/g' ~/daniela-os/index.html

echo "✅ Holograma local inyectado."
