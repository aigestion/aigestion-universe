/**
 * Daniela OS — Jarvis Desktop Overlay
 * Mode 4: Planetary System
 * 12 planets in 3 tiers + satellites + sub-satellites + drag + focus zoom
 */

class PlanetaryMode {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.planets = [];
    this.satellites = [];
    this.subSatellites = [];
    this.connections = [];
    this.labels = [];
    this.coreParticles = null;
    this.visible = false;
    this.time = 0;
    this.focusedPlanet = null;

    this.BASE_NODES = [
      { id: 'g1', name: 'ECOSISTEMA GOOGLE', icon: '🌐', color: '#00f0ff', rx: 2.2, ry: 3.2, angle: 0,
        sats: [{ name: 'Drive', icon: '📁', subs: ['Sincro', 'Nube'] }, { name: 'Gmail', icon: '✉️', subs: ['Filtros'] }, { name: 'Calendar', icon: '📅', subs: [] }, { name: 'YouTube', icon: '▶️', subs: ['Analytics'] }] },
      { id: 'g2', name: 'INTELIGENCIA', icon: '🧠', color: '#8b5cf6', rx: 2.2, ry: 3.2, angle: Math.PI / 2,
        sats: [{ name: 'OpenAI', icon: '🤖', subs: ['GPT-4'] }, { name: 'Gemini', icon: '💎', subs: [] }, { name: 'Claude', icon: '🎭', subs: [] }] },
      { id: 'g3', name: 'DESARROLLO', icon: '💻', color: '#22c55e', rx: 2.2, ry: 3.2, angle: Math.PI,
        sats: [{ name: 'GitHub', icon: '🐙', subs: ['PRs'] }, { name: 'Docker', icon: '🐳', subs: ['Containers'] }, { name: 'VS Code', icon: '📝', subs: [] }] },
      { id: 'g4', name: 'FINANZAS', icon: '💰', color: '#f59e0b', rx: 2.2, ry: 3.2, angle: Math.PI * 1.5,
        sats: [{ name: 'Stripe', icon: '💳', subs: ['Pagos'] }, { name: 'Banco', icon: '🏦', subs: [] }] },
      { id: 'g5', name: 'COMUNICACION', icon: '📢', color: '#ef4444', rx: 3.8, ry: 5.8, angle: Math.PI / 4,
        sats: [{ name: 'Slack', icon: '💬', subs: [] }, { name: 'Twitter', icon: '🐦', subs: [] }, { name: 'Discord', icon: '🎮', subs: [] }] },
      { id: 'g6', name: 'CREATIVIDAD', icon: '🎨', color: '#ec4899', rx: 3.8, ry: 5.8, angle: Math.PI * 0.75,
        sats: [{ name: 'Blender', icon: '🧊', subs: ['Render'] }, { name: 'Figma', icon: '🎯', subs: [] }] },
      { id: 'g7', name: 'CONOCIMIENTO', icon: '📚', color: '#14b8a6', rx: 3.8, ry: 5.8, angle: Math.PI * 1.25,
        sats: [{ name: 'Notion', icon: '📋', subs: ['Docs'] }, { name: 'Obsidian', icon: '🔮', subs: [] }] },
      { id: 'g8', name: 'MONITOREO', icon: '📊', color: '#f97316', rx: 3.8, ry: 5.8, angle: Math.PI * 1.75,
        sats: [{ name: 'Grafana', icon: '📈', subs: [] }, { name: 'Prometheus', icon: '🔥', subs: [] }] },
      { id: 'g9', name: 'SEGURIDAD', icon: '🔒', color: '#6366f1', rx: 5.2, ry: 8.2, angle: 0.3,
        sats: [{ name: 'Vault', icon: '🗝️', subs: [] }, { name: 'Firewall', icon: '🛡️', subs: [] }] },
      { id: 'g10', name: 'INFRAESTRUCTURA', icon: '🏗️', color: '#0ea5e9', rx: 5.2, ry: 8.2, angle: Math.PI * 0.6,
        sats: [{ name: 'AWS', icon: '☁️', subs: ['EC2', 'S3'] }, { name: 'K8s', icon: '⚙️', subs: [] }] },
      { id: 'g11', name: 'AUTOMATIZACION', icon: '⚡', color: '#eab308', rx: 5.2, ry: 8.2, angle: Math.PI * 1.2,
        sats: [{ name: 'Zapier', icon: '🔗', subs: [] }, { name: 'Cron', icon: '⏰', subs: [] }] },
      { id: 'g12', name: 'IOT & HARDWARE', icon: '📡', color: '#10b981', rx: 5.2, ry: 8.2, angle: Math.PI * 1.7,
        sats: [{ name: 'Termux', icon: '📱', subs: [] }, { name: 'Sensors', icon: '🌡️', subs: [] }] },
    ];

