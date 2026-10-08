/**
 * Daniela OS — Jarvis Desktop Overlay
 * Mode 2: Globe
 * Wireframe Earth + atmosphere shader + region nodes + data packets
 */

class GlobeMode {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.globe = null;
    this.nodes = [];
    this.connections = [];
    this.packets = [];
    this.stars = null;
    this.visible = false;
    this.time = 0;

    this.regions = [
      { name: 'Madrid', lat: 40.4, lon: -3.7, color: 0x0ea5e9, requests: 1240 },
      { name: 'Mexico City', lat: 19.4, lon: -99.1, color: 0x8b5cf6, requests: 892 },
      { name: 'Tokyo', lat: 35.7, lon: 139.7, color: 0x06b6d4, requests: 2100 },
      { name: 'New York', lat: 40.7, lon: -74.0, color: 0x22c55e, requests: 1800 },
      { name: 'London', lat: 51.5, lon: -0.1, color: 0xf59e0b, requests: 950 },
      { name: 'Sydney', lat: -33.9, lon: 151.2, color: 0xef4444, requests: 670 },
      { name: 'Dubai', lat: 25.2, lon: 55.3, color: 0xec4899, requests: 1100 },
      { name: 'Singapore', lat: 1.3, lon: 103.8, color: 0x14b8a6, requests: 1400 },
      { name: 'Sao Paulo', lat: -23.5, lon: -46.6, color: 0xf97316, requests: 780 },
      { name: 'Berlin', lat: 52.5, lon: 13.4, color: 0xa78bfa, requests: 620 },
    ];

