/**
 * Daniela OS — Jarvis Desktop Overlay
 * Mode 1: Arc Reactor
 * Animated holographic center with rotating rings and particles
 */

class ArcReactorMode {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.rings = [];
    this.particles = null;
    this.coreGlow = null;
    this.innerGlow = null;
    this.outerRing = null;
    this.visible = false;
    this.time = 0;
    this.build();
  }

  build() {
    // Core glow
    const coreGeo = new THREE.SphereGeometry(0.3, 32, 32);
    const coreMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.6 });
    this.coreGlow = new THREE.Mesh(coreGeo, coreMat);
    this.group.add(this.coreGlow);

    const glowGeo = new THREE.SphereGeometry(0.5, 32, 32);
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.15 });
    this.innerGlow = new THREE.Mesh(glowGeo, glowMat);
    this.group.add(this.innerGlow);

    // Rings
    const ringConfigs = [
      { radius: 1.2, tube: 0.02, segments: 64, color: 0x00f0ff, speed: 0.5, axis: 'z' },
      { radius: 1.5, tube: 0.015, segments: 64, color: 0x00f0ff, speed: -0.3, axis: 'z' },
      { radius: 1.8, tube: 0.01, segments: 64, color: 0x00d4e0, speed: 0.2, axis: 'x' },
      { radius: 2.0, tube: 0.008, segments: 64, color: 0x00b0c0, speed: -0.15, axis: 'y' },
    ];

    ringConfigs.forEach(cfg => {
      const geo = new THREE.TorusGeometry(cfg.radius, cfg.tube, 8, cfg.segments);
      const mat = new THREE.MeshBasicMaterial({ color: cfg.color, transparent: true, opacity: 0.6 });
      const ring = new THREE.Mesh(geo, mat);
      ring.userData = { speed: cfg.speed, axis: cfg.axis, baseOpacity: 0.6 };
      this.group.add(ring);
      this.rings.push(ring);
    });

    // Particles
    const count = 200;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const i3 = i * 3;
      const r = 1.0 + Math.random() * 1.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;
      positions[i3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i3 + 2] = r * Math.cos(phi);
      colors[i3] = 0.0;
      colors[i3 + 1] = 0.8 + Math.random() * 0.2;
      colors[i3 + 2] = 0.9 + Math.random() * 0.1;
    }
    const partGeo = new THREE.BufferGeometry();
    partGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    partGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    const partMat = new THREE.PointsMaterial({
      size: 0.03, vertexColors: true, transparent: true, opacity: 0.6,
      blending: THREE.AdditiveBlending
    });
    this.particles = new THREE.Points(partGeo, partMat);
    this.group.add(this.particles);

    // Outer ring
    const outerGeo = new THREE.RingGeometry(2.2, 2.25, 64);
    const outerMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.3, side: THREE.DoubleSide });
    this.outerRing = new THREE.Mesh(outerGeo, outerMat);
    this.group.add(this.outerRing);

    this.scene.add(this.group);
    this.group.visible = false;
  }

  show() {
    this.visible = true;
    this.group.visible = true;
  }

  hide() {
    this.visible = false;
    this.group.visible = false;
  }

  update(time, mouse) {
    if (!this.visible) return;
    this.time = time;

    this.rings.forEach(ring => {
      const { speed, axis } = ring.userData;
      if (axis === 'z') ring.rotation.z += speed * 0.016;
      else if (axis === 'x') ring.rotation.x += speed * 0.016;
      else if (axis === 'y') ring.rotation.y += speed * 0.016;
    });

    if (this.particles) {
      this.particles.rotation.y += 0.002;
      this.particles.rotation.x += 0.001;
    }

    if (this.coreGlow) {
      this.coreGlow.material.opacity = (Math.sin(time * 2) * 0.1 + 0.5);
      this.coreGlow.scale.setScalar(1 + Math.sin(time * 3) * 0.05);
    }

    if (this.innerGlow) {
      this.innerGlow.material.opacity = 0.1 + Math.sin(time * 1.5) * 0.05;
    }

    if (this.outerRing) {
      this.outerRing.material.opacity = 0.2 + Math.sin(time * 2) * 0.1;
      this.outerRing.rotation.z += 0.001;
    }

    // Mouse-tracked rotation
    this.group.rotation.y += (mouse.x * 0.3 - this.group.rotation.y) * 0.02;
    this.group.rotation.x += (mouse.y * 0.15 - this.group.rotation.x) * 0.02;
  }
}

window.ArcReactorMode = ArcReactorMode;
