/**
 * Daniela OS — Jarvis Desktop Overlay
 * Mode 3: Neural Core
 * 480 particles + 32 instanced photons + 13 skill nodes + connectors
 */

class NeuralCoreMode {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.neuralCluster = null;
    this.photons = null;
    this.skillNodes = [];
    this.skillLabels = [];
    this.ragRing = null;
    this.photonPaths = [];
    this.visible = false;
    this.time = 0;
    this.speaking = false;

    this.SKILLS = [
      { id: 'YOUTUBE', label: 'YOUTUBE', color: 0xff0033 },
      { id: 'GMAIL', label: 'GMAIL', color: 0xff4444 },
      { id: 'DRIVE', label: 'DRIVE', color: 0x22c55e },
      { id: 'CALENDAR', label: 'CAL', color: 0x3b82f6 },
      { id: 'SLACK', label: 'SLACK', color: 0xe015c3 },
      { id: 'GITHUB', label: 'GITHUB', color: 0xffffff },
      { id: 'NOTION', label: 'NOTION', color: 0xf59e0b },
      { id: 'OPENAI', label: 'OPENAI', color: 0x10b981 },
      { id: 'BLENDER', label: 'BLENDER', color: 0xf97316 },
      { id: 'STRIPE', label: 'STRIPE', color: 0x6366f1 },
      { id: 'DOCKER', label: 'DOCKER', color: 0x0ea5e9 },
      { id: 'TWITTER', label: 'TWITTER', color: 0x1da1f2 },
      { id: 'OBSIDIAN', label: 'OBS', color: 0x8b5cf6 },
    ];

    this._tempV = new THREE.Vector3();
    this._tempP0 = new THREE.Vector3();
    this._tempP1 = new THREE.Vector3();
    this._tempP2 = new THREE.Vector3();
    this._outBezier = new THREE.Vector3();