    this.build();
  }

  latLonToVector3(lat, lon, radius) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    return new THREE.Vector3(
      -(radius * Math.sin(phi) * Math.cos(theta)),
      (radius * Math.sin(phi) * Math.sin(theta)),
      (radius * Math.cos(phi))
    );
  }

  build() {
    // Lights
    const ambient = new THREE.AmbientLight(0x404080, 0.3);
    const sun = new THREE.DirectionalLight(0xffffff, 1);
    sun.position.set(5, 3, 5);
    const rim = new THREE.DirectionalLight(0x0ea5e9, 0.5);
    rim.position.set(-5, 0, -5);
    this.group.add(ambient, sun, rim);

    // Globe
    const globeGeo = new THREE.SphereGeometry(1, 128, 128);
    const globeMat = new THREE.MeshPhongMaterial({
      color: 0x0a0a1a, emissive: 0x0a0a2a, specular: 0x0ea5e9, shininess: 100, opacity: 0.95, transparent: true
    });
    this.globe = new THREE.Mesh(globeGeo, globeMat);
    this.group.add(this.globe);

    // Wireframe
    const wireGeo = new THREE.SphereGeometry(1.005, 64, 64);
    const wireMat = new THREE.MeshBasicMaterial({ wireframe: true, color: 0x0ea5e9, opacity: 0.1, transparent: true });
    this.globe.add(new THREE.Mesh(wireGeo, wireMat));

    // Atmosphere
    const atmoGeo = new THREE.SphereGeometry(1.15, 64, 64);
    const atmoMat = new THREE.ShaderMaterial({
      vertexShader: `varying vec3 vNormal; void main() { vNormal = normalize(normalMatrix * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
      fragmentShader: `varying vec3 vNormal; void main() { float intensity = pow(0.6 - dot(vNormal, vec3(0, 0, 1.0)), 2.0); gl_FragColor = vec4(0.05, 0.65, 0.91, 1.0) * intensity * 0.8; }`,
      side: THREE.BackSide, blending: THREE.AdditiveBlending, transparent: true
    });
    this.group.add(new THREE.Mesh(atmoGeo, atmoMat));

    // Region nodes
    this.regions.forEach(region => {
      const pos = this.latLonToVector3(region.lat, region.lon, 1.02);
      const size = 0.02 + region.requests / 50000;

      const nodeGeo = new THREE.SphereGeometry(size, 16, 16);
      const nodeMat = new THREE.MeshBasicMaterial({ color: region.color });
      const node = new THREE.Mesh(nodeGeo, nodeMat);
      node.position.copy(pos);

      const glowGeo = new THREE.SphereGeometry(size * 2.5, 16, 16);
      const glowMat = new THREE.MeshBasicMaterial({ color: region.color, transparent: true, opacity: 0.2 });
      const glow = new THREE.Mesh(glowGeo, glowMat);
      node.add(glow);

      // Label
      const canvas = document.createElement('canvas');
      canvas.width = 256;
      canvas.height = 64;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#0ea5e9';
      ctx.font = 'bold 24px Orbitron, monospace';
      ctx.fillText(region.name, 10, 32);
      const tex = new THREE.CanvasTexture(canvas);
      const spriteMat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.8 });
      const sprite = new THREE.Sprite(spriteMat);
      sprite.position.copy(pos).multiplyScalar(1.3);
      sprite.scale.set(0.4, 0.1, 1);

      node.userData = { glow, baseScale: 1, pulseSpeed: 2 + Math.random() * 2, region };
      this.globe.add(node);
      this.globe.add(sprite);
      this.nodes.push(node);
    });

    // Connection lines
    for (let i = 0; i < this.regions.length; i++) {
      for (let j = i + 1; j < this.regions.length; j++) {
        if (Math.random() > 0.5) continue;
        const start = this.latLonToVector3(this.regions[i].lat, this.regions[i].lon, 1.02);
        const end = this.latLonToVector3(this.regions[j].lat, this.regions[j].lon, 1.02);
        const mid = start.clone().add(end).multiplyScalar(0.5).normalize().multiplyScalar(1.3);
        const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
        const pts = curve.getPoints(50);
        const lineGeo = new THREE.BufferGeometry().setFromPoints(pts);
        const lineMat = new THREE.LineBasicMaterial({ color: 0x334155, transparent: true, opacity: 0.15 });
        const line = new THREE.Line(lineGeo, lineMat);
        this.globe.add(line);
        this.connections.push({ line, start, end, curve });
      }
    }

    // Stars
    const starCount = 2000;
    const starPos = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount; i++) {
      const i3 = i * 3;
      starPos[i3] = (Math.random() - 0.5) * 200;
      starPos[i3 + 1] = (Math.random() - 0.5) * 200;
      starPos[i3 + 2] = (Math.random() - 0.5) * 200;
    }
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
    const starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.05, transparent: true, opacity: 0.5 });
    this.stars = new THREE.Points(starGeo, starMat);
    this.scene.add(this.stars);

    this.scene.add(this.group);
    this.group.visible = false;

    // Spawn packets periodically
    this.packetInterval = null;
  }

  spawnPacket() {
    if (!this.visible || this.connections.length === 0) return;
    const conn = this.connections[Math.floor(Math.random() * this.connections.length)];
    const geo = new THREE.SphereGeometry(0.012, 8, 8);
    const mat = new THREE.MeshBasicMaterial({ color: 0x22c55e, transparent: true, opacity: 0.8 });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(conn.start);
    this.globe.add(mesh);
    this.packets.push({ mesh, start: conn.start, end: conn.end, progress: 0, speed: 0.01 + Math.random() * 0.02 });
  }

  show() {
    this.visible = true;
    this.group.visible = true;
    if (this.stars) this.stars.visible = true;
    this.packetInterval = setInterval(() => this.spawnPacket(), 300);
  }

  hide() {
    this.visible = false;
    this.group.visible = false;
    if (this.stars) this.stars.visible = false;
    if (this.packetInterval) clearInterval(this.packetInterval);
    // Remove packets
    this.packets.forEach(p => this.globe.remove(p.mesh));
    this.packets = [];
  }

  update(time, mouse) {
    if (!this.visible) return;
    this.time = time;

    if (this.globe) {
      this.globe.rotation.y += 0.001;
      this.globe.rotation.x = mouse.y * 0.1;
    }

    this.group.rotation.y += (mouse.x * 0.2 - this.group.rotation.y) * 0.02;

    // Node pulsing
    this.nodes.forEach(node => {
      if (node.userData.glow) {
        node.userData.glow.scale.setScalar(1 + Math.sin(time * node.userData.pulseSpeed) * 0.3);
      }
    });

    // Animate packets
    for (let i = this.packets.length - 1; i >= 0; i--) {
      const p = this.packets[i];
      p.progress += p.speed;
      if (p.progress >= 1) {
        this.globe.remove(p.mesh);
        this.packets.splice(i, 1);
        continue;
      }
      const t = p.progress;
      const oneMinusT = 1 - t;
      const mid = p.start.clone().add(p.end).multiplyScalar(0.5).normalize().multiplyScalar(1.3);
      p.mesh.position.set(
        oneMinusT * oneMinusT * p.start.x + 2 * oneMinusT * t * mid.x + t * t * p.end.x,
        oneMinusT * oneMinusT * p.start.y + 2 * oneMinusT * t * mid.y + t * t * p.end.y,
        oneMinusT * oneMinusT * p.start.z + 2 * oneMinusT * t * mid.z + t * t * p.end.z
      );
    }

    // Connection opacity
    this.connections.forEach((conn, i) => {
      conn.line.material.opacity = 0.1 + Math.sin(time * 2 + i) * 0.05;
    });
  }
}

window.GlobeMode = GlobeMode;