    this._tempV = new THREE.Vector3();
    this.build();
  }

  build() {
    // Core particles
    const coreCount = 800;
    const corePos = new Float32Array(coreCount * 3);
    for (let i = 0; i < coreCount; i++) {
      const i3 = i * 3;
      const r = 0.5 + Math.random() * 0.3;
      const u = Math.random(), v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      corePos[i3] = r * Math.sin(phi) * Math.cos(theta);
      corePos[i3 + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.85;
      corePos[i3 + 2] = r * Math.cos(phi);
    }
    const coreGeo = new THREE.BufferGeometry();
    coreGeo.setAttribute('position', new THREE.BufferAttribute(corePos, 3));
    const coreMat = new THREE.PointsMaterial({
      color: 0x00f0ff, size: 0.035, transparent: true, opacity: 0.9,
      blending: THREE.AdditiveBlending
    });
    this.coreParticles = new THREE.Points(coreGeo, coreMat);
    this.group.add(this.coreParticles);

    // Planets
    this.BASE_NODES.forEach(node => {
      const x = Math.cos(node.angle) * node.rx;
      const y = Math.sin(node.angle) * node.ry;

      // Planet mesh
      const geo = new THREE.SphereGeometry(0.12, 16, 16);
      const mat = new THREE.MeshBasicMaterial({ color: node.color });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(x, y, 0);
      mesh.userData = { node, basePos: new THREE.Vector3(x, y, 0) };
      this.group.add(mesh);

      // Connection line
      const lineGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 0, 0), mesh.position
      ]);
      const lineMat = new THREE.LineBasicMaterial({ color: node.color, transparent: true, opacity: 0.2 });
      const line = new THREE.Line(lineGeo, lineMat);
      this.group.add(line);
      this.connections.push(line);

      // HTML label
      const label = document.createElement('div');
      label.className = 'planet-label';
      label.innerHTML = `<span style="color:${node.color}">${node.icon}</span> ${node.name}`;
      label.style.cssText = `position:fixed;color:#e2e8f0;font-family:'Share Tech Mono',monospace;font-size:10px;pointer-events:none;opacity:0.7;text-shadow:0 0 8px ${node.color};letter-spacing:1px;white-space:nowrap;`;
      document.body.appendChild(label);

      this.planets.push({ mesh, line, label, node, satellites: [] });

      // Satellites
      node.sats.forEach((sat, si) => {
        const orbAngle = (si / node.sats.length) * Math.PI * 2;
        const satGeo = new THREE.SphereGeometry(0.06, 12, 12);
        const satMat = new THREE.MeshBasicMaterial({ color: node.color, transparent: true, opacity: 0.7 });
        const satMesh = new THREE.Mesh(satGeo, satMat);
        satMesh.visible = false;

        const satLabel = document.createElement('div');
        satLabel.className = 'satellite-label';
        satLabel.textContent = `${sat.icon} ${sat.name}`;
        satLabel.style.cssText = `position:fixed;color:#e2e8f0;font-family:'Share Tech Mono',monospace;font-size:8px;pointer-events:none;opacity:0.5;text-shadow:0 0 4px ${node.color};display:none;`;
        document.body.appendChild(satLabel);

        this.group.add(satMesh);
        this.satellites.push({ mesh: satMesh, label: satLabel, parent: mesh, orbAngle, orbRadius: 0.95, node });

        // Sub-satellites
        sat.subs.forEach((sub, subi) => {
          const subAngle = (subi / sat.subs.length) * Math.PI * 2;
          const subGeo = new THREE.SphereGeometry(0.03, 8, 8);
          const subMat = new THREE.MeshBasicMaterial({ color: node.color, transparent: true, opacity: 0.5 });
          const subMesh = new THREE.Mesh(subGeo, subMat);
          subMesh.visible = false;

          const subLabel = document.createElement('div');
          subLabel.className = 'subsatellite-label';
          subLabel.textContent = sub;
          subLabel.style.cssText = `position:fixed;color:#e2e8f0;font-family:'Share Tech Mono',monospace;font-size:7px;pointer-events:none;opacity:0.4;display:none;`;
          document.body.appendChild(subLabel);

          this.group.add(subMesh);
          this.subSatellites.push({ mesh: subMesh, label: subLabel, parent: satMesh, subAngle, orbRadius: 0.35 });
        });
      });
    });

    this.scene.add(this.group);
    this.group.visible = false;
  }

  show() {
    this.visible = true;
    this.group.visible = true;
    this.planets.forEach(p => p.label.style.display = '');
  }

  hide() {
    this.visible = false;
    this.group.visible = false;
    this.planets.forEach(p => {
      p.label.style.display = 'none';
      p.satellites.forEach(s => {
        s.label.style.display = 'none';
        s.mesh.visible = false;
      });
    });
    this.satellites.forEach(s => s.label.style.display = 'none');
    this.subSatellites.forEach(s => {
      s.label.style.display = 'none';
      s.mesh.visible = false;
    });
  }

  update(time, mouse) {
    if (!this.visible) return;
    this.time = time;

    // Core particles rotation
    if (this.coreParticles) {
      this.coreParticles.rotation.y += 0.0004;
    }

    // Satellite orbits
    this.satellites.forEach(sat => {
      sat.orbAngle += 0.003;
      if (sat.parent.visible) {
        sat.mesh.visible = true;
        sat.label.style.display = '';
        sat.mesh.position.x = sat.parent.position.x + Math.cos(sat.orbAngle) * sat.orbRadius;
        sat.mesh.position.y = sat.parent.position.y + Math.sin(sat.orbAngle) * sat.orbRadius;
        sat.mesh.position.z = -0.15;
      } else if (!this.focusedPlanet) {
        sat.mesh.visible = false;
        sat.label.style.display = 'none';
      }
    });

    // Sub-satellite orbits
    this.subSatellites.forEach(sub => {
      sub.subAngle += 0.006;
      if (sub.parent.visible) {
        sub.mesh.visible = true;
        sub.label.style.display = '';
        sub.mesh.position.x = sub.parent.position.x + Math.cos(sub.subAngle) * sub.orbRadius;
        sub.mesh.position.y = sub.parent.position.y + Math.sin(sub.subAngle) * sub.orbRadius;
        sub.mesh.position.z = -0.25;
      } else {
        sub.mesh.visible = false;
        sub.label.style.display = 'none';
      }
    });

    // Label projection
    const camera = this.scene.parent?.camera || window._jarvisCamera;
    if (camera) {
      this.planets.forEach(p => {
        this._tempV.set(0, 0, 0);
        p.mesh.getWorldPosition(this._tempV);
        this._tempV.project(camera);
        p.label.style.left = `${(this._tempV.x * 0.5 + 0.5) * window.innerWidth}px`;
        p.label.style.top = `${(-this._tempV.y * 0.5 + 0.5) * window.innerHeight}px`;
        p.label.style.transform = 'translate(-50%, -50%)';
        p.label.style.display = this._tempV.z < 1 ? '' : 'none';
      });

      this.satellites.forEach(s => {
        if (!s.mesh.visible) return;
        this._tempV.copy(s.mesh.position);
        this._tempV.applyMatrix4(this.group.matrixWorld);
        this._tempV.project(camera);
        s.label.style.left = `${(this._tempV.x * 0.5 + 0.5) * window.innerWidth}px`;
        s.label.style.top = `${(-this._tempV.y * 0.5 + 0.5) * window.innerHeight}px`;
        s.label.style.transform = 'translate(-50%, -50%)';
        s.label.style.display = this._tempV.z < 1 ? '' : 'none';
      });
    }
  }
}

window.PlanetaryMode = PlanetaryMode;