    this.build();
  }

  computeBezier(p0, p1, p2, t) {
    const u = 1 - t;
    this._outBezier.set(
      u * u * p0.x + 2 * u * t * p1.x + t * t * p2.x,
      u * u * p0.y + 2 * u * t * p1.y + t * t * p2.y,
      u * u * p0.z + 2 * u * t * p1.z + t * t * p2.z
    );
    return this._outBezier;
  }

  build() {
    // Core lights
    const ambient = new THREE.AmbientLight(0x404080, 0.3);
    this.group.add(ambient);

    // Neural cluster - 480 particles on sphere
    const clusterCount = 480;
    const clusterPos = new Float32Array(clusterCount * 3);
    for (let i = 0; i < clusterCount; i++) {
      const i3 = i * 3;
      const u = Math.random(), v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = 0.42 + Math.random() * 0.1;
      clusterPos[i3] = r * Math.sin(phi) * Math.cos(theta);
      clusterPos[i3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      clusterPos[i3 + 2] = r * Math.cos(phi);
    }
    const clusterGeo = new THREE.BufferGeometry();
    clusterGeo.setAttribute('position', new THREE.BufferAttribute(clusterPos, 3));
    const clusterMat = new THREE.PointsMaterial({
      color: 0x00f0ff, size: 0.024, transparent: true, opacity: 0.85,
      blending: THREE.AdditiveBlending
    });
    this.neuralCluster = new THREE.Points(clusterGeo, clusterMat);
    this.group.add(this.neuralCluster);

    // RAG ring
    const ragGeo = new THREE.RingGeometry(0.58, 0.60, 32);
    const ragMat = new THREE.MeshBasicMaterial({ color: 0xe024c3, side: THREE.DoubleSide, transparent: true, opacity: 0.6 });
    this.ragRing = new THREE.Mesh(ragGeo, ragMat);
    this.ragRing.rotation.x = Math.PI / 2;
    this.group.add(this.ragRing);

    // CPU thread satellites
    this.threadSatellites = [];
    for (let i = 0; i < 4; i++) {
      const angle = (i / 4) * Math.PI * 2;
      const radius = 0.72 + Math.random() * 0.15;
      const geo = new THREE.SphereGeometry(0.025, 6, 6);
      const mat = new THREE.MeshBasicMaterial({ color: 0xffaa00 });
      const sat = new THREE.Mesh(geo, mat);
      sat.userData = { angle, radius };
      this.group.add(sat);
      this.threadSatellites.push(sat);
    }

    // Skill nodes on fibonacci sphere
    this.SKILLS.forEach((skill, idx) => {
      const phi = Math.acos(-1 + (2 * idx) / this.SKILLS.length);
      const theta = Math.sqrt(this.SKILLS.length * Math.PI) * phi;
      const r = 1.35;

      const pos = new THREE.Vector3(
        r * Math.sin(phi) * Math.cos(theta),
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi)
      );

      // Node mesh
      const nodeGeo = new THREE.SphereGeometry(0.042, 6, 6);
      const nodeMat = new THREE.MeshBasicMaterial({ color: skill.color });
      const node = new THREE.Mesh(nodeGeo, nodeMat);
      node.position.copy(pos);
      this.group.add(node);
      this.skillNodes.push({ mesh: node, skill, pos });

      // Connector line
      const dir = pos.clone().normalize();
      const len = pos.length();
      const lineGeo = new THREE.CylinderGeometry(0.003, 0.003, len, 4);
      const lineMat = new THREE.MeshBasicMaterial({ color: skill.color, transparent: true, opacity: 0.3 });
      const line = new THREE.Mesh(lineGeo, lineMat);
      line.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
      this.group.add(line);

      // HTML label
      const label = document.createElement('div');
      label.className = 'neural-skill-label';
      label.textContent = skill.label;
      label.style.cssText = `position:fixed;color:#e2e8f0;font-family:'Share Tech Mono',monospace;font-size:9px;pointer-events:none;opacity:0.6;text-shadow:0 0 6px #00f0ff;letter-spacing:1px;`;
      document.body.appendChild(label);
      this.skillLabels.push({ el: label, pos });
    });

    // Instanced photons
    const PHOTON_COUNT = 32;
    const photonGeo = new THREE.SphereGeometry(0.02, 4, 4);
    const photonMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.8 });
    this.photons = new THREE.InstancedMesh(photonGeo, photonMat, PHOTON_COUNT);
    this.group.add(this.photons);

    const origin = new THREE.Vector3(0, 0, 0);
    for (let i = 0; i < PHOTON_COUNT; i++) {
      const target = this.skillNodes[Math.floor(Math.random() * this.skillNodes.length)].pos.clone();
      const mid = target.clone().multiplyScalar(0.5).add(new THREE.Vector3(
        (Math.random() - 0.5) * 0.4, (Math.random() - 0.5) * 0.4, (Math.random() - 0.5) * 0.4
      ));
      this.photonPaths.push({ target, midControl: mid, speedOffset: Math.random() * 0.1 });
    }

    this.scene.add(this.group);
    this.group.visible = false;
  }

  show() {
    this.visible = true;
    this.group.visible = true;
    this.skillLabels.forEach(l => l.el.style.display = '');
  }

  hide() {
    this.visible = false;
    this.group.visible = false;
    this.skillLabels.forEach(l => l.el.style.display = 'none');
  }

  update(time, mouse) {
    if (!this.visible) return;
    this.time = time;

    // Core rotation
    this.group.rotation.y = time * 0.15;
    this.group.rotation.x = Math.sin(time * 0.1) * 0.04;

    // Neural cluster rotation
    if (this.neuralCluster) {
      this.neuralCluster.rotation.y = -time * 0.2;
      const scale = this.speaking ? (0.85 + Math.sin(time * 20) * 0.15) : 1;
      this.neuralCluster.scale.setScalar(scale);
    }

    // Thread satellites orbit
    this.threadSatellites.forEach(sat => {
      sat.userData.angle += 0.02;
      sat.position.x = Math.cos(sat.userData.angle) * sat.userData.radius;
      sat.position.z = Math.sin(sat.userData.angle) * sat.userData.radius;
      sat.position.y = Math.sin(time * 2) * 0.05;
    });

    // Photon animation
    const dummy = new THREE.Object3D();
    const origin = new THREE.Vector3(0, 0, 0);
    this.photons.count = this.photonPaths.length;

    for (let i = 0; i < this.photonPaths.length; i++) {
      const p = this.photonPaths[i];
      const progress = (time * 0.45 + p.speedOffset) % 1;
      const t = 0.5 - 0.5 * Math.cos(progress * Math.PI);

      this.computeBezier(origin, p.midControl, p.target, t);
      dummy.position.copy(this._outBezier);
      const s = 0.5 + Math.sin(progress * Math.PI) * 0.5;
      dummy.scale.setScalar(s);
      dummy.updateMatrix();
      this.photons.setMatrixAt(i, dummy.matrix);
    }
    this.photons.instanceMatrix.needsUpdate = true;

    // Skill label projection
    const camera = this.scene.parent?.camera || window._jarvisCamera;
    if (camera) {
      this.skillLabels.forEach(({ el, pos }) => {
        this._tempV.copy(pos);
        this._tempV.applyMatrix4(this.group.matrixWorld);
        this._tempV.project(camera);
        const x = (this._tempV.x * 0.5 + 0.5) * window.innerWidth;
        const y = (-this._tempV.y * 0.5 + 0.5) * window.innerHeight;
        el.style.left = `${x}px`;
        el.style.top = `${y}px`;
        el.style.transform = 'translate(-50%, -50%)';
        el.style.display = this._tempV.z < 1 ? '' : 'none';
      });
    }
  }
}

window.NeuralCoreMode = NeuralCoreMode;
