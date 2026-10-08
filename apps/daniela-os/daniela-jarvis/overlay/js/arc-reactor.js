/**
 * Daniela OS — Jarvis Desktop Overlay
 * Arc Reactor Core (Three.js)
 * Animated holographic center with rotating rings and particles
 */

class ArcReactor {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(60, 1, 0.1, 1000);
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      alpha: true,
      antialias: true
    });

    this.rings = [];
    this.particles = null;
    this.coreGlow = null;
    this.time = 0;
    this.intensity = 1.0;

    this.init();
  }

  init() {
    this.renderer.setSize(400, 400);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setClearColor(0x000000, 0);

    this.camera.position.z = 5;

    this.createCoreGlow();
    this.createRings();
    this.createParticles();
    this.createOuterRing();

    this.animate();
  }

  createCoreGlow() {
    const geometry = new THREE.SphereGeometry(0.3, 32, 32);
    const material = new THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.6
    });
    this.coreGlow = new THREE.Mesh(geometry, material);
    this.scene.add(this.coreGlow);

    // Inner glow
    const glowGeo = new THREE.SphereGeometry(0.5, 32, 32);
    const glowMat = new THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.15
    });
    this.innerGlow = new THREE.Mesh(glowGeo, glowMat);
    this.scene.add(this.innerGlow);
  }

  createRings() {
    const ringConfigs = [
      { radius: 1.2, tube: 0.02, segments: 64, color: 0x00f0ff, speed: 0.5, axis: 'z' },
      { radius: 1.5, tube: 0.015, segments: 64, color: 0x00f0ff, speed: -0.3, axis: 'z' },
      { radius: 1.8, tube: 0.01, segments: 64, color: 0x00d4e0, speed: 0.2, axis: 'x' },
      { radius: 2.0, tube: 0.008, segments: 64, color: 0x00b0c0, speed: -0.15, axis: 'y' },
    ];

    ringConfigs.forEach(cfg => {
      const geometry = new THREE.TorusGeometry(cfg.radius, cfg.tube, 8, cfg.segments);
      const material = new THREE.MeshBasicMaterial({
        color: cfg.color,
        transparent: true,
        opacity: 0.6
      });
      const ring = new THREE.Mesh(geometry, material);
      ring.userData = { speed: cfg.speed, axis: cfg.axis, baseOpacity: 0.6 };
      this.scene.add(ring);
      this.rings.push(ring);
    });
  }

  createParticles() {
    const count = 200;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      const i3 = i * 3;
      const radius = 1.0 + Math.random() * 1.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;

      positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i3 + 2] = radius * Math.cos(phi);

      // Cyan-ish colors
      colors[i3] = 0.0;
      colors[i3 + 1] = 0.8 + Math.random() * 0.2;
      colors[i3 + 2] = 0.9 + Math.random() * 0.1;
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 0.03,
      vertexColors: true,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending
    });

    this.particles = new THREE.Points(geometry, material);
    this.scene.add(this.particles);
  }

  createOuterRing() {
    const geometry = new THREE.RingGeometry(2.2, 2.25, 64);
    const material = new THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.3,
      side: THREE.DoubleSide
    });
    this.outerRing = new THREE.Mesh(geometry, material);
    this.scene.add(this.outerRing);
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    this.time += 0.016;

    // Rotate rings
    this.rings.forEach(ring => {
      const { speed, axis } = ring.userData;
      if (axis === 'z') ring.rotation.z += speed * 0.016;
      else if (axis === 'x') ring.rotation.x += speed * 0.016;
      else if (axis === 'y') ring.rotation.y += speed * 0.016;
    });

    // Rotate particles
    if (this.particles) {
      this.particles.rotation.y += 0.002;
      this.particles.rotation.x += 0.001;
    }

    // Pulse core glow
    if (this.coreGlow) {
      const pulse = Math.sin(this.time * 2) * 0.1 + 0.5;
      this.coreGlow.material.opacity = pulse * this.intensity;
      this.coreGlow.scale.setScalar(1 + Math.sin(this.time * 3) * 0.05);
    }

    // Pulse inner glow
    if (this.innerGlow) {
      this.innerGlow.material.opacity = 0.1 + Math.sin(this.time * 1.5) * 0.05;
    }

    // Pulse outer ring
    if (this.outerRing) {
      this.outerRing.material.opacity = 0.2 + Math.sin(this.time * 2) * 0.1;
      this.outerRing.rotation.z += 0.001;
    }

    this.renderer.render(this.scene, this.camera);
  }

  setIntensity(val) {
    this.intensity = Math.max(0, Math.min(1, val));
    this.rings.forEach(ring => {
      ring.material.opacity = ring.userData.baseOpacity * this.intensity;
    });
  }

  pulse() {
    this.intensity = 1.5;
    setTimeout(() => { this.intensity = 1.0; }, 500);
  }
}

window.ArcReactor = ArcReactor;
